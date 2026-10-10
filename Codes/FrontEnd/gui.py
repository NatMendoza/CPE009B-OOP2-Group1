import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QLineEdit, QPushButton,
    QComboBox, QListWidget, QScrollArea, QGridLayout, QHBoxLayout, QVBoxLayout,
)

STORE_NAME = "Group 1 Grocery"
COLUMNS = 3

# the collections shown above the products
CATEGORIES = ["All", "Staples", "Canned Goods", "Instant", "Cooking"]

# serial number, name, price in php, category
PRODUCTS = [
    ("SN-1001", "Jasmine Rice 5kg", 285.00, "Staples"),
    ("SN-1002", "Fresh Eggs (dozen)", 108.00, "Staples"),
    ("SN-1003", "Pancit Canton", 16.00, "Instant"),
    ("SN-1004", "Canned Tuna 155g", 38.00, "Canned Goods"),
    ("SN-1005", "Corned Beef 150g", 52.00, "Canned Goods"),
    ("SN-1006", "Sardines in Tomato Sauce", 28.00, "Canned Goods"),
    ("SN-1007", "3-in-1 Coffee (10 sachets)", 70.00, "Instant"),
    ("SN-1008", "Cooking Oil 1L", 132.00, "Cooking"),
    ("SN-1009", "Soy Sauce 385ml", 28.00, "Cooking"),
    ("SN-1010", "White Sugar 1kg", 85.00, "Staples"),
]

# discount name and how much it takes off
DISCOUNTS = [
    ("No discount", 0),
    ("Promo 10% less", 0.10),
    ("Senior / PWD 20% less", 0.20),
]

# colors and styles, black and white only
STYLE = """
QWidget { font-size: 13px; color: #111111; }
QMainWindow, QWidget#root { background: #F2F2F2; }
QScrollArea { border: none; }

QFrame#header { background: #111111; border-bottom: 4px solid #777777; }
QFrame#header QLabel { color: white; background: transparent; }
QLabel#logo { background: white; color: #111111; border-radius: 8px; font-weight: bold; font-size: 20px; }
QLabel#store { font-size: 22px; font-weight: bold; }
QLabel#tagline { font-size: 12px; color: #BBBBBB; }
QFrame#header QLineEdit { background: #222222; border: 1px solid #555555; border-radius: 6px; padding: 10px 14px; color: white; }
QFrame#header QLineEdit:focus { border: 1px solid white; }

QFrame#register { background: white; border: 1px solid #CCCCCC; border-radius: 10px; }
QFrame#register QLabel { background: transparent; }
QLabel#regtitle { font-size: 16px; font-weight: bold; }
QLabel#total { font-size: 30px; font-weight: bold; }
QListWidget { border: none; border-top: 1px dashed #999999; border-bottom: 1px dashed #999999; }
QComboBox { background: white; border: 1px solid #CCCCCC; border-radius: 6px; padding: 6px; }

QPushButton { background: #E6E6E6; border: none; border-radius: 6px; padding: 9px; }
QPushButton:hover { background: #D4D4D4; }

QPushButton#cat { background: white; border: 1px solid #CCCCCC; border-radius: 16px; padding: 7px 18px; }
QPushButton#cat:hover { border: 1px solid #111111; }
QPushButton#cat:checked { background: #111111; color: white; border: 1px solid #111111; }

QFrame#card { background: white; border: 1px solid #CCCCCC; border-radius: 10px; }
QFrame#card:hover { border: 2px solid #111111; }
QFrame#card QLabel { background: transparent; border: none; }
QLabel#imgbox { background: #E6E6E6; color: #777777; border-radius: 8px; }
QLabel#cardname { font-weight: bold; }
QLabel#cardsn { color: #777777; }
QLabel#cardprice { font-weight: bold; font-size: 15px; }
"""


# makes a number look like ₱1,234.50
def php(v):
    return f"₱{v:,.2f}"


