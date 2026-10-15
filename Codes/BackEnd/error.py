
class POSError(Exception):
    """Base class for all expected POS errors."""


class ValidationError(POSError):
    """A field (name, price, stock, username...) has a bad value."""


class InvalidSerialError(POSError):
    """Serial number is not in the SN-#### format."""


class ItemNotFoundError(POSError):
    """No item matches the serial number."""


class InvalidQuantityError(POSError):
    """Quantity is not a whole number between 1 and the maximum."""


class InvalidAmountError(POSError):
    """A peso amount could not be understood."""


class InsufficientStockError(POSError):
    """Not enough stock to sell the requested quantity."""


class InsufficientPaymentError(POSError):
    """Payment is less than the total."""


class EmptyCartError(POSError):
    """Tried to check out with nothing in the cart."""


class InvalidDiscountError(POSError):
    """Unknown customer type or promo code."""


class TransactionStateError(POSError):
    """Action not allowed in the transaction's current state (e.g. already paid)."""


class AuthenticationError(POSError):
    """Wrong username/password, or nobody is logged in."""


class PermissionDeniedError(POSError):
    """The logged-in user's role is not allowed to do this."""


class StorageError(POSError):
    """A CSV file is missing, unreadable, or could not be written."""


class AccountLockedError(AuthenticationError):
    """Too many wrong passwords; the account is locked for a short time."""

