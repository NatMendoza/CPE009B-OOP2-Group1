import csv
from datetime import date
from pathlib import Path

from discounts import PromoDiscount
from errors import InvalidDiscountError, ItemNotFoundError, POSError, StorageError, ValidationError
from items import Item
from sample_data import SAMPLE_PRODUCTS, SAMPLE_STOCK
from users import ROLE_CLASSES
from validators import normalize_serial

ITEM_COLUMNS = ["serial", "name", "price", "stock", "category", "image"]
USER_COLUMNS = ["username", "password_hash", "role", "full_name"]
PROMO_COLUMNS = ["name", "percent"]
HEADER_COLUMNS = ["transaction_id", "datetime", "cashier", "customer_type", "discount_name",
                  "subtotal", "discount", "vat", "total", "payment", "change"]
DETAIL_COLUMNS = ["transaction_id", "serial", "name", "unit_price", "quantity", "line_total"]


# reads a csv file into a list of dicts
def read_rows(path):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except OSError as e:
        raise StorageError(f"Could not read {Path(path).name}: {e}") from e


# writes a csv file, append=True adds rows to the end instead of replacing the file
def write_csv(path, columns, rows, append=False):
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not path.exists() or path.stat().st_size == 0
        with open(path, "a" if append else "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file or not append:
                writer.writerow(columns)
            writer.writerows(rows)
    except OSError as e:
        raise StorageError(f"Could not write {path.name}: {e}") from e


class ItemRepository:
    def __init__(self, path):
        self._path = Path(path)
        self._items = {}
        self.warnings = []

        # first time running, make the file from the sample products
        if not self._path.exists():
            rows = []
            for number, (name, price, category) in enumerate(SAMPLE_PRODUCTS, start=1001):
                rows.append([f"SN-{number}", name, price, SAMPLE_STOCK, category, ""])
            write_csv(self._path, ITEM_COLUMNS, rows)

        self._load()

    def _load(self):
        for line_no, row in enumerate(read_rows(self._path), start=2):
            try:
                item = Item(row["serial"], row["name"], row["price"], row["stock"],
                            row.get("category") or "Other", row.get("image") or "")
            except (POSError, KeyError) as e:
                self.warnings.append(f"items.csv line {line_no} skipped: {e}")
                continue
            if item.serial in self._items:
                self.warnings.append(f"items.csv line {line_no} skipped: {item.serial} is repeated.")
                continue
            self._items[item.serial] = item

    # matches the serial number or the name, and the collection if one is chosen
    def search(self, query="", category=None):
        query = str(query).strip().lower()
        found = []
        for item in self._items.values():
            if category and category != "All" and item.category.lower() != str(category).lower():
                continue
            if query and query not in item.serial.lower() and query not in item.name.lower():
                continue
            found.append(item)
        return found

    def get(self, serial):
        item = self._items.get(normalize_serial(serial))
        if item is None:
            raise ItemNotFoundError(f"No item with serial number {serial!r}.")
        return item

    def categories(self):
        names = []
        for item in self._items.values():
            if item.category not in names:
                names.append(item.category)
        return names

    def add(self, item):
        if item.serial in self._items:
            raise ValidationError(f"{item.serial} already exists.")
        self._items[item.serial] = item
        try:
            self.save()
        except StorageError:
            del self._items[item.serial]
            raise

    def set_price(self, serial, new_price):
        item = self.get(serial)
        old_price = item.price
        item.price = new_price
        try:
            self.save()
        except StorageError:
            item.price = old_price
            raise

    def remove(self, serial):
        item = self.get(serial)
        del self._items[item.serial]
        try:
            self.save()
        except StorageError:
            self._items[item.serial] = item
            raise

    def save(self):
        rows = [[i.serial, i.name, i.price, i.stock, i.category, i.image] for i in self._items.values()]
        write_csv(self._path, ITEM_COLUMNS, rows)


class UserRepository:
    def __init__(self, path):
        self._path = Path(path)
        self._users = {}
        self.warnings = []
        if self._path.exists():
            self._load()

    def _load(self):
        for line_no, row in enumerate(read_rows(self._path), start=2):
            user_class = ROLE_CLASSES.get((row.get("role") or "").strip().lower())
            if user_class is None:
                self.warnings.append(f"users.csv line {line_no} skipped: unknown role.")
                continue
            try:
                user = user_class(row["username"], row["password_hash"], row.get("full_name") or "")
            except (POSError, KeyError) as e:
                self.warnings.append(f"users.csv line {line_no} skipped: {e}")
                continue
            self._users[user.username.lower()] = user

    def get(self, username):
        return self._users.get(str(username).strip().lower())

    def add(self, user):
        key = user.username.lower()
        if key in self._users:
            raise ValidationError("That username is already taken.")
        self._users[key] = user
        try:
            self.save()
        except StorageError:
            del self._users[key]
            raise

    def save(self):
        rows = [[u.username, u.password_hash, u.ROLE, u.full_name] for u in self._users.values()]
        write_csv(self._path, USER_COLUMNS, rows)


class PromoRepository:
    def __init__(self, path):
        self._promos = {}
        self.warnings = []
        path = Path(path)
        if not path.exists():
            return
        for line_no, row in enumerate(read_rows(path), start=2):
            try:
                promo = PromoDiscount(row["name"], row["percent"])
            except (POSError, KeyError) as e:
                self.warnings.append(f"promos.csv line {line_no} skipped: {e}")
                continue
            self._promos[row["name"].strip().lower()] = (row["name"].strip(), promo)

    def names(self):
        return [name for name, promo in self._promos.values()]

    def get(self, name):
        found = self._promos.get(str(name).strip().lower())
        if found is None:
            raise InvalidDiscountError(f"Unknown promo: {name!r}.")
        return found[1]


class TransactionLog:
    def __init__(self, data_dir):
        folder = Path(data_dir)
        self._headers_path = folder / "transactions.csv"
        self._details_path = folder / "transaction_items.csv"

    # TXN-20261017-0001, the number goes up for every sale of the day
    def next_transaction_id(self):
        prefix = f"TXN-{date.today():%Y%m%d}-"
        last = 0
        for row in self.read_headers():
            if row["transaction_id"].startswith(prefix):
                try:
                    last = max(last, int(row["transaction_id"][len(prefix):]))
                except ValueError:
                    pass
        return f"{prefix}{last + 1:04d}"

    def append(self, txn):
        header_row = [txn.transaction_id, txn.completed_at.strftime("%Y-%m-%d %H:%M:%S"),
                      txn.cashier, txn.customer_type, txn.discount_name, txn.subtotal,
                      txn.discount_amount, txn.vat, txn.total, txn.payment, txn.change]
        detail_rows = [[txn.transaction_id, l.serial, l.name, l.unit_price, l.quantity, l.line_total]
                       for l in txn.lines]
        write_csv(self._headers_path, HEADER_COLUMNS, [header_row], append=True)
        write_csv(self._details_path, DETAIL_COLUMNS, detail_rows, append=True)

    def read_headers(self):
        return read_rows(self._headers_path) if self._headers_path.exists() else []

    def read_details(self):
        return read_rows(self._details_path) if self._details_path.exists() else []
