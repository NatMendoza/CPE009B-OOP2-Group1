import os
import sys

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget, QFrame, QLabel, QLineEdit,
    QPushButton, QComboBox, QListWidget, QListWidgetItem, QScrollArea, QGridLayout,
    QHBoxLayout, QVBoxLayout, QFormLayout, QDialog, QMessageBox,
)

# backend files, these stay as separate files
from config import STORE_NAME
from errors import POSError
from services import POSBackend
from users import User, Cashier
from validators import money


# shared styles and helpers

# colors and styles for all 3 pages, black and white only
STYLE = """
QWidget { font-size: 13px; color: #111111; }
QMainWindow, QStackedWidget { background: #F2F2F2; }
QWidget#gridhost { background: #F2F2F2; }
QScrollArea { border: none; }

QLineEdit { background: white; border: 1px solid #CCCCCC; border-radius: 6px; padding: 9px 12px; }
QLineEdit:focus { border: 1px solid #111111; }
QComboBox { background: white; border: 1px solid #CCCCCC; border-radius: 6px; padding: 6px; }

QPushButton { background: #E6E6E6; border: none; border-radius: 6px; padding: 9px; }
QPushButton:hover { background: #D4D4D4; }
QPushButton#primary { background: #111111; color: white; font-weight: bold; padding: 11px; }
QPushButton#primary:hover { background: #333333; }
QPushButton#toggle { background: transparent; font-weight: bold; padding: 0px; }
QPushButton#toggle:hover { color: #777777; }
QPushButton#cat, QPushButton#tab { background: white; border: 1px solid #CCCCCC; border-radius: 16px; padding: 7px 18px; }
QPushButton#cat:hover, QPushButton#tab:hover { border: 1px solid #111111; }
QPushButton#cat:checked, QPushButton#tab:checked { background: #111111; color: white; border: 1px solid #111111; }
QPushButton#tab { font-weight: bold; padding: 7px 26px; }

QFrame#header { background: #111111; border-bottom: 4px solid #777777; }
QFrame#header QLabel { color: white; background: transparent; }
QFrame#header QLabel#logo { background: white; color: #111111; border-radius: 8px; font-weight: bold; font-size: 20px; }
QFrame#header QLabel#store { font-size: 22px; font-weight: bold; }
QFrame#header QLabel#tagline { font-size: 12px; color: #BBBBBB; }
QFrame#header QLineEdit { background: #222222; border: 1px solid #555555; border-radius: 6px; padding: 10px 14px; color: white; }
QFrame#header QLineEdit:focus { border: 1px solid white; }
QFrame#header QPushButton { background: #333333; color: white; padding: 10px 18px; }
QFrame#header QPushButton:hover { background: #555555; }

QFrame#panel { background: white; border: 1px solid #CCCCCC; border-radius: 10px; }
QFrame#panel QLabel { background: transparent; }
QLabel#regtitle { font-size: 16px; font-weight: bold; }
QLabel#muted { color: #777777; }
QLabel#total { font-size: 30px; font-weight: bold; }
QListWidget { border: none; border-top: 1px dashed #999999; border-bottom: 1px dashed #999999; }
QListWidget::item { padding: 5px 2px; }
QListWidget::item:selected { background: #111111; color: white; }

QFrame#card { background: white; border: 1px solid #CCCCCC; border-radius: 10px; }
QFrame#card:hover { border: 2px solid #111111; }
QFrame#card QLabel { background: transparent; border: none; }
QFrame#card QLabel#imgbox { background: #E6E6E6; color: #777777; border-radius: 8px; }
QFrame#card QLabel#cardname { font-weight: bold; }
QFrame#card QLabel#cardsn { color: #777777; }
QFrame#card QLabel#cardprice { font-weight: bold; font-size: 15px; }

QFrame#logincard { background: white; border: 1px solid #CCCCCC; border-radius: 10px; }
QFrame#logincard QLabel { background: transparent; border: none; }
QFrame#logincard QLabel#logo { background: #111111; color: white; border-radius: 8px; font-weight: bold; font-size: 20px; }
QFrame#logincard QLabel#store { font-size: 22px; font-weight: bold; }
QFrame#logincard QLabel#tagline { font-size: 12px; color: #777777; }
QFrame#logincard QLabel#note { font-size: 11px; color: #999999; }
"""


# makes a number look like ₱1,234.50
def php(v):
    return f"₱{v:,.2f}"