# one product in the grid, calls on_click with its serial number when clicked
class ProductCard(QFrame):
    def __init__(self, sn, name, price, category, on_click):
        super().__init__()
        self.sn = sn
        self.name = name
        self.category = category
        self.on_click = on_click
        self.setObjectName("card")

        # image goes here later
        image = QLabel("image")
        image.setObjectName("imgbox")
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setMinimumHeight(90)

        name_label = QLabel(name)
        name_label.setObjectName("cardname")
        name_label.setWordWrap(True)
        sn_label = QLabel(sn)
        sn_label.setObjectName("cardsn")
        price_label = QLabel(php(price))
        price_label.setObjectName("cardprice")

        # serial number on the left, price on the right
        bottom = QHBoxLayout()
        bottom.addWidget(sn_label)
        bottom.addStretch(1)
        bottom.addWidget(price_label)

        layout = QVBoxLayout(self)
        layout.addWidget(image)
        layout.addWidget(name_label)
        layout.addLayout(bottom)

    def mousePressEvent(self, event):
        self.on_click(self.sn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Group 1")
        self.resize(1100, 650)

        # cart is a list of serial numbers
        self.cart = []
        self.category = "All"
        self.names = {sn: name for sn, name, price, cat in PRODUCTS}
        self.prices = {sn: price for sn, name, price, cat in PRODUCTS}

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        # header: logo, store name, search box
        logo = QLabel("G1")
        logo.setObjectName("logo")
        logo.setFixedSize(52, 52)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        store = QLabel(STORE_NAME)
        store.setObjectName("store")
        tagline = QLabel("Point of Sale")
        tagline.setObjectName("tagline")
        names = QVBoxLayout()
        names.setSpacing(0)
        names.addWidget(store)
        names.addWidget(tagline)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by serial number")
        self.search.setMinimumWidth(380)
        self.search.textChanged.connect(lambda: self.show_cards())

        header = QFrame()
        header.setObjectName("header")
        head_layout = QHBoxLayout(header)
        head_layout.setContentsMargins(24, 16, 24, 16)
        head_layout.addWidget(logo)
        head_layout.addSpacing(6)
        head_layout.addLayout(names)
        head_layout.addStretch(1)
        head_layout.addWidget(self.search)

        # cash register on the left
        title = QLabel("Cash register")
        title.setObjectName("regtitle")
        self.cart_list = QListWidget()

        self.discount = QComboBox()
        for name, rate in DISCOUNTS:
            self.discount.addItem(name, rate)
        self.discount.currentIndexChanged.connect(self.update_total)

        self.total_label = QLabel()
        self.total_label.setObjectName("total")
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_cart)

        register = QFrame()
        register.setObjectName("register")
        register.setFixedWidth(340)
        reg_layout = QVBoxLayout(register)
        reg_layout.addWidget(title)
        reg_layout.addWidget(self.cart_list, 1)
        reg_layout.addWidget(self.discount)
        reg_layout.addWidget(QLabel("Total"))
        reg_layout.addWidget(self.total_label)
        reg_layout.addWidget(clear_button)

        # products on the right
        self.cards = []
        for sn, name, price, cat in PRODUCTS:
            self.cards.append(ProductCard(sn, name, price, cat, self.add_item))

        # collection buttons, only one can be selected
        cat_row = QHBoxLayout()
        for cat in CATEGORIES:
            button = QPushButton(cat)
            button.setObjectName("cat")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setChecked(cat == "All")
            button.clicked.connect(lambda checked, c=cat: self.pick_category(c))
            cat_row.addWidget(button)
        cat_row.addStretch(1)

        grid_widget = QWidget()
        self.grid = QGridLayout(grid_widget)
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        for col in range(COLUMNS):
            self.grid.setColumnStretch(col, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(grid_widget)

        # put everything together
        body = QHBoxLayout()
        body.setContentsMargins(16, 16, 16, 16)
        body.setSpacing(16)
        right = QVBoxLayout()
        right.addLayout(cat_row)
        right.addWidget(scroll, 1)

        body.addWidget(register)
        body.addLayout(right, 1)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(header)
        main_layout.addLayout(body, 1)

        self.show_cards()
        self.update_total()

    def pick_category(self, category):
        self.category = category
        self.show_cards()

    # only show the cards that match the search and the selected collection
    def show_cards(self):
        text = self.search.text().strip().lower()
        for card in self.cards:
            self.grid.removeWidget(card)
            card.hide()

        position = 0
        for card in self.cards:
            right_category = self.category == "All" or card.category == self.category
            matches = text in card.sn.lower() or text in card.name.lower()
            if right_category and matches:
                self.grid.addWidget(card, position // COLUMNS, position % COLUMNS)
                card.show()
                position += 1

    def add_item(self, sn):
        self.cart.append(sn)
        self.cart_list.addItem(f"{self.names[sn]}    {php(self.prices[sn])}")
        self.update_total()

    def update_total(self):
        subtotal = sum(self.prices[sn] for sn in self.cart)
        rate = self.discount.currentData()
        self.total_label.setText(php(subtotal * (1 - rate)))

    def clear_cart(self):
        self.cart.clear()
        self.cart_list.clear()
        self.update_total()


app = QApplication(sys.argv)
app.setStyleSheet(STYLE)
window = MainWindow()
window.show()
sys.exit(app.exec())