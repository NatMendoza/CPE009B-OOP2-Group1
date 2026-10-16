import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from config import MAX_QTY
from errors import InvalidAmountError, InvalidQuantityError, InvalidSerialError

CENT = Decimal("0.01")
SERIAL_PATTERN = re.compile(r"^SN-\d{3,6}$")


def money(value) -> Decimal:
    """Convert anything money-like to a Decimal rounded to centavos.

    Never use float for money: 0.1 + 0.2 != 0.3 in float.
    """
    if value is None or isinstance(value, bool):
        raise InvalidAmountError(f"Invalid amount: {value!r}")
    try:
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
    if qty <= 0:
        raise InvalidQuantityError("Quantity must be at least 1.")
    if qty > MAX_QTY:
        raise InvalidQuantityError(f"Quantity cannot be more than {MAX_QTY}.")
    return qty


def normalize_serial(value) -> str:
    """'sn-2045', ' SN-2045 ' and '2045' all become 'SN-2045'."""
    s = str(value).strip().upper()
    if s.isdigit():
        s = f"SN-{s}"
    if not SERIAL_PATTERN.match(s):
        raise InvalidSerialError(f"Invalid serial number {value!r}. Use the format SN-1234.")
    return s

