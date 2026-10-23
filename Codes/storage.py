# storage.py
# reads and writes the csv files for items, users, promos and sales

import csv
from datetime import date, datetime
from pathlib import Path

from config import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME
from discounts import PromoDiscount
from errors import (DuplicateError, InvalidDiscountError, ItemNotFoundError, POSError,
                    StorageError, TransactionNotFoundError, VoidError)
from items import Item
from users import ROLE_CLASSES, Admin, User
from validators import normalize_serial


# csv helpers
def read_csv(path):
    # gives back every row as a dictionary
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except (OSError, csv.Error, UnicodeDecodeError) as e:
        raise StorageError(f"Could not read {Path(path).name}: {e}") from e


def write_csv(path, fields, rows, mode="w"):
    # w replaces the file, a adds rows to the end
    path = Path(path)
    is_new = mode == "w" or not path.exists()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            if is_new:
                writer.writeheader()
            writer.writerows(rows)
    except OSError as e:
        raise StorageError(f"Could not write {path.name} (is it open in another program?): {e}") from e


def save_or_undo(save, undo):
    # tries to save, and if it fails it undoes the change in memory
    try:
        save()
    except StorageError:
        undo()
        raise


# items.csv
class ItemRepository:
    FIELDS = ["serial", "name", "price", "stock", "category", "image"]

    def __init__(self, path):
        self._path = Path(path)
        self._items = {}        # items saved by serial number
        self.warnings = []      # messages about skipped rows
        if self._path.exists():
            self._load()
        else:
            self.warnings.append(f"{self._path.name} was not found. Starting with no items.")

    def _load(self):
        for number, row in enumerate(read_csv(self._path), start=2):
            try:
                item = Item(row.get("serial"), row.get("name"), row.get("price"),
                            row.get("stock"), row.get("category"), row.get("image"))
            except POSError as e:
                self.warnings.append(f"{self._path.name} row {number} skipped: {e}")
                continue
            if item.serial in self._items:
                self.warnings.append(f"{self._path.name} row {number} skipped: duplicate {item.serial}")
                continue
            self._items[item.serial] = item

    def save(self):
        write_csv(self._path, self.FIELDS, [item.to_row() for item in self.all()])

    def all(self):
        return sorted(self._items.values(), key=lambda item: item.serial)

    def get(self, serial):
        key = normalize_serial(serial)
        if key not in self._items:
            raise ItemNotFoundError(f"No item with serial number {key}.")
        return self._items[key]

    def search(self, query="", category=None):
        # matches the serial number or part of the name
        text = str(query or "").strip().casefold()
        text_no_dash = text.replace("-", "").replace(" ", "")
        results = []
        for item in self.all():
            if category and category != "All" and item.category.casefold() != str(category).casefold():
                continue
            in_name = text in item.name.casefold()
            in_serial = text_no_dash in item.serial.casefold().replace("-", "")
            if text and not (in_name or in_serial):
                continue
            results.append(item)
        return results

    def categories(self):
        return sorted({item.category for item in self._items.values()})

    def add(self, item):
        if item.serial in self._items:
            raise DuplicateError(f"Serial number {item.serial} already exists.")
        self._items[item.serial] = item
        save_or_undo(self.save, lambda: self._items.pop(item.serial))

    def remove(self, serial):
        item = self.get(serial)
        del self._items[item.serial]
        save_or_undo(self.save, lambda: self._items.__setitem__(item.serial, item))

    def set_price(self, serial, new_price):
        item = self.get(serial)
        old_price = item.price
        item.price = new_price      # gives an error first if the price is bad
        save_or_undo(self.save, lambda: setattr(item, "price", old_price))