def show_message(parent, icon, title, text):
    QMessageBox(icon, title, text, QMessageBox.StandardButton.Ok, parent).exec()


# label on the left and a value on the right, like "Subtotal      ₱100.00"
def make_row(text, value_label):
    row = QHBoxLayout()
    row.addWidget(QLabel(text))
    row.addStretch(1)
    row.addWidget(value_label)
    return row


# black bar on top of the pages. returns the bar and its layout
# so each page can add its own stuff on the right side
def make_header():
    header = QFrame()
    header.setObjectName("header")
    layout = QHBoxLayout(header)
    layout.setContentsMargins(24, 16, 24, 16)

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

    layout.addWidget(logo)
    layout.addSpacing(6)
    layout.addLayout(names)
    layout.addStretch(1)
    return header, layout


# page 1: login and register

# label, field name, is it a password, placeholder
REGISTER_FIELDS = [
    ("First Name:", "txt_first_name", False, "Enter your first name"),
    ("Last Name:", "txt_last_name", False, "Enter your last name"),
    ("Username:", "txt_username", False, "Choose a username"),
    ("Password:", "txt_password", True, "Choose a password"),
]


# password box with a show / hide button next to it
def make_password_row(edit):
    edit.setEchoMode(QLineEdit.EchoMode.Password)
    button = QPushButton("Show")
    button.setObjectName("toggle")
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setFixedWidth(45)

    def toggle():
        if edit.echoMode() == QLineEdit.EchoMode.Password:
            edit.setEchoMode(QLineEdit.EchoMode.Normal)
            button.setText("Hide")
        else:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            button.setText("Show")

    button.clicked.connect(toggle)

    row = QHBoxLayout()
    row.addWidget(edit)
    row.addWidget(button)
    return row


class LoginPage(QWidget):
    # sent when the login worked
    logged_in = pyqtSignal()

    def __init__(self, backend):
        super().__init__()
        self.backend = backend

        # logo and store name on top of the card
        logo = QLabel("G1")
        logo.setObjectName("logo")
        logo.setFixedSize(52, 52)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        store = QLabel(STORE_NAME)
        store.setObjectName("store")
        store.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline = QLabel("Point of Sale")
        tagline.setObjectName("tagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # login / register tabs
        self.tab_login = QPushButton("Login")
        self.tab_register = QPushButton("Register")
        for tab in (self.tab_login, self.tab_register):
            tab.setObjectName("tab")
            tab.setCheckable(True)
            tab.setAutoExclusive(True)
            tab.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab_login.setChecked(True)
        self.tab_login.clicked.connect(self.show_login)
        self.tab_register.clicked.connect(self.show_register)

        tabs = QHBoxLayout()
        tabs.addStretch(1)
        tabs.addWidget(self.tab_login)
        tabs.addWidget(self.tab_register)
        tabs.addStretch(1)

        # login form
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter your username")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Enter your password")
        self.login_password.returnPressed.connect(self.login)

        login_form = QFormLayout()
        login_form.setSpacing(12)
        login_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        login_form.addRow("Username:", self.login_username)
        login_form.addRow("Password:", make_password_row(self.login_password))

        login_button = QPushButton("Login")
        login_button.setObjectName("primary")
        login_button.clicked.connect(self.login)

        self.login_box = QWidget()
        login_layout = QVBoxLayout(self.login_box)
        login_layout.setContentsMargins(0, 0, 0, 0)
        login_layout.setSpacing(14)
        login_layout.addLayout(login_form)
        login_layout.addWidget(login_button)

        # register form
        self.inputs = {}
        register_form = QFormLayout()
        register_form.setSpacing(12)
        register_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        for label_text, field_name, is_password, placeholder in REGISTER_FIELDS:
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            self.inputs[field_name] = edit
            if is_password:
                register_form.addRow(label_text, make_password_row(edit))
            else:
                register_form.addRow(label_text, edit)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_form)
        submit_button = QPushButton("Submit")
        submit_button.setObjectName("primary")
        submit_button.clicked.connect(self.submit_form)
        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        buttons.addWidget(clear_button)
        buttons.addWidget(submit_button)

        self.register_box = QWidget()
        register_layout = QVBoxLayout(self.register_box)
        register_layout.setContentsMargins(0, 0, 0, 0)
        register_layout.setSpacing(14)
        register_layout.addLayout(register_form)
        register_layout.addLayout(buttons)
        self.register_box.hide()

        note = QLabel("New accounts are made as cashier accounts")
        note.setObjectName("note")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # put everything in the card
        card = QFrame()
        card.setObjectName("logincard")
        card.setFixedWidth(480)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 30, 35, 30)
        card_layout.setSpacing(12)
        card_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignHCenter)
        card_layout.addWidget(store)
        card_layout.addWidget(tagline)
        card_layout.addSpacing(6)
        card_layout.addLayout(tabs)
        card_layout.addSpacing(6)
        card_layout.addWidget(self.login_box)
        card_layout.addWidget(self.register_box)
        card_layout.addWidget(note)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    def show_login(self):
        self.register_box.hide()
        self.login_box.show()

    def show_register(self):
        self.login_box.hide()
        self.register_box.show()

    def login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()

        # the backend checks the password and the lockout
        try:
            self.backend.login(username, password)
        except POSError as e:
            show_message(self, QMessageBox.Icon.Warning, "Login Failed", str(e))
            return

        self.login_username.clear()
        self.login_password.clear()
        self.logged_in.emit()

    def submit_form(self):
        data = {}
        for field_name, edit in self.inputs.items():
            # password is not stripped because the backend hashes it exactly as typed
            data[field_name] = edit.text() if field_name == "txt_password" else edit.text().strip()

        # all fields are required
        if "" in data.values():
            show_message(self, QMessageBox.Icon.Warning, "Missing Information",
                         "All fields are required! Please fill in all empty fields before submitting.")
            return

        full_name = data["txt_first_name"] + " " + data["txt_last_name"]
        try:
            hashed = User.hash_password(data["txt_password"])
            self.backend.users.add(Cashier(data["txt_username"], hashed, full_name))
        except POSError as e:
            show_message(self, QMessageBox.Icon.Warning, "Registration Failed", str(e))
            return

        show_message(self, QMessageBox.Icon.Information, "Success",
                     "Account registered and saved successfully!")
        self.clear_form()

        # go back to the login tab
        self.tab_login.setChecked(True)
        self.show_login()

    def clear_form(self):
        for edit in self.inputs.values():
            edit.clear()


