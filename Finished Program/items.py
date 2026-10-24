# Item (ENCAPSULATION): private attributes, validated through properties.
from errors import InsufficientStockError, InvalidQuantityError, ValidationError
from validators import money, normalize_serial, parse_quantity


class Item:
    def __init__(self, serial, name, price, stock, category="Other", image=""):
        # the serial is cleaned and checked first
        self._serial = normalize_serial(serial)
        self.name = name          # these go through the setters below,
        self.price = price        # so bad data is rejected at creation too
        self.stock = stock
        self.category = category
        self.image = image

    @property
    def serial(self) -> str:      # read-only: no setter on purpose
        return self._serial

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value):
        value = str(value or "").strip()
        if not value:
            raise ValidationError("Item name cannot be empty.")
        self._name = value

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        p = money(value)
        # price can't be zero or negative
        if p <= 0:
            raise ValidationError(f"Price must be greater than 0 (item {self._serial}).")
        self._price = p

    @property
    def stock(self) -> int:
        return self._stock

    @stock.setter
    def stock(self, value):
        try:
            n = int(str(value).strip())
        except ValueError:
            raise ValidationError(f"Stock must be a whole number, got {value!r}.") from None
        # stock can't go below zero
        if n < 0:
            raise ValidationError("Stock cannot be negative.")
        self._stock = n

    @property
    def category(self) -> str:
        return self._category

    @category.setter
    def category(self, value):
        # an empty category becomes Other
        self._category = str(value or "").strip() or "Other"

    @property
    def image(self) -> str:
        return self._image

    @image.setter
    def image(self, value):
        self._image = str(value or "").strip()

    # takes items out of stock when something is sold
    def reduce_stock(self, qty: int):
        if qty <= 0:
            raise InvalidQuantityError("Quantity must be at least 1.")
        if qty > self._stock:
            raise InsufficientStockError(f"Only {self._stock} of {self._name} left in stock.")
        self._stock -= qty

    # puts items back, used for restock and void
    def add_stock(self, qty):
        self._stock += parse_quantity(qty)

    # used when saving the item to the csv
    def to_row(self) -> dict:
        return {"serial": self._serial, "name": self._name, "price": f"{self._price:.2f}",
                "stock": self._stock, "category": self._category, "image": self._image}

    def __repr__(self):
        return f"Item({self._serial!r}, {self._name!r}, {self._price}, stock={self._stock})"