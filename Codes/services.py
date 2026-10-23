# POSBackend: the ONLY class the GUI needs to talk to.
from __future__ import annotations

import time
from decimal import Decimal
from pathlib import Path

from config import DATA_DIR
from discounts import FIXED_DISCOUNTS, NoDiscount, create_fixed_discount
from errors import (AuthenticationError, InsufficientStockError, InvalidDiscountError,
                    ItemNotFoundError, StorageError, TransactionStateError, ValidationError)
from items import Item
from receipts import ReceiptStore, build_receipt
from reports import SalesReport
from storage import ItemRepository, PromoRepository, TransactionLog, UserRepository
from transaction import Transaction
from users import ROLE_CLASSES, LoginGuard, User
from validators import money, normalize_serial, parse_quantity


class POSBackend:
    # customer types the gui can show
    CUSTOMER_TYPES = ["regular", *FIXED_DISCOUNTS.keys(), "promo"]

    def __init__(self, data_dir=None, clock=time.monotonic):
        data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.items = ItemRepository(data_dir / "items.csv")
        self.users = UserRepository(data_dir / "users.csv")
        self.promos = PromoRepository(data_dir / "promos.csv")
        self._log = TransactionLog(data_dir)
        self._receipts = ReceiptStore(data_dir / "receipts")
        self._reports = SalesReport(self._log)
        self._guard = LoginGuard(clock=clock)
        self._user: User | None = None
        self._txn: Transaction | None = None
        self.last_receipt_path: Path | None = None

    @property
    def load_warnings(self) -> list[str]:
        # Show these to the admin on startup (bad CSV rows that were skipped).
        return self.items.warnings + self.users.warnings + self.promos.warnings

    # session
    # checks the lock first, then the username and password
    def login(self, username, password) -> User:
        self._guard.check(username)                  # raises AccountLockedError if locked
        user = self.users.get(username)
        # one generic message so nobody can guess which usernames exist
        if user is None or not user.verify_password(password):
            self._guard.record_failure(username)
            self._guard.check(username)              # raises if THIS was the last allowed try
            raise AuthenticationError("Invalid username or password.")
        self._guard.reset(username)
        self._user = user
        self._txn = None
        return user

    def logout(self):
        self._user = None
        self._txn = None

    @property
    def current_user(self) -> User | None:
        return self._user

    def change_password(self, old_password, new_password):
        user = self._need_user()
        old_hash = user.password_hash
        user.change_password(old_password, new_password)
        try:
            self.users.save()
        except StorageError:
            user.restore_hash(old_hash)              # undo, the file was not updated
            raise

    def _need_user(self) -> User:
        if self._user is None:
            raise AuthenticationError("Please log in first.")
        return self._user

    def _need_txn(self) -> Transaction:
        self._need_user()
        if self._txn is None:
            raise TransactionStateError("No transaction in progress. Start a new transaction first.")
        return self._txn

    # catalog
    def search_items(self, query="", category=None) -> list[Item]:
        self._need_user()
        return self.items.search(query, category)

    def get_item(self, serial) -> Item:
        self._need_user()
        return self.items.get(serial)

    def categories(self) -> list[str]:
        return ["All"] + self.items.categories()

    def promo_names(self) -> list[str]:
        self._need_user()
        return self.promos.names()

    # selling
    # starts a new empty sale for the logged in user
    def start_transaction(self) -> str:
        user = self._need_user()
        user.require("sell")
        if self._txn is not None and self._txn.status == "open" and self._txn.lines:
            raise TransactionStateError("Finish or cancel the current transaction first.")
        self._txn = Transaction(self._log.next_transaction_id(), user.username)
        return self._txn.transaction_id

    @property
    def transaction(self) -> Transaction | None:
        return self._txn

    # adds the item to the cart and checks the stock
    def add_to_cart(self, serial, qty=1):
        txn = self._need_txn()
        txn.add_item(self.items.get(serial), qty)

    def set_cart_quantity(self, serial, qty):
        txn = self._need_txn()
        txn.set_quantity(self.items.get(serial), qty)

    def remove_from_cart(self, serial):
        # Void one line of the open cart.
        self._need_txn().remove_item(normalize_serial(serial))

    def clear_cart(self):
        self._need_txn().clear()

    def cart_lines(self) -> list[dict]:
        t = self._need_txn()
        return [{"serial": l.serial, "name": l.name, "unit_price": l.unit_price,
                 "quantity": l.quantity, "line_total": l.line_total} for l in t.lines]

    def cancel_transaction(self):
        if self._txn is not None and self._txn.status == "open":
            self._txn.cancel()
        self._txn = None

    # picks the discount: regular, senior, pwd, solo parent or a promo
    def set_customer_type(self, kind, promo_name=None):
        txn = self._need_txn()
        kind = str(kind).strip().lower().replace(" ", "_").replace("-", "_")
        if kind == "regular":
            txn.set_discount(NoDiscount(), kind)
        elif kind in FIXED_DISCOUNTS:
            txn.set_discount(create_fixed_discount(kind), kind)
        elif kind == "promo":
            if not promo_name:
                raise InvalidDiscountError("Choose which promo to apply.")
            txn.set_discount(self.promos.get(promo_name), kind)
        else:
            raise InvalidDiscountError(f"Unknown customer type: {kind!r}")

    def totals(self) -> dict:
        # Everything the right-hand panel of the GUI needs, as Decimals.
        t = self._need_txn()
        return {"subtotal": t.subtotal, "discount": t.discount_amount, "vat": t.vat,
                "total": t.total, "item_count": t.item_count,
                "customer_type": t.customer_type, "discount_name": t.discount_name}

    def change_for(self, payment) -> Decimal:
        # Live 'change' preview while the cashier types the payment.
        return self._need_txn().change_for(payment)

    # pays, takes the stock out, saves everything and gives back the receipt text
    def checkout(self, payment) -> str:
        txn = self._need_txn()
        txn.pay(payment)                       # validates cart and payment, may raise
        sold = []
        try:
            for line in txn.lines:             # deduct stock in memory
                item = self.items.get(line.serial)
                item.reduce_stock(line.quantity)
                sold.append((item, line.quantity))
            self.items.save()                  # then persist; any failure to roll back
            self._log.append(txn)
        except Exception:
            self._undo_stock(sold, "reduce")
            txn.revert_payment()
            raise
        receipt = build_receipt(txn)
        try:                                   # the sale is already recorded, so a
            self.last_receipt_path = self._receipts.save(txn.transaction_id, receipt)
        except StorageError:                   # receipt-file problem must not undo it
            self.last_receipt_path = None
        self._txn = None
        return receipt

    def _undo_stock(self, changed, how):
        # Put memory AND the items file back after a failed multi-step change.
        for item, qty in changed:
            try:
                item.add_stock(qty) if how == "reduce" else item.reduce_stock(qty)
            except (InsufficientStockError, ValidationError):
                pass
        try:
            self.items.save()
        except StorageError:
            pass

    def get_receipt(self, transaction_id) -> str:
        # Reprint a saved receipt.
        self._need_user()
        return self._receipts.read(transaction_id)

    # manager/admin: products
    # adds stock to an existing item, manager and admin only
    def restock(self, serial, qty):
        self._need_user().require("restock")
        item = self.items.get(serial)
        qty = parse_quantity(qty)
        item.add_stock(qty)
        try:
            self.items.save()
        except StorageError:
            item.reduce_stock(qty)
            raise

    # adds a new product, manager and admin only
    def add_item(self, serial, name, price, stock, category="Other", image=""):
        self._need_user().require("manage_items")
        self.items.add(Item(serial, name, price, stock, category, image))   # saves too

    def update_price(self, serial, new_price):
        self._need_user().require("manage_items")
        self.items.set_price(serial, new_price)

    def delete_item(self, serial):
        self._need_user().require("manage_items")
        self.items.remove(serial)

    # manager/admin: promos
    def add_promo(self, name, percent):
        self._need_user().require("manage_items")
        self.promos.add(name, percent)

    def remove_promo(self, name):
        self._need_user().require("manage_items")
        self.promos.remove(name)

    # admin: void
    def recent_transactions(self, limit=20) -> list[dict]:
        self._need_user().require("void_sales")
        return self._log.recent(parse_quantity(limit))

    def transaction_details(self, transaction_id) -> dict:
        self._need_user().require("view_reports")
        return self._log.get_transaction(transaction_id)

    def void_transaction(self, transaction_id, reason) -> dict:
        # Cancel a PAID sale: stock goes back, the record stays flagged 'voided'.
        user = self._need_user()
        user.require("void_sales")
        reason = str(reason or "").strip()
        if not reason:
            raise ValidationError("Please give a reason for the void.")
        lines = self._log.get_lines(transaction_id)    # raises if missing / already voided
        restored, skipped = [], []
        try:
            for serial, qty in lines:
                try:
                    item = self.items.get(serial)
                except ItemNotFoundError:              # product was deleted since the sale
                    skipped.append(serial)
                    continue
                item.add_stock(qty)
                restored.append((item, qty))
            self.items.save()
            self._log.mark_voided(transaction_id, user.username, reason)
        except Exception:
            self._undo_stock(restored, "add")
            raise
        return {"transaction_id": str(transaction_id).strip().upper(),
                "restored_items": len(restored), "skipped_serials": skipped}

    # admin: users
    # only the admin can create accounts
    def create_user(self, username, password, role, full_name="", email="", contact=""):
        self._need_user().require("manage_users")
        cls = ROLE_CLASSES.get(str(role).strip().lower())
        if cls is None:
            raise ValidationError(f"Unknown role {role!r}. Use cashier, manager or admin.")
        self.users.add(cls(username, User.hash_password(password), full_name, email, contact))

    def list_users(self) -> list[dict]:
        self._need_user().require("manage_users")
        return [{"username": u.username, "role": u.ROLE, "full_name": u.full_name,
                 "email": u.email, "contact": u.contact} for u in self.users.all()]

    def reset_password(self, username, new_password):
        # Admin sets a new password (e.g. for a locked-out cashier).
        self._need_user().require("manage_users")
        user = self.users.get(username)
        if user is None:
            raise ValidationError(f"No user named {username!r}.")
        old_hash = user.password_hash
        user.reset_password(new_password)
        try:
            self.users.save()
        except StorageError:
            user.restore_hash(old_hash)
            raise
        self._guard.reset(username)

    # reports
    # totals for one day, manager and admin only
    def sales_summary(self, day=None) -> dict:
        self._need_user().require("view_reports")
        return self._reports.summary(day)

    def best_sellers(self, limit=5, day=None) -> list[dict]:
        self._need_user().require("view_reports")
        return self._reports.best_sellers(limit, day)