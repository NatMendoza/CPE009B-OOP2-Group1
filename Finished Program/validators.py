import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from config import MAX_QTY
from errors import (InvalidAmountError, InvalidQuantityError, InvalidSerialError,
                    ValidationError)

# smallest peso amount, one centavo
CENT = Decimal("0.01")
# serial must look like SN- then 3 to 6 digits
SERIAL_PATTERN = re.compile(r"^SN-\d{3,6}$")
# letters, numbers, dot, dash or underscore only
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
# simple email check, needs an @ and a dot
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# philippine mobile number, 09 then 9 digits or +639
CONTACT_PATTERN = re.compile(r"^(09\d{9}|\+639\d{9})$")


def money(value) -> Decimal:
    # Convert anything money-like to a Decimal rounded to centavos.
    # Never use float for money: 0.1 and 0.2 != 0.3 in float.
    # reject empty values and True or False
    if value is None or isinstance(value, bool):
        raise InvalidAmountError(f"Invalid amount: {value!r}")
    try:
        # turn the text into a Decimal, commas are removed first
        d = Decimal(str(value).strip().replace(",", ""))
        if not d.is_finite():
            raise InvalidOperation
        return d.quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise InvalidAmountError(f"Invalid amount: {value!r}") from None


def parse_quantity(value) -> int:
    if isinstance(value, bool):
        raise InvalidQuantityError("Quantity must be a whole number.")
    try:
        qty = int(str(value).strip())  # "2.5" and "abc" both fail here
    except ValueError:
        raise InvalidQuantityError(f"Quantity must be a whole number, got {value!r}.") from None
    # quantity has to be at least 1
    if qty <= 0:
        raise InvalidQuantityError("Quantity must be at least 1.")
    # and not more than the limit
    if qty > MAX_QTY:
        raise InvalidQuantityError(f"Quantity cannot be more than {MAX_QTY}.")
    return qty


def normalize_serial(value) -> str:
    # 'sn-2045', 'SN2045', ' SN-2045 ' and '2045' all become 'SN-2045'.
    # clean up the text first
    s = str(value).strip().upper()
    if s.isascii() and s.isdigit():
        s = f"SN-{s}"
    elif re.fullmatch(r"SN\d+", s):
        s = f"SN-{s[2:]}"
    # after cleaning it still has to match the pattern
    if not SERIAL_PATTERN.match(s):
        raise InvalidSerialError(f"Invalid serial number {value!r}. Use the format SN-1234.")
    return s


def validate_username(value) -> str:
    s = str(value or "").strip()
    if not USERNAME_PATTERN.match(s):
        raise ValidationError(
            "Username must be 3-30 characters: letters, numbers, dot, dash or underscore.")
    return s


def validate_email(value) -> str:
    # Optional field: empty is fine, but if given it must look like an email.
    s = str(value or "").strip()
    if s and not EMAIL_PATTERN.match(s):
        raise ValidationError(f"Invalid email address: {s!r}.")
    return s


def validate_contact(value) -> str:
    # Optional field. Accepts 09XXXXXXXXX or +639XXXXXXXXX.
    s = str(value or "").strip().replace(" ", "").replace("-", "")
    if s and not CONTACT_PATTERN.match(s):
        raise ValidationError("Contact number must look like 09XXXXXXXXX.")
    return s