# users.csv
class UserRepository:
    FIELDS = ["username", "password_hash", "role", "full_name", "email", "contact"]

    def __init__(self, path):
        self._path = Path(path)
        self._users = {}        # users saved by lowercase username
        self.warnings = []
        if self._path.exists():
            self._load()
        if not self._users:
            self._make_default_admin()

    def _load(self):
        for number, row in enumerate(read_csv(self._path), start=2):
            user_class = ROLE_CLASSES.get((row.get("role") or "").strip().lower())
            if user_class is None:
                self.warnings.append(f"{self._path.name} row {number} skipped: unknown role")
                continue
            try:
                user = user_class(row.get("username"), row.get("password_hash"),
                                  row.get("full_name"), row.get("email"), row.get("contact"))
            except POSError as e:
                self.warnings.append(f"{self._path.name} row {number} skipped: {e}")
                continue
            if user.username.lower() in self._users:
                self.warnings.append(f"{self._path.name} row {number} skipped: duplicate username")
                continue
            self._users[user.username.lower()] = user

    def _make_default_admin(self):
        admin = Admin(DEFAULT_ADMIN_USERNAME, User.hash_password(DEFAULT_ADMIN_PASSWORD),
                      "Administrator")
        self._users[admin.username.lower()] = admin
        self.warnings.append(
            f"A default admin was created. Username: {DEFAULT_ADMIN_USERNAME}, "
            f"password: {DEFAULT_ADMIN_PASSWORD}. Please change the password after logging in.")
        try:
            self.save()
        except StorageError as e:
            self.warnings.append(str(e))

    def save(self):
        write_csv(self._path, self.FIELDS, [user.to_row() for user in self.all()])

    def all(self):
        return sorted(self._users.values(), key=lambda user: user.username.lower())

    def get(self, username):
        # gives None if there is no such user
        return self._users.get(str(username).strip().lower())

    def add(self, user):
        key = user.username.lower()
        if key in self._users:
            raise DuplicateError(f"Username {user.username!r} is already taken.")
        self._users[key] = user
        save_or_undo(self.save, lambda: self._users.pop(key))


# promos.csv
class PromoRepository:
    FIELDS = ["name", "percent"]

    def __init__(self, path):
        self._path = Path(path)
        self._promos = {}       # promos saved by lowercase name
        self.warnings = []
        if self._path.exists():
            self._load()
        else:
            # two sample promos for a new store
            for name, percent in [("Weekend Sale", "10"), ("Holiday Promo", "15")]:
                self._promos[name.lower()] = PromoDiscount(name, percent)
            try:
                self.save()
            except StorageError as e:
                self.warnings.append(str(e))

    def _load(self):
        for number, row in enumerate(read_csv(self._path), start=2):
            try:
                promo = PromoDiscount(row.get("name"), row.get("percent"))
            except POSError as e:
                self.warnings.append(f"{self._path.name} row {number} skipped: {e}")
                continue
            self._promos[promo.base_name.lower()] = promo

    def save(self):
        rows = [{"name": p.base_name, "percent": f"{p.percent.normalize():f}"}
                for p in self._promos.values()]
        write_csv(self._path, self.FIELDS, rows)

    def names(self):
        return sorted(promo.base_name for promo in self._promos.values())

    def get(self, name):
        promo = self._promos.get(str(name).strip().lower())
        if promo is None:
            raise InvalidDiscountError(f"Unknown promo: {name!r}.")
        return promo

    def add(self, name, percent):
        promo = PromoDiscount(name, percent)        # checks the name and percent
        key = promo.base_name.lower()
        if key in self._promos:
            raise DuplicateError(f"Promo {promo.base_name!r} already exists.")
        self._promos[key] = promo
        save_or_undo(self.save, lambda: self._promos.pop(key))

    def remove(self, name):
        promo = self.get(name)
        key = promo.base_name.lower()
        del self._promos[key]
        save_or_undo(self.save, lambda: self._promos.__setitem__(key, promo))


