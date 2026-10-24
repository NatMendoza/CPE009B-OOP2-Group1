from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from config import MAX_QTY, VAT_RATE
from discounts import Discount, NoDiscount
from errors import (EmptyCartError, InsufficientPaymentError, InsufficientStockError,
                    InvalidQuantityError, TransactionStateError)
from items import Item
from validators import money, parse_quantity


# one row in the cart
@dataclass
class CartLine:
    serial: str
    name: str
    unit_price: Decimal   # price is copied at time of sale, so later price
    quantity: int         # changes never alter old receipts

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


# one sale, from an empty cart until it is paid or cancelled
class Transaction:
    def __init__(self, transaction_id: str, cashier_username: str):
        self._id = transaction_id
        self._cashier = cashier_username
        # cart items, saved by serial number
        self._lines: dict[str, CartLine] = {}
        self._discount: Discount = NoDiscount()
        self._customer_type = "regular"
        self._status = "open"          # open to paid or cancelled
        self._payment: Decimal | None = None
        self._change: Decimal | None = None
        self._completed_at: datetime | None = None

    # read-only info
    @property
    def transaction_id(self): return self._id
    @property
    def cashier(self): return self._cashier
    @property
    def status(self): return self._status
    @property
    def customer_type(self): return self._customer_type
    @property
    def discount_name(self): return self._discount.name
    @property
    def payment(self): return self._payment
    @property
    def change(self): return self._change
    @property
    def completed_at(self): return self._completed_at
    @property
    def lines(self) -> list[CartLine]: return list(self._lines.values())
    @property
    def item_count(self) -> int: return sum(l.quantity for l in self._lines.values())

    def _require_open(self):
        if self._status != "open":
            raise TransactionStateError(f"Transaction {self._id} is already {self._status}.")

    # cart operations
    def add_item(self, item: Item, qty):
        self._require_open()
        qty = parse_quantity(qty)
        # how many of this item are already in the cart
        already = self._lines[item.serial].quantity if item.serial in self._lines else 0
        # can't sell more than what is in stock
        if already + qty > item.stock:
            raise InsufficientStockError(
                f"Only {item.stock} of {item.name} in stock ({already} already in cart)."
            )
        # or more than the cart limit
        if already + qty > MAX_QTY:
            raise InvalidQuantityError(f"Cannot have more than {MAX_QTY} of one item in a cart.")
        if item.serial in self._lines:
            self._lines[item.serial].quantity += qty
        else:
            self._lines[item.serial] = CartLine(item.serial, item.name, item.price, qty)

    def set_quantity(self, item: Item, qty):
        # Replace the quantity (for a +/- or edit box in the GUI).
        self._require_open()
        qty = parse_quantity(qty)
        if item.serial not in self._lines:
            raise TransactionStateError(f"{item.name} is not in the cart.")
        if qty > item.stock:
            raise InsufficientStockError(f"Only {item.stock} of {item.name} in stock.")
        self._lines[item.serial].quantity = qty

    def remove_item(self, serial: str):
        # Void one line from the cart.
        self._require_open()
        if serial not in self._lines:
            raise TransactionStateError("That item is not in the cart.")
        del self._lines[serial]

    def clear(self):
        self._require_open()
        self._lines.clear()

    def set_discount(self, discount: Discount, customer_type: str):
        self._require_open()
        self._discount = discount
        self._customer_type = customer_type

    # money (computed on demand, so they can never go out of sync)
    # the money below is computed every time so it never goes out of sync
    @property
    def subtotal(self) -> Decimal:
        return sum((l.line_total for l in self._lines.values()), Decimal("0.00"))

    @property
    def discount_amount(self) -> Decimal:
        # POLYMORPHISM: we don't know/care which Discount subclass this is
        return min(self._discount.compute_discount(self.subtotal), self.subtotal)

    @property
    def net_amount(self) -> Decimal:
        return self.subtotal - self.discount_amount

    @property
    def vat(self) -> Decimal:
        # prices already include VAT, so VAT = the 12% part inside the net amount
        return money(self.net_amount / (1 + VAT_RATE) * VAT_RATE)

    @property
    def total(self) -> Decimal:
        return self.net_amount

    # payment
    def change_for(self, amount) -> Decimal:
        # Preview of the change. Does not change the transaction.
        return max(money(amount) - self.total, Decimal("0.00"))

    # checks the cart and the payment, then marks the sale as paid
    def pay(self, amount) -> Decimal:
        self._require_open()
        if not self._lines:
            raise EmptyCartError("The cart is empty. Add at least one item before paying.")
        amt = money(amount)
        # payment must cover the total
        if amt < self.total:
            raise InsufficientPaymentError(
                f"Payment of PHP {amt:,.2f} is short. Total is PHP {self.total:,.2f}."
            )
        self._payment = amt
        self._change = amt - self.total
        self._status = "paid"
        # the payment time is used on the receipt
        self._completed_at = datetime.now()
        return self._change

    def revert_payment(self):
        # Used by the backend if saving to disk fails after pay().
        self._payment = self._change = self._completed_at = None
        self._status = "open"

    def cancel(self):
        self._require_open()
        self._status = "cancelled"