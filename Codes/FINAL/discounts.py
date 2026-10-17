from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation

from config import SENIOR_PWD_RATE
from errors import ValidationError
from validators import money


class Discount(ABC):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def compute_discount(self, subtotal: Decimal) -> Decimal:
        """Return the peso amount to deduct from subtotal."""


class NoDiscount(Discount):
    def __init__(self):
        super().__init__("None")

    def compute_discount(self, subtotal: Decimal) -> Decimal:
        return Decimal("0.00")


class SeniorDiscount(Discount):
    def __init__(self):
        super().__init__("Senior Citizen (20%)")

    def compute_discount(self, subtotal: Decimal) -> Decimal:
        return money(subtotal * SENIOR_PWD_RATE)


class PWDDiscount(Discount):
    def __init__(self):
        super().__init__("PWD (20%)")

    def compute_discount(self, subtotal: Decimal) -> Decimal:
        return money(subtotal * SENIOR_PWD_RATE)


class PromoDiscount(Discount):
    def __init__(self, name: str, percent):
        try:
            pct = Decimal(str(percent).strip())
        except InvalidOperation:
            raise ValidationError(f"Promo {name!r}: bad percent {percent!r}.") from None
        if not pct.is_finite() or not (Decimal("0") < pct <= Decimal("100")):
            raise ValidationError(f"Promo {name!r}: percent must be above 0 and at most 100.")
        super().__init__(f"{name} ({pct.normalize():f}%)")
        self._percent = pct

    def compute_discount(self, subtotal: Decimal) -> Decimal:
        return money(subtotal * self._percent / Decimal("100"))