# transactions.csv and transaction_items.csv
# one row for each sale and one row for each item in it
class TransactionLog:
    HEADER_FIELDS = ["transaction_id", "datetime", "cashier", "customer_type", "discount_name",
                     "subtotal", "discount", "vat", "total", "payment", "change",
                     "status", "voided_by", "voided_at", "void_reason"]
    DETAIL_FIELDS = ["transaction_id", "serial", "name", "unit_price", "quantity", "line_total"]

    def __init__(self, data_dir):
        self._headers_path = Path(data_dir) / "transactions.csv"
        self._details_path = Path(data_dir) / "transaction_items.csv"

    def read_headers(self):
        if not self._headers_path.exists():
            return []
        rows = read_csv(self._headers_path)
        for row in rows:
            row["status"] = (row.get("status") or "paid").strip().lower()
        return rows

    def read_details(self):
        if not self._details_path.exists():
            return []
        return read_csv(self._details_path)

    def next_transaction_id(self):
        # the id has the date and a 4 digit number that goes up with each sale of the day
        prefix = f"TXN-{date.today():%Y%m%d}-"
        numbers = [int(r["transaction_id"][len(prefix):]) for r in self.read_headers()
                   if r["transaction_id"].startswith(prefix)
                   and r["transaction_id"][len(prefix):].isdigit()]
        return f"{prefix}{max(numbers, default=0) + 1:04d}"

    def append(self, txn):
        header = {
            "transaction_id": txn.transaction_id,
            "datetime": txn.completed_at.isoformat(timespec="seconds"),
            "cashier": txn.cashier,
            "customer_type": txn.customer_type,
            "discount_name": txn.discount_name,
            "subtotal": f"{txn.subtotal:.2f}",
            "discount": f"{txn.discount_amount:.2f}",
            "vat": f"{txn.vat:.2f}",
            "total": f"{txn.total:.2f}",
            "payment": f"{txn.payment:.2f}",
            "change": f"{txn.change:.2f}",
            "status": "paid",
        }
        details = [{"transaction_id": txn.transaction_id, "serial": l.serial, "name": l.name,
                    "unit_price": f"{l.unit_price:.2f}", "quantity": l.quantity,
                    "line_total": f"{l.line_total:.2f}"} for l in txn.lines]

        # items are saved first, then the sale row, a sale only counts once its row is saved
        write_csv(self._details_path, self.DETAIL_FIELDS, details, mode="a")

        def undo():
            # take the items back out so a retry doesn't save them twice
            kept = [d for d in self.read_details() if d["transaction_id"] != txn.transaction_id]
            write_csv(self._details_path, self.DETAIL_FIELDS, kept)

        save_or_undo(lambda: write_csv(self._headers_path, self.HEADER_FIELDS, [header], mode="a"),
                     undo)

    # used by the void screen
    def recent(self, limit=20):
        return list(reversed(self.read_headers()))[:limit]

    def get_transaction(self, transaction_id):
        tid = str(transaction_id).strip().upper()
        for header in self.read_headers():
            if header["transaction_id"].upper() == tid:
                lines = [d for d in self.read_details()
                         if d["transaction_id"] == header["transaction_id"]]
                return {**header, "lines": lines}
        raise TransactionNotFoundError(f"Transaction {tid} was not found.")

    def get_lines(self, transaction_id):
        # gives the serial and quantity of each item in a sale that can still be voided
        sale = self.get_transaction(transaction_id)
        if sale["status"] == "voided":
            raise VoidError(f"Transaction {sale['transaction_id']} is already voided.")
        lines = []
        for line in sale["lines"]:
            if not line["quantity"].isdigit():
                raise StorageError(f"transaction_items.csv has a bad quantity: {line['quantity']!r}")
            lines.append((line["serial"], int(line["quantity"])))
        return lines

    def mark_voided(self, transaction_id, by, reason):
        # the sale stays in the file as a record and is marked as voided
        tid = str(transaction_id).strip().upper()
        rows = self.read_headers()
        row = next((r for r in rows if r["transaction_id"].upper() == tid), None)
        if row is None:
            raise TransactionNotFoundError(f"Transaction {tid} was not found.")
        if row["status"] == "voided":
            raise VoidError(f"Transaction {row['transaction_id']} is already voided.")
        row.update(status="voided", voided_by=by, void_reason=reason,
                   voided_at=datetime.now().isoformat(timespec="seconds"))
        write_csv(self._headers_path, self.HEADER_FIELDS, rows)