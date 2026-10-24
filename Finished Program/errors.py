class POSError(Exception):
    # Base class for all expected POS errors. The GUI can catch just this.
    pass


class ValidationError(POSError):
    # A field (name, price, stock, username...) has a bad value.
    pass


class InvalidSerialError(POSError):
    # Serial number is not in the SN-#### format.
    pass


class ItemNotFoundError(POSError):
    # No item matches the serial number.
    pass


class InvalidQuantityError(POSError):
    # Quantity is not a whole number between 1 and the maximum.
    pass


class InvalidAmountError(POSError):
    # A peso amount could not be understood.
    pass


class InsufficientStockError(POSError):
    # Not enough stock to sell the requested quantity.
    pass


class InsufficientPaymentError(POSError):
    # Payment is less than the total.
    pass


class EmptyCartError(POSError):
    # Tried to check out with nothing in the cart.
    pass


class InvalidDiscountError(POSError):
    # Unknown customer type or promo.
    pass


class TransactionStateError(POSError):
    # Action not allowed in the transaction's current state (e.g. already paid).
    pass


class TransactionNotFoundError(POSError):
    # No saved transaction has that number.
    pass


class VoidError(POSError):
    # A transaction cannot be voided (for example it is already voided).
    pass


class DuplicateError(POSError):
    # That serial number, username or promo already exists.
    pass


class AuthenticationError(POSError):
    # Wrong username/password, or nobody is logged in.
    pass


class PermissionDeniedError(POSError):
    # The logged-in user's role is not allowed to do this.
    pass


class StorageError(POSError):
    # A CSV file is missing, unreadable, or could not be written.
    pass


class AccountLockedError(AuthenticationError):
    # Too many wrong passwords; the account is locked for a short time.
    pass