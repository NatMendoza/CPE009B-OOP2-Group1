# test_backend.py
# run it with: python test_backend.py
# it uses a temporary folder, so your real data is not touched

import shutil
import tempfile
from decimal import Decimal
from pathlib import Path

from errors import *
from services import POSBackend
from discounts import Discount
from users import User


def expect_error(error_type, function, *args):
    # passes only if the function raises that kind of error
    try:
        function(*args)
    except error_type:
        return
    except Exception as e:
        raise AssertionError(f"expected {error_type.__name__} but got {type(e).__name__}: {e}")
    raise AssertionError(f"expected {error_type.__name__} but nothing was raised")


# set up: a temp folder with a copy of the items, and a fake clock for the lockout
temp = Path(tempfile.mkdtemp())
shutil.copy(Path(__file__).parent / "data" / "items.csv", temp / "items.csv")
clock = [0.0]
backend = POSBackend(temp, clock=lambda: clock[0])

# abstract classes can't be made directly
expect_error(TypeError, Discount, "x")
expect_error(TypeError, User, "abc", "x")

# login and lockout
assert len(backend.items.all()) == 100
expect_error(AuthenticationError, backend.login, "admin", "wrong")
expect_error(AuthenticationError, backend.login, "admin", "wrong")
expect_error(AccountLockedError, backend.login, "admin", "wrong")       # 3rd wrong try locks it
expect_error(AccountLockedError, backend.login, "admin", "admin123")    # even the right password
clock[0] += 61                                                          # wait out the lock
admin = backend.login("admin", "admin123")
assert admin.can("void_sales")

# search by serial number and by name
assert backend.search_items("SN-1045")[0].serial == "SN-1045"
assert backend.search_items("1045")[0].serial == "SN-1045"
assert backend.search_items("sn1045")[0].serial == "SN-1045"
assert len(backend.search_items("milo")) == 1
assert all(i.category == "Beverages" for i in backend.search_items("", "Beverages"))
expect_error(ItemNotFoundError, backend.get_item, "SN-9999")

# admin adds a product
backend.add_item("SN-2001", "Test Item", "12.50", 10, "Snacks")
assert "SN-2001" in (temp / "items.csv").read_text(encoding="utf-8")
expect_error(DuplicateError, backend.add_item, "SN-2001", "Same serial", 5, 1)
expect_error(ValidationError, backend.add_item, "SN-2002", "Bad price", -5, 1)

# a sale with the senior discount: 2 x 58 + 45 = 161, 20% off = 128.80
backend.start_transaction()
backend.add_to_cart("SN-1001", 2)
backend.add_to_cart("1005", 1)
backend.set_customer_type("senior")
totals = backend.totals()
assert totals["subtotal"] == Decimal("161.00")
assert totals["discount"] == Decimal("32.20")
assert totals["total"] == Decimal("128.80")
assert totals["vat"] == Decimal("13.80")
assert backend.change_for(200) == Decimal("71.20")
expect_error(InsufficientPaymentError, backend.checkout, 100)
expect_error(InsufficientStockError, backend.add_to_cart, "SN-1001", 500)
receipt = backend.checkout(200)
assert "71.20" in receipt and "VAT (12%)" in receipt
assert backend.get_item("SN-1001").stock == 48
transaction_id = receipt.split("Transaction No: ")[1].split("\n")[0]
assert backend.last_receipt_path.exists()

# a promo sale and a normal sale (no "-0.00" on the receipt)
backend.start_transaction()
backend.add_to_cart("SN-1002", 1)
expect_error(InvalidDiscountError, backend.set_customer_type, "promo")
backend.set_customer_type("promo", "weekend sale")
assert backend.totals()["discount"] == Decimal("28.50")
backend.set_customer_type("regular")
assert "-0.00" not in backend.checkout(300)

# if saving the sale fails, the stock goes back to what it was
backend.start_transaction()
backend.add_to_cart("SN-1003", 1)
real_append = backend._log.append
def broken_append(txn):
    raise StorageError("disk full")
backend._log.append = broken_append
expect_error(StorageError, backend.checkout, 500)
backend._log.append = real_append
assert backend.get_item("SN-1003").stock == 50
assert "SN-1003,Jasmine Rice – 1 kg,65.00,50" in (temp / "items.csv").read_text(encoding="utf-8")
assert backend.transaction.status == "open"
backend.cancel_transaction()

# report before the void
summary = backend.sales_summary()
assert summary["transactions"] == 2 and summary["voided"] == 0
assert backend.best_sellers()[0]["serial"] == "SN-1001"

# void the first sale
expect_error(TransactionNotFoundError, backend.void_transaction, "TXN-20000101-0001", "x")
expect_error(ValidationError, backend.void_transaction, transaction_id, "   ")
result = backend.void_transaction(transaction_id, "Customer returned everything")
assert result["restored_items"] == 2
assert backend.get_item("SN-1001").stock == 50
assert backend.get_item("SN-1005").stock == 50
expect_error(VoidError, backend.void_transaction, transaction_id, "again")
summary = backend.sales_summary()
assert summary["transactions"] == 1 and summary["voided"] == 1
assert "voided" in (temp / "transactions.csv").read_text(encoding="utf-8")

# roles and permissions
backend.create_user("cashier1", "secret1", "cashier", "Juan Dela Cruz", "juan@mail.com", "09171234567")
expect_error(DuplicateError, backend.create_user, "CASHIER1", "secret1", "cashier")
expect_error(ValidationError, backend.create_user, "bad", "secret1", "cashier", "", "not-an-email")
backend.logout()
cashier = backend.login("cashier1", "secret1")
assert "Ready to sell" in cashier.greeting()
expect_error(PermissionDeniedError, backend.add_item, "SN-3000", "X", 5, 1)
expect_error(PermissionDeniedError, backend.void_transaction, transaction_id, "x")
expect_error(PermissionDeniedError, backend.sales_summary)
expect_error(PermissionDeniedError, backend.create_user, "x1", "secret1", "cashier")

# a changed password is still there after restarting the program
backend.change_password("secret1", "newsecret")
backend.logout()
assert POSBackend(temp).login("cashier1", "newsecret")
expect_error(AuthenticationError, POSBackend(temp).login, "cashier1", "secret1")

shutil.rmtree(temp)
print("ALL TESTS PASSED")
