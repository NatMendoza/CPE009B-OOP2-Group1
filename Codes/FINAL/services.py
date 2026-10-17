from __future__ import annotations

import time
from pathlib import Path

from discounts import NoDiscount, PWDDiscount, SeniorDiscount
from errors import (AuthenticationError, InvalidDiscountError, StorageError,
                    TransactionStateError, ValidationError)
from items import Item
from receipts import ReceiptStore, build_receipt
from reports import SalesReport
from storage import ItemRepository, PromoRepository, TransactionLog, UserRepository
from transaction import Transaction
from users import ROLE_CLASSES, LoginGuard, User
from validators import normalize_serial, parse_quantity


class POSBackend:
    def __init__(self, data_dir="data", clock=time.monotonic):
        data_dir = Path(data_dir)
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
        """Show these to the admin on startup (bad CSV rows that were skipped)."""
        return self.items.warnings + self.users.warnings + self.promos.warnings

    # ------------------------------------------------------------ session
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
            user._password_hash = old_hash           # undo, the file was not updated
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

    # ------------------------------------------------------------ catalog
    def search_items(self, query="", category=None) -> list[Item]:
        self._need_user()
        return self.items.search(query, category)

    def get_item(self, serial) -> Item:
        self._need_user()
        return self.items.get(serial)

    def categories(self) -> list[str]:
        return ["All"] + self.items.categories()

    # ------------------------------------------------------------ selling
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

    def add_to_cart(self, serial, qty=1):
        txn = self._need_txn()
        txn.add_item(self.items.get(serial), qty)

    def set_cart_quantity(self, serial, qty):
        txn = self._need_txn()
        txn.set_quantity(self.items.get(serial), qty)

    def remove_from_cart(self, serial):
        self._need_txn().remove_item(normalize_serial(serial))

    def clear_cart(self):
        self._need_txn().clear()

    def cancel_transaction(self):
        if self._txn is not None and self._txn.status == "open":
            self._txn.cancel()
        self._txn = None

    def set_customer_type(self, kind, promo_name=None):
        txn = self._need_txn()
        kind = str(kind).strip().lower()
        if kind == "regular":
            txn.set_discount(NoDiscount(), kind)
        elif kind == "senior":
            txn.set_discount(SeniorDiscount(), kind)
        elif kind == "pwd":
            txn.set_discount(PWDDiscount(), kind)
        elif kind == "promo":
            if not promo_name:
                raise InvalidDiscountError("Choose which promo to apply.")
            txn.set_discount(self.promos.get(promo_name), kind)
        else:
            raise InvalidDiscountError(f"Unknown customer type: {kind!r}")

    def totals(self) -> dict:
        """Everything the right-hand panel of the GUI needs, as Decimals."""
        t = self._need_txn()
        return {"subtotal": t.subtotal, "discount": t.discount_amount,
                "vat": t.vat, "total": t.total}

    def checkout(self, payment) -> str:
        txn = self._need_txn()
        txn.pay(payment)                       # validates cart + payment, may raise
        sold = []
        try:
            for line in txn.lines:             # deduct stock in memory
                item = self.items.get(line.serial)
                item.reduce_stock(line.quantity)
                sold.append((item, line.quantity))
            self.items.save()                  # then persist; any failure -> roll back
            self._log.append(txn)
        except Exception:
            for item, qty in sold:
                item.add_stock(qty)
            txn.revert_payment()
            raise
        receipt = build_receipt(txn)
        try:                                   # the sale is already recorded, so a
            self.last_receipt_path = self._receipts.save(txn.transaction_id, receipt)
        except StorageError:                   # receipt-file problem must not undo it
            self.last_receipt_path = None
        self._txn = None
        return receipt

    # ------------------------------------------------------------ manager/admin
    def restock(self, serial, qty):
        self._need_user().require("restock")
        item = self.items.get(serial)
        item.add_stock(parse_quantity(qty))
        self.items.save()

    def add_item(self, serial, name, price, stock, category="Other", image=""):
        self._need_user().require("manage_items")
        self.items.add(Item(serial, name, price, stock, category, image))

    def update_price(self, serial, new_price):
        self._need_user().require("manage_items")
        self.items.set_price(serial, new_price)

    def delete_item(self, serial):
        self._need_user().require("manage_items")
        self.items.remove(serial)

    def create_user(self, username, password, role, full_name=""):
        self._need_user().require("manage_users")
        cls = ROLE_CLASSES.get(str(role).strip().lower())
        if cls is None:
            raise ValidationError(f"Unknown role {role!r}. Use cashier, manager or admin.")
        self.users.add(cls(username, User.hash_password(password), full_name))

    def sales_summary(self, day=None) -> dict:
        self._need_user().require("view_reports")
        return self._reports.summary(day)

    def best_sellers(self, limit=5, day=None) -> list[dict]:
        self._need_user().require("view_reports")
        return self._reports.best_sellers(limit, day)