# page 2: products

COLUMNS = 3

# what is shown on screen, and the name the backend uses
CUSTOMER_TYPES = [
    ("Regular", "regular"),
    ("Senior Citizen 20% less", "senior"),
    ("PWD 20% less", "pwd"),
]


# one product in the grid, calls on_click with its serial number when clicked
class ProductCard(QFrame):
    def __init__(self, item, on_click):
        super().__init__()
        self.item = item
        self.on_click = on_click
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        image = QLabel("image")
        image.setObjectName("imgbox")
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setMinimumHeight(90)

        # use the real picture if the item has one
        if item.image and os.path.isfile(item.image):
            image.setPixmap(QPixmap(item.image).scaledToHeight(90, Qt.TransformationMode.SmoothTransformation))

        name_label = QLabel(item.name)
        name_label.setObjectName("cardname")
        name_label.setWordWrap(True)
        sn_label = QLabel(item.serial)
        sn_label.setObjectName("cardsn")
        price_label = QLabel(php(item.price))
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
        self.on_click(self.item.serial)


class ProductsPage(QWidget):
    checkout_clicked = pyqtSignal()
    logged_out = pyqtSignal()

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.category = "All"
        self.cards = []

        # header: search, user name and logout
        header, head_layout = make_header()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by serial number")
        self.search.setMinimumWidth(380)
        self.search.textChanged.connect(lambda: self.show_cards())
        self.user_label = QLabel()
        logout_button = QPushButton("Logout")
        logout_button.clicked.connect(self.logout)
        head_layout.addWidget(self.search)
        head_layout.addSpacing(16)
        head_layout.addWidget(self.user_label)
        head_layout.addWidget(logout_button)

        # cash register on the left
        title = QLabel("Cash register")
        title.setObjectName("regtitle")
        self.cart_list = QListWidget()

        minus_button = QPushButton("-")
        plus_button = QPushButton("+")
        remove_button = QPushButton("Remove")
        minus_button.clicked.connect(lambda: self.change_quantity(-1))
        plus_button.clicked.connect(lambda: self.change_quantity(1))
        remove_button.clicked.connect(lambda: self.remove_selected())
        item_buttons = QHBoxLayout()
        item_buttons.addWidget(minus_button)
        item_buttons.addWidget(plus_button)
        item_buttons.addWidget(remove_button, 1)

        self.customer = QComboBox()
        for text, kind in CUSTOMER_TYPES:
            self.customer.addItem(text, kind)
        self.customer.currentIndexChanged.connect(self.pick_customer)

        self.subtotal_label = QLabel()
        self.discount_label = QLabel()
        self.vat_label = QLabel()
        self.vat_label.setObjectName("muted")
        self.total_label = QLabel()
        self.total_label.setObjectName("total")

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_cart)
        checkout_button = QPushButton("Checkout")
        checkout_button.setObjectName("primary")
        checkout_button.clicked.connect(self.go_checkout)

        register = QFrame()
        register.setObjectName("panel")
        register.setFixedWidth(360)
        reg_layout = QVBoxLayout(register)
        reg_layout.addWidget(title)
        reg_layout.addWidget(self.cart_list, 1)
        reg_layout.addLayout(item_buttons)
        reg_layout.addWidget(self.customer)
        reg_layout.addLayout(make_row("Subtotal", self.subtotal_label))
        reg_layout.addLayout(make_row("Discount", self.discount_label))
        reg_layout.addWidget(self.vat_label)
        reg_layout.addWidget(QLabel("Total"))
        reg_layout.addWidget(self.total_label)
        reg_layout.addWidget(clear_button)
        reg_layout.addWidget(checkout_button)

        # collection buttons, in a row that can scroll sideways
        self.cat_box = QWidget()
        self.cat_box.setObjectName("gridhost")
        self.cat_layout = QHBoxLayout(self.cat_box)
        self.cat_layout.setContentsMargins(0, 0, 0, 8)
        cat_scroll = QScrollArea()
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setFixedHeight(62)
        cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cat_scroll.setWidget(self.cat_box)

        # product grid
        grid_widget = QWidget()
        grid_widget.setObjectName("gridhost")
        self.grid = QGridLayout(grid_widget)
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        for col in range(COLUMNS):
            self.grid.setColumnStretch(col, 1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(grid_widget)

        right = QVBoxLayout()
        right.addWidget(cat_scroll)
        right.addWidget(scroll, 1)

        # put everything together
        body = QHBoxLayout()
        body.setContentsMargins(16, 16, 16, 16)
        body.setSpacing(16)
        body.addWidget(register)
        body.addLayout(right, 1)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(header)
        main_layout.addLayout(body, 1)

    # called after login and after a sale, starts a fresh transaction
    def start_new(self):
        try:
            self.backend.start_transaction()
        except POSError as e:
            show_message(self, QMessageBox.Icon.Warning, "Cannot Start", str(e))
            return

        user = self.backend.current_user
        self.user_label.setText(f"{user.full_name} ({user.ROLE})")

        # a new transaction is always regular, so reset the dropdown without calling the backend
        self.customer.blockSignals(True)
        self.customer.setCurrentIndex(0)
        self.customer.blockSignals(False)

        self.category = "All"
        self.search.clear()
        self.load_categories()
        self.show_cards()
        self.refresh_cart()

    # called when coming back from the checkout page, keeps the same cart
    def resume(self):
        self.refresh_cart()

    def load_categories(self):
        # remove the old buttons first
        while self.cat_layout.count():
            widget = self.cat_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        for name in self.backend.categories():
            button = QPushButton(name)
            button.setObjectName("cat")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setChecked(name == self.category)
            button.clicked.connect(lambda checked, c=name: self.pick_category(c))
            self.cat_layout.addWidget(button)
        self.cat_layout.addStretch(1)

    def pick_category(self, name):
        self.category = name
        self.show_cards()

    # rebuilds the grid with the items that match the search and the collection
    def show_cards(self):
        for card in self.cards:
            self.grid.removeWidget(card)
            card.hide()
            card.deleteLater()
        self.cards = []

        category = None if self.category == "All" else self.category
        try:
            items = self.backend.search_items(self.search.text().strip(), category)
        except POSError:
            items = []      # half typed search text just shows nothing

        for position, item in enumerate(items):
            card = ProductCard(item, self.add_item)
            self.cards.append(card)
            self.grid.addWidget(card, position // COLUMNS, position % COLUMNS)

    def add_item(self, serial):
        try:
            self.backend.add_to_cart(serial)
        except POSError as e:
            show_message(self, QMessageBox.Icon.Warning, "Cannot Add Item", str(e))
            return
        self.refresh_cart(keep=serial)

    # + and - buttons change the quantity of the selected cart item
    def change_quantity(self, amount):
        row = self.cart_list.currentItem()
        if row is None:
            return
        serial = row.data(Qt.ItemDataRole.UserRole)
        line = next(l for l in self.backend.transaction.lines if l.serial == serial)
        new_quantity = line.quantity + amount

        try:
            if new_quantity < 1:
                self.backend.remove_from_cart(serial)
            else:
                self.backend.set_cart_quantity(serial, new_quantity)
        except POSError as e:
            show_message(self, QMessageBox.Icon.Warning, "Cannot Change Quantity", str(e))
        self.refresh_cart(keep=serial)

    def remove_selected(self):
        row = self.cart_list.currentItem()
        if row is None:
            return
        try:
            self.backend.remove_from_cart(row.data(Qt.ItemDataRole.UserRole))
        except POSError as e:
            show_message(self, QMessageBox.Icon.Warning, "Cannot Remove", str(e))
        self.refresh_cart()

    def clear_cart(self):
        try:
            self.backend.clear_cart()
        except POSError as e:
            show_message(self, QMessageBox.Icon.Warning, "Cannot Clear", str(e))
        self.refresh_cart()

    # redraws the cart list, keep is the serial number to keep selected
    def refresh_cart(self, keep=None):
        self.cart_list.clear()
        for line in self.backend.transaction.lines:
            row = QListWidgetItem(f"{line.quantity} × {line.name}    {php(line.line_total)}")
            row.setData(Qt.ItemDataRole.UserRole, line.serial)
            self.cart_list.addItem(row)
            if line.serial == keep:
                self.cart_list.setCurrentItem(row)
        self.update_totals()

    def pick_customer(self):
        try:
            self.backend.set_customer_type(self.customer.currentData())
        except POSError as e:
            show_message(self, QMessageBox.Icon.Warning, "Cannot Apply Discount", str(e))
        self.update_totals()

    # the backend does all the math, we just show it
    def update_totals(self):
        totals = self.backend.totals()
        self.subtotal_label.setText(php(totals["subtotal"]))
        self.discount_label.setText("-" + php(totals["discount"]))
        self.vat_label.setText(f"incl. 12% VAT: {php(totals['vat'])}")
        self.total_label.setText(php(totals["total"]))

    def go_checkout(self):
        if not self.backend.transaction.lines:
            show_message(self, QMessageBox.Icon.Warning, "Empty Cart",
                         "Add at least one item before checking out.")
            return
        self.checkout_clicked.emit()

    def logout(self):
        self.backend.cancel_transaction()
        self.backend.logout()
        self.logged_out.emit()


# page 3: checkout

# popup that shows the receipt after paying
class ReceiptDialog(QDialog):
    def __init__(self, text, saved_as, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Receipt")

        receipt = QLabel(text)
        receipt.setStyleSheet("font-family: Consolas, 'Courier New', monospace; background: white; padding: 16px;")
        done_button = QPushButton("New transaction")
        done_button.setObjectName("primary")
        done_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(receipt)
        if saved_as:
            note = QLabel(f"Saved as {saved_as.name}")
            note.setObjectName("muted")
            layout.addWidget(note)
        layout.addWidget(done_button)


class CheckoutPage(QWidget):
    back_clicked = pyqtSignal()
    sale_done = pyqtSignal()

    def __init__(self, backend):
        super().__init__()
        self.backend = backend

        # header with a back button
        header, head_layout = make_header()
        back_button = QPushButton("Back to products")
        back_button.clicked.connect(lambda: self.back_clicked.emit())
        head_layout.addWidget(back_button)

        # left side, what is being bought
        order_title = QLabel("Order summary")
        order_title.setObjectName("regtitle")
        self.items_list = QListWidget()
        self.discount_type = QLabel()
        self.discount_type.setObjectName("muted")

        order = QFrame()
        order.setObjectName("panel")
        order_layout = QVBoxLayout(order)
        order_layout.addWidget(order_title)
        order_layout.addWidget(self.items_list, 1)
        order_layout.addWidget(self.discount_type)

        # right side, the money part
        pay_title = QLabel("Payment")
        pay_title.setObjectName("regtitle")
        self.subtotal_label = QLabel()
        self.discount_label = QLabel()
        self.vat_label = QLabel()
        self.vat_label.setObjectName("muted")
        self.total_label = QLabel()
        self.total_label.setObjectName("total")

        self.payment = QLineEdit()
        self.payment.setPlaceholderText("Amount received")
        self.payment.textChanged.connect(lambda: self.update_change())
        self.payment.returnPressed.connect(self.pay)
        self.change_label = QLabel()

        pay_button = QPushButton("Pay")
        pay_button.setObjectName("primary")
        pay_button.clicked.connect(self.pay)

        payment_box = QFrame()
        payment_box.setObjectName("panel")
        payment_box.setFixedWidth(380)
        pay_layout = QVBoxLayout(payment_box)
        pay_layout.addWidget(pay_title)
        pay_layout.addLayout(make_row("Subtotal", self.subtotal_label))
        pay_layout.addLayout(make_row("Discount", self.discount_label))
        pay_layout.addWidget(self.vat_label)
        pay_layout.addStretch(1)
        pay_layout.addWidget(QLabel("Total"))
        pay_layout.addWidget(self.total_label)
        pay_layout.addSpacing(10)
        pay_layout.addWidget(self.payment)
        pay_layout.addLayout(make_row("Change", self.change_label))
        pay_layout.addWidget(pay_button)

        body = QHBoxLayout()
        body.setContentsMargins(16, 16, 16, 16)
        body.setSpacing(16)
        body.addWidget(order, 1)
        body.addWidget(payment_box)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(header)
        main_layout.addLayout(body, 1)

    # called every time this page is opened
    def load(self):
        transaction = self.backend.transaction
        self.items_list.clear()
        for line in transaction.lines:
            self.items_list.addItem(f"{line.quantity} × {line.name}    {php(line.line_total)}")
        self.discount_type.setText(f"Discount: {transaction.discount_name}")

        totals = self.backend.totals()
        self.subtotal_label.setText(php(totals["subtotal"]))
        self.discount_label.setText("-" + php(totals["discount"]))
        self.vat_label.setText(f"incl. 12% VAT: {php(totals['vat'])}")
        self.total_label.setText(php(totals["total"]))

        self.payment.clear()
        self.update_change()
        self.payment.setFocus()

    # shows the change while the cashier types the payment
    def update_change(self):
        try:
            change = money(self.payment.text()) - self.backend.totals()["total"]
        except POSError:
            self.change_label.setText(php(0))
            return

        if change < 0:
            self.change_label.setText("Short by " + php(-change))
        else:
            self.change_label.setText(php(change))

    def pay(self):
        # the backend checks the payment, saves the sale and makes the receipt
        try:
            receipt = self.backend.checkout(self.payment.text())
        except POSError as e:
            show_message(self, QMessageBox.Icon.Warning, "Payment Failed", str(e))
            return

        ReceiptDialog(receipt, self.backend.last_receipt_path, self).exec()
        self.sale_done.emit()


# main window

class MainWindow(QMainWindow):
    def __init__(self, backend):
        super().__init__()
        self.setWindowTitle("Group 1")

        # the 3 pages
        self.login_page = LoginPage(backend)
        self.products_page = ProductsPage(backend)
        self.checkout_page = CheckoutPage(backend)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.products_page)
        self.stack.addWidget(self.checkout_page)
        self.setCentralWidget(self.stack)

        # what each page does when it is finished
        self.login_page.logged_in.connect(self.after_login)
        self.products_page.checkout_clicked.connect(self.show_checkout)
        self.products_page.logged_out.connect(self.show_login)
        self.checkout_page.back_clicked.connect(self.back_to_products)
        self.checkout_page.sale_done.connect(self.after_login)

    def show_login(self):
        self.stack.setCurrentWidget(self.login_page)

    # also used after a sale, both start a new transaction
    def after_login(self):
        self.products_page.start_new()
        self.stack.setCurrentWidget(self.products_page)

    def show_checkout(self):
        self.checkout_page.load()
        self.stack.setCurrentWidget(self.checkout_page)

    def back_to_products(self):
        self.products_page.resume()
        self.stack.setCurrentWidget(self.products_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)

    # the csv files are in the data folder next to this file
    data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    try:
        backend = POSBackend(data_folder)
    except POSError as e:
        QMessageBox.critical(None, "Startup Error", str(e))
        sys.exit(1)

    window = MainWindow(backend)
    window.resize(1150, 700)
    window.show()

    # bad rows in the csv files that were skipped
    if backend.load_warnings:
        QMessageBox.warning(window, "Data Warnings", "\n".join(backend.load_warnings[:10]))

    sys.exit(app.exec())