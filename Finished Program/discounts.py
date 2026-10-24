# Discounts: ABSTRACTION (Discount), INHERITANCE (FixedRate to Senior/PWD/...),
# POLYMORPHISM (every subclass answers compute_discount() its own way).
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation

from config import FIXED_DISCOUNT_RATE
from errors import InvalidDiscountError, ValidationError
from validators import money


# parent class for all discounts, you can't make a Discount directly
class Discount(ABC):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    # every discount has to write its own compute_discount
    @abstractmethod
    def compute_discount(self, subtotal: Decimal) -> Decimal:
        # Return the peso amount to deduct from subtotal.
        pass


# no discount, used for regular customers
class NoDiscount(Discount):
    def __init__(self):
        super().__init__("None")

    def compute_discount(self, subtotal: Decimal) -> Decimal:
        return Decimal("0.00")


class FixedRateDiscount(Discount):
    # Shared logic for the fixed 20% discounts (PWD / Senior / More).

    def __init__(self, name: str, rate: Decimal = FIXED_DISCOUNT_RATE):
        super().__init__(name)
        self._rate = rate

    def compute_discount(self, subtotal: Decimal) -> Decimal:
        return money(subtotal * self._rate)


class SeniorDiscount(FixedRateDiscount):
    def __init__(self):
        super().__init__("Senior Citizen (20%)")


class PWDDiscount(FixedRateDiscount):
    def __init__(self):
        super().__init__("PWD (20%)")


class SoloParentDiscount(FixedRateDiscount):
    # The 'More' in the requirement. Add another class like this for any other group.

    def __init__(self):
        super().__init__("Solo Parent (20%)")


# promo with a percent off that the admin can set
class PromoDiscount(Discount):
    def __init__(self, name: str, percent):
        base = str(name or "").strip()
        if not base:
            raise ValidationError("Promo name cannot be empty.")
        try:
            pct = Decimal(str(percent).strip())
        except InvalidOperation:
            raise ValidationError(f"Promo {base!r}: bad percent {percent!r}.") from None
        # percent must be above 0 and up to 100
        if not pct.is_finite() or not (Decimal("0") < pct <= Decimal("100")):
            raise ValidationError(f"Promo {base!r}: percent must be above 0 and at most 100.")
        super().__init__(f"{base} ({pct.normalize():f}%)")
        self._base_name = base
        self._percent = pct

    @property
    def base_name(self) -> str:
        return self._base_name

    @property
    def percent(self) -> Decimal:
        return self._percent

    def compute_discount(self, subtotal: Decimal) -> Decimal:
        return money(subtotal * self._percent / Decimal("100"))


# customer type to class. Adding a new fixed discount = one class and one line here.
FIXED_DISCOUNTS = {
    "senior": SeniorDiscount,
    "pwd": PWDDiscount,
    "solo_parent": SoloParentDiscount,
}


# makes the right discount from the customer type
def create_fixed_discount(kind: str) -> Discount:
    cls = FIXED_DISCOUNTS.get(kind)
    if cls is None:
        raise InvalidDiscountError(f"Unknown customer type: {kind!r}")
    return cls()