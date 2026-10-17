from errors import InsufficientStockError, ValidationError
from validators import money, normalize_serial, parse_quantity
class Item:
    def __init__(self, serial, name, price, stock, category="Other", image=""):
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
        value = str(value).strip()
        if not value:
            raise ValidationError("Item name cannot be empty.")
        self._name = value

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        p = money(value)
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
        if n < 0:
            raise ValidationError("Stock cannot be negative.")
        self._stock = n

    @property
    def category(self) -> str:
        return self._category

    @category.setter
    def category(self, value):
        self._category = str(value).strip() or "Other"

    @property
    def image(self) -> str:
        return self._image

    @image.setter
    def image(self, value):
        self._image = str(value or "").strip()

    def reduce_stock(self, qty: int):
        if qty > self._stock:
            raise InsufficientStockError(f"Only {self._stock} of {self._name} left in stock.")
        self._stock -= qty

    def add_stock(self, qty):
        self._stock += parse_quantity(qty)

