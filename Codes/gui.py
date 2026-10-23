# Group 1 - Grocery Point of Sales (GUI)
# 3 main pages: login and register, store, checkout

import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget, QLabel,
    QLineEdit, QPushButton, QComboBox, QSpinBox, QCheckBox, QFrame, QScrollArea,
    QGridLayout, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QDialogButtonBox, QPlainTextEdit, QFileDialog, QInputDialog,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QFont, QPixmap, QColor, QIcon, QGuiApplication
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

# settings and the backend we made
from config import BASE_DIR, LOGO_PATH, STORE_NAME
from errors import POSError
from Registration import RegistrationWindow
from services import POSBackend
from validators import money


# Updated App Style: Matching Logo Lime Green Accent (#82B536 / #71A02B) with Clean Black/White & Maximized Space
APP_STYLE = """
QMainWindow, QDialog { background-color: #F8F9FA; }
QLabel { color: #111111; }

QLineEdit, QComboBox, QSpinBox {
    border: 1.5px solid #CED4DA; border-radius: 6px; padding: 5px 10px;
    background-color: #FFFFFF; color: #111111; font-size: 13px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 2px solid #71A02B; }

QPushButton {
    border: 1.5px solid #212529; border-radius: 6px; padding: 6px 12px;
    background-color: #FFFFFF; color: #212529; font-weight: 600; font-size: 13px;
}
QPushButton:hover { background-color: #F1F3F5; border-color: #71A02B; color: #71A02B; }
QPushButton:disabled { color: #ADB5BD; border-color: #DEE2E6; background-color: #F8F9FA; }

QPushButton#primary { background-color: #71A02B; color: white; border: none; font-weight: bold; }
QPushButton#primary:hover { background-color: #5F8A22; }
QPushButton#primary:disabled { background-color: #CED4DA; color: white; }

QPushButton#danger { color: #C92A2A; border: 1.5px solid #C92A2A; background-color: #FFF5F5; }
QPushButton#danger:hover { background-color: #FFE3E3; }

QFrame#topbar {
    background-color: #1A1A1A;
    border-bottom: 3px solid #71A02B;
}
QPushButton#topbtn {
    background-color: transparent; color: white; border: 1.5px solid rgba(255, 255, 255, 0.4);
    padding: 4px 10px; border-radius: 6px; font-size: 12px;
}
QPushButton#topbtn:hover { background-color: #71A02B; border-color: #71A02B; color: white; }

QFrame#card, QFrame#productCard, QFrame#cartPanel, QFrame#sidePanel {
    background-color: #FFFFFF; border: 1.5px solid #E0E0E0; border-radius: 10px;
}
QFrame#productCard:hover {
    border: 1.5px solid #71A02B;
}

QTableWidget { border: none; gridline-color: #E9ECEF; background-color: white; color: #212529; selection-background-color: #EBFbee; selection-color: #111111; }
QHeaderView::section {
    background-color: #F1F3F5; color: #212529; border: none; padding: 6px; font-weight: 600;
}

QTabWidget::pane { border: none; }
QTabBar::tab { padding: 8px 24px; color: #495057; font-weight: 600; }
QTabBar::tab:selected { color: #71A02B; border-bottom: 3px solid #71A02B; }
"""

CUSTOMER_TYPES = [
    ("Regular", "regular"),
    ("Senior Citizen (20% off)", "senior"),
    ("PWD (20% off)", "pwd"),
    ("Solo Parent (20% off)", "solo_parent"),
    ("Promo", "promo"),
]


def peso(amount):
    return f"₱{amount:,.2f}"


def show_error(parent, error):
    QMessageBox.warning(parent, "Oops", str(error))


def show_info(parent, title, text):
    QMessageBox.information(parent, title, text)


def load_image(path, width, height):
    if not path:
        return None
    full_path = BASE_DIR / path
    if not full_path.is_file():
        return None
    pix = QPixmap(str(full_path))
    if pix.isNull():
        return None
    return pix.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio,
                      Qt.TransformationMode.SmoothTransformation)


def make_logo_label(size):
    lbl = QLabel()
    lbl.setFixedSize(size, size)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pix = load_image(str(LOGO_PATH), size, size)
    if pix:
        lbl.setPixmap(pix)
        lbl.setStyleSheet("border: none; background: transparent;")
    else:
        lbl.setText("LOGO")
        lbl.setStyleSheet("background-color: #71A02B; color: white; font-weight: bold; "
                          "border: none; border-radius: 8px;")
    return lbl


def add_shadow(widget):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(20)
    shadow.setXOffset(0)
    shadow.setYOffset(4)
    shadow.setColor(QColor(0, 0, 0, 30))
    widget.setGraphicsEffect(shadow)


class TextDialog(QDialog):
    def __init__(self, title, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(460, 560)

        layout = QVBoxLayout(self)
        box = QPlainTextEdit()
        box.setReadOnly(True)
        box.setPlainText(text)
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        box.setFont(font)
        layout.addWidget(box)

        btn_close = QPushButton("Close")
        btn_close.setObjectName("primary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class LoginPage(QWidget):
    logged_in = pyqtSignal()
    go_register = pyqtSignal()

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.initUI()

    def initUI(self):
        self.setObjectName("loginRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget#loginRoot {
                background-color: #1A1A1A;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(460)
        add_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 30, 35, 30)
        card_layout.setSpacing(12)

        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_row.addWidget(make_logo_label(70))
        card_layout.addLayout(logo_row)

        title = QLabel(STORE_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("border: none; color: #111111;")
        
        subtitle = QLabel("Point of Sales")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #71A02B; font-weight: 600; border: none;")
        
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(10)

        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Username")
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Password")
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)

        self.chk_show = QCheckBox("Show password")
        self.chk_show.toggled.connect(self.toggle_password)

        self.btn_login = QPushButton("Login")
        self.btn_login.setObjectName("primary")
        self.btn_login.setMinimumHeight(40)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self.do_login)

        self.txt_user.returnPressed.connect(self.txt_pass.setFocus)
        self.txt_pass.returnPressed.connect(self.do_login)

        card_layout.addWidget(self.txt_user)
        card_layout.addWidget(self.txt_pass)
        card_layout.addWidget(self.chk_show)
        card_layout.addWidget(self.btn_login)

        btn_register = QPushButton("No account yet? Register here")
        btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_register.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #71A02B;
                text-decoration: underline;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #5F8A22;
            }
        """)
        btn_register.clicked.connect(self.go_register.emit)
        card_layout.addWidget(btn_register)

        outer_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    def toggle_password(self, checked):
        if checked:
            self.txt_pass.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)

    @pyqtSlot()
    def do_login(self):
        username = self.txt_user.text().strip()
        password = self.txt_pass.text()

        if not username or not password:
            show_info(self, "Missing Information", "Please enter your username and password.")
            return

        try:
            self.backend.login(username, password)
        except POSError as e:
            show_error(self, e)
            self.txt_pass.clear()
            return

        self.txt_pass.clear()
        self.logged_in.emit()


class AddProductDialog(QDialog):
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.setWindowTitle("Add Product")
        self.setMinimumWidth(420)

        form = QFormLayout()
        self.txt_serial = QLineEdit(self.next_serial())
        self.txt_name = QLineEdit()
        self.txt_price = QLineEdit()
        self.txt_price.setPlaceholderText("e.g. 45.50")
        self.spn_stock = QSpinBox()
        self.spn_stock.setRange(0, 99999)
        self.spn_stock.setValue(50)

        self.cmb_category = QComboBox()
        self.cmb_category.setEditable(True)
        self.cmb_category.addItems(self.backend.items.categories())

        self.txt_image = QLineEdit()
        self.txt_image.setPlaceholderText("Optional, e.g. images/SN-1101.png")
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse_image)
        image_row = QHBoxLayout()
        image_row.addWidget(self.txt_image)
        image_row.addWidget(btn_browse)

        form.addRow("Serial No.:", self.txt_serial)
        form.addRow("Name:", self.txt_name)
        form.addRow("Price (₱):", self.txt_price)
        form.addRow("Stock:", self.spn_stock)
        form.addRow("Category:", self.cmb_category)
        form.addRow("Image:", image_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_product)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def next_serial(self):
        numbers = [int(i.serial[3:]) for i in self.backend.items.all()]
        return f"SN-{max(numbers) + 1}" if numbers else "SN-1001"

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose image", str(BASE_DIR),
                                              "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        try:
            path = str(Path(path).relative_to(BASE_DIR))
        except ValueError:
            pass
        self.txt_image.setText(path.replace("\\", "/"))

    def save_product(self):
        try:
            self.backend.add_item(
                self.txt_serial.text(), self.txt_name.text(), self.txt_price.text(),
                self.spn_stock.value(), self.cmb_category.currentText(),
                self.txt_image.text())
        except POSError as e:
            show_error(self, e)
            return
        show_info(self, "Saved", "Product added!")
        self.accept()


class VoidDialog(QDialog):
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.setWindowTitle("Void a Sale")
        self.setMinimumWidth(480)

        form = QFormLayout()
        self.cmb_sales = QComboBox()
        try:
            for t in self.backend.recent_transactions(30):
                text = f"{t['transaction_id']}  |  ₱{t['total']}  |  {t['status']}"
                self.cmb_sales.addItem(text, t["transaction_id"])
        except POSError as e:
            show_error(self, e)
        self.txt_reason = QLineEdit()
        self.txt_reason.setPlaceholderText("Why is this sale being voided?")
        form.addRow("Sale:", self.cmb_sales)
        form.addRow("Reason:", self.txt_reason)

        btn_void = QPushButton("Void Sale")
        btn_void.setObjectName("danger")
        btn_void.clicked.connect(self.do_void)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.reject)
        row = QHBoxLayout()
        row.addWidget(btn_close)
        row.addWidget(btn_void)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(row)

    def do_void(self):
        txn_id = self.cmb_sales.currentData()
        if not txn_id:
            show_info(self, "No Sale", "There is no sale to void.")
            return

        answer = QMessageBox.question(
            self, "Are you sure?",
            f"Void {txn_id}?\nThe items will be returned to stock.")
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            result = self.backend.void_transaction(txn_id, self.txt_reason.text())
        except POSError as e:
            show_error(self, e)
            return

        message = f"{result['transaction_id']} was voided.\n{result['restored_items']} item(s) returned to stock."
        if result["skipped_serials"]:
            message += "\nSkipped (product no longer exists): " + ", ".join(result["skipped_serials"])
        show_info(self, "Voided", message)
        self.accept()


class StorePage(QWidget):
    go_checkout = pyqtSignal()
    logged_out = pyqtSignal()

    COLUMNS = 4                    # Increased columns to maximize space usage horizontally

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.cart_serials = []
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.build_topbar())

        body = QHBoxLayout()
        body.setContentsMargins(10, 10, 10, 10)  # Reduced padding to maximize space
        body.setSpacing(12)
        body.addLayout(self.build_product_area(), 1)
        body.addWidget(self.build_cart_panel())
        main_layout.addLayout(body)

    def build_topbar(self):
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(65)
        row = QHBoxLayout(topbar)
        row.setContentsMargins(15, 0, 15, 0)

        row.addWidget(make_logo_label(40))
        lbl_store = QLabel(STORE_NAME)
        lbl_store.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lbl_store.setStyleSheet("color: white;")
        row.addWidget(lbl_store)
        row.addStretch()

        self.lbl_user = QLabel("")
        self.lbl_user.setStyleSheet("color: #E0E0E0; font-weight: 500;")
        row.addWidget(self.lbl_user)

        self.btn_add_product = QPushButton("Add Product")
        self.btn_report = QPushButton("Sales Report")
        self.btn_void = QPushButton("Void Sale")
        self.btn_password = QPushButton("Change Password")
        self.btn_logout = QPushButton("Logout")
        for btn in (self.btn_add_product, self.btn_report, self.btn_void,
                    self.btn_password, self.btn_logout):
            btn.setObjectName("topbtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            row.addWidget(btn)

        self.btn_add_product.clicked.connect(self.open_add_product)
        self.btn_report.clicked.connect(self.show_report)
        self.btn_void.clicked.connect(self.open_void)
        self.btn_password.clicked.connect(self.change_password)
        self.btn_logout.clicked.connect(self.do_logout)
        return topbar

    def build_product_area(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)

        search_row = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search by name or serial number (e.g. SN-1045), Enter adds it to the cart")
        self.txt_search.setMinimumHeight(36)
        self.txt_search.textChanged.connect(self.load_products)
        self.txt_search.returnPressed.connect(self.search_enter)

        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumHeight(36)
        self.cmb_category.setMinimumWidth(180)
        self.cmb_category.currentIndexChanged.connect(self.load_products)

        search_row.addWidget(self.txt_search)
        search_row.addWidget(self.cmb_category)
        layout.addLayout(search_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_holder = QWidget()
        self.grid = QGridLayout(self.grid_holder)
        self.grid.setSpacing(10)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self.grid_holder)
        layout.addWidget(scroll)
        return layout

    def build_cart_panel(self):
        panel = QFrame()
        panel.setObjectName("cartPanel")
        panel.setFixedWidth(360)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Current Cart")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("border: none;")
        self.lbl_txn = QLabel("")
        self.lbl_txn.setStyleSheet("color: #6C757D; font-size: 11px; border: none;")
        layout.addWidget(title)
        layout.addWidget(self.lbl_txn)

        self.tbl_cart = QTableWidget(0, 3)
        self.tbl_cart.setHorizontalHeaderLabels(["Item", "Qty", "Total"])
        self.tbl_cart.verticalHeader().setVisible(False)
        self.tbl_cart.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_cart.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_cart.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        header = self.tbl_cart.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tbl_cart)

        btn_row = QHBoxLayout()
        btn_minus = QPushButton("-")
        btn_plus = QPushButton("+")
        btn_remove = QPushButton("Remove")
        btn_clear = QPushButton("Clear")
        btn_remove.setObjectName("danger")
        btn_clear.setObjectName("danger")
        for btn in (btn_minus, btn_plus, btn_remove, btn_clear):
            btn_row.addWidget(btn)
        btn_minus.clicked.connect(self.cart_minus)
        btn_plus.clicked.connect(self.cart_plus)
        btn_remove.clicked.connect(self.cart_remove)
        btn_clear.clicked.connect(self.cart_clear)
        layout.addLayout(btn_row)

        self.lbl_subtotal = QLabel("")
        self.lbl_subtotal.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_subtotal.setStyleSheet("border: none; color: #212529;")
        layout.addWidget(self.lbl_subtotal)

        btn_checkout = QPushButton("Proceed to Checkout")
        btn_checkout.setObjectName("primary")
        btn_checkout.setMinimumHeight(42)
        btn_checkout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_checkout.clicked.connect(self.to_checkout)
        layout.addWidget(btn_checkout)
        return panel

    def on_show(self):
        user = self.backend.current_user
        self.lbl_user.setText(f"{user.greeting()}   [{user.dashboard_title()}]")

        self.btn_add_product.setVisible(user.can("manage_items"))
        self.btn_report.setVisible(user.can("view_reports"))
        self.btn_void.setVisible(user.can("void_sales"))

        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItems(self.backend.categories())
        self.cmb_category.blockSignals(False)

        self.txt_search.blockSignals(True)
        self.txt_search.clear()
        self.txt_search.blockSignals(False)

        self.load_products()
        self.load_cart()

    def load_products(self, *args):
        while self.grid.count():
            widget = self.grid.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        query = self.txt_search.text()
        category = self.cmb_category.currentText()
        try:
            items = self.backend.search_items(query, category)
        except POSError as e:
            show_error(self, e)
            return

        if not items:
            self.grid.addWidget(QLabel("No products found."), 0, 0)
            return

        for index, item in enumerate(items):
            row = index // self.COLUMNS
            col = index % self.COLUMNS
            self.grid.addWidget(self.make_card(item), row, col)

    def make_card(self, item):
        card = QFrame()
        card.setObjectName("productCard")
        card.setFixedSize(185, 255)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        img = QLabel()
        img.setFixedSize(161, 90)
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = load_image(item.image, 161, 90)
        if pix:
            img.setPixmap(pix)
            img.setStyleSheet("border: none;")
        else:
            img.setText("No image yet")
            img.setStyleSheet("background-color: #F8F9FA; color: #ADB5BD; border: none; border-radius: 6px; font-size: 11px;")
        layout.addWidget(img)

        lbl_name = QLabel(item.name)
        lbl_name.setWordWrap(True)
        lbl_name.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_name.setStyleSheet("border: none; color: #212529;")
        
        lbl_serial = QLabel(item.serial)
        lbl_serial.setStyleSheet("color: #6C757D; font-size: 10px; border: none;")
        
        lbl_price = QLabel(peso(item.price))
        lbl_price.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_price.setStyleSheet("color: #71A02B; border: none;")
        
        lbl_stock = QLabel(f"Stock: {item.stock}")
        lbl_stock.setStyleSheet("color: #6C757D; font-size: 10px; border: none;")

        btn_add = QPushButton("Add to Cart")
        btn_add.setObjectName("primary")
        btn_add.setFixedHeight(30)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        if item.stock == 0:
            btn_add.setText("Out of stock")
            btn_add.setEnabled(False)

        btn_add.clicked.connect(lambda checked, serial=item.serial: self.add_to_cart(serial))

        layout.addWidget(lbl_name)
        layout.addWidget(lbl_serial)
        layout.addStretch()
        layout.addWidget(lbl_price)
        layout.addWidget(lbl_stock)
        layout.addWidget(btn_add)
        return card

    def search_enter(self):
        text = self.txt_search.text().strip()
        if not text:
            return
        try:
            item = self.backend.get_item(text)
        except POSError:
            return
        self.add_to_cart(item.serial)
        self.txt_search.clear()

    def add_to_cart(self, serial):
        try:
            self.backend.add_to_cart(serial, 1)
        except POSError as e:
            show_error(self, e)
            return
        self.load_cart()

    def load_cart(self):
        lines = self.backend.cart_lines()
        self.cart_serials = [line["serial"] for line in lines]

        self.tbl_cart.setRowCount(len(lines))
        for row, line in enumerate(lines):
            name = QTableWidgetItem(line["name"])
            qty = QTableWidgetItem(str(line["quantity"]))
            total = QTableWidgetItem(peso(line["line_total"]))
            qty.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tbl_cart.setItem(row, 0, name)
            self.tbl_cart.setItem(row, 1, qty)
            self.tbl_cart.setItem(row, 2, total)

        totals = self.backend.totals()
        self.lbl_subtotal.setText(f"Subtotal ({totals['item_count']} items): {peso(totals['subtotal'])}")
        self.lbl_txn.setText(f"Transaction No: {self.backend.transaction.transaction_id}")

    def selected_serial(self):
        row = self.tbl_cart.currentRow()
        if row < 0 or row >= len(self.cart_serials):
            show_info(self, "Select an item", "Click an item in the cart first.")
            return None
        return self.cart_serials[row]

    def current_quantity(self, serial):
        for line in self.backend.cart_lines():
            if line["serial"] == serial:
                return line["quantity"]
        return 0

    def change_quantity(self, amount):
        serial = self.selected_serial()
        if serial is None:
            return
        row = self.tbl_cart.currentRow()
        new_qty = self.current_quantity(serial) + amount
        try:
            if new_qty <= 0:
                self.backend.remove_from_cart(serial)
            else:
                self.backend.set_cart_quantity(serial, new_qty)
        except POSError as e:
            show_error(self, e)
            return
        self.load_cart()
        if row < self.tbl_cart.rowCount():
            self.tbl_cart.selectRow(row)

    @pyqtSlot()
    def cart_plus(self):
        self.change_quantity(1)

    @pyqtSlot()
    def cart_minus(self):
        self.change_quantity(-1)

    @pyqtSlot()
    def cart_remove(self):
        serial = self.selected_serial()
        if serial is None:
            return
        try:
            self.backend.remove_from_cart(serial)
        except POSError as e:
            show_error(self, e)
            return
        self.load_cart()

    @pyqtSlot()
    def cart_clear(self):
        if not self.cart_serials:
            return
        answer = QMessageBox.question(self, "Clear cart", "Remove everything from the cart?")
        if answer == QMessageBox.StandardButton.Yes:
            self.backend.clear_cart()
            self.load_cart()

    @pyqtSlot()
    def to_checkout(self):
        if not self.cart_serials:
            show_info(self, "Empty cart", "Add at least one item before checking out.")
            return
        self.go_checkout.emit()

    @pyqtSlot()
    def open_add_product(self):
        dialog = AddProductDialog(self.backend, self)
        if dialog.exec():
            self.on_show()

    @pyqtSlot()
    def open_void(self):
        dialog = VoidDialog(self.backend, self)
        if dialog.exec():
            self.on_show()

    @pyqtSlot()
    def show_report(self):
        try:
            summary = self.backend.sales_summary()
            best = self.backend.best_sellers(5)
        except POSError as e:
            show_error(self, e)
            return

        lines = [
            f"Sales report for {summary['date']}",
            "=" * 36,
            f"Transactions : {summary['transactions']}  (voided: {summary['voided']})",
            f"Gross sales  : {peso(summary['gross_sales'])}",
            f"Discounts    : {peso(summary['discounts'])}",
            f"VAT included : {peso(summary['vat'])}",
            f"Net sales    : {peso(summary['net_sales'])}",
        ]
        if best:
            lines += ["", "Best sellers:"]
            for number, b in enumerate(best, start=1):
                lines.append(f"{number}. {b['name']}  x{b['quantity']}")
        TextDialog("Sales Report", "\n".join(lines), self).exec()

    @pyqtSlot()
    def change_password(self):
        old, ok = QInputDialog.getText(self, "Change Password", "Current password:",
                                       QLineEdit.EchoMode.Password)
        if not ok:
            return
        new, ok = QInputDialog.getText(self, "Change Password", "New password:",
                                       QLineEdit.EchoMode.Password)
        if not ok:
            return
        try:
            self.backend.change_password(old, new)
        except POSError as e:
            show_error(self, e)
            return
        show_info(self, "Done", "Password changed.")

    @pyqtSlot()
    def do_logout(self):
        txn = self.backend.transaction
        if txn is not None and txn.lines:
            answer = QMessageBox.question(self, "Logout",
                                          "There are still items in the cart. Logout anyway?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.logged_out.emit()


class CheckoutPage(QWidget):
    back_to_store = pyqtSignal()
    sale_done = pyqtSignal()

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        title = QLabel("Checkout")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.lbl_txn = QLabel("")
        self.lbl_txn.setStyleSheet("color: #6C757D;")
        main_layout.addWidget(title)
        main_layout.addWidget(self.lbl_txn)

        body = QHBoxLayout()
        body.setSpacing(15)

        self.tbl_items = QTableWidget(0, 4)
        self.tbl_items.setHorizontalHeaderLabels(["Item", "Qty", "Unit Price", "Total"])
        self.tbl_items.verticalHeader().setVisible(False)
        self.tbl_items.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self.tbl_items.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        body.addWidget(self.tbl_items, 3)

        side = QFrame()
        side.setObjectName("sidePanel")
        side.setFixedWidth(380)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(15, 15, 15, 15)
        side_layout.setSpacing(8)

        lbl_customer = QLabel("Customer Type")
        lbl_customer.setStyleSheet("font-weight: 600; border: none;")
        self.cmb_customer = QComboBox()
        for text, kind in CUSTOMER_TYPES:
            self.cmb_customer.addItem(text, kind)
        self.cmb_customer.currentIndexChanged.connect(self.apply_customer_type)

        lbl_promo = QLabel("Promo")
        lbl_promo.setStyleSheet("font-weight: 600; border: none;")
        self.cmb_promo = QComboBox()
        self.cmb_promo.currentIndexChanged.connect(self.apply_customer_type)

        side_layout.addWidget(lbl_customer)
        side_layout.addWidget(self.cmb_customer)
        side_layout.addWidget(lbl_promo)
        side_layout.addWidget(self.cmb_promo)
        side_layout.addSpacing(6)

        self.lbl_subtotal = self.add_total_row(side_layout, "Subtotal")
        self.lbl_discount = self.add_total_row(side_layout, "Discount")
        self.lbl_vat = self.add_total_row(side_layout, "VAT (12% included)")
        self.lbl_total = self.add_total_row(side_layout, "TOTAL", big=True)
        side_layout.addSpacing(6)

        lbl_payment = QLabel("Payment (₱)")
        lbl_payment.setStyleSheet("font-weight: 600; border: none;")
        self.txt_payment = QLineEdit()
        self.txt_payment.setPlaceholderText("Enter the amount given")
        self.txt_payment.setMinimumHeight(36)
        self.txt_payment.textChanged.connect(self.update_change)
        self.txt_payment.returnPressed.connect(self.do_pay)

        btn_exact = QPushButton("Exact amount")
        btn_exact.clicked.connect(self.fill_exact)
        pay_row = QHBoxLayout()
        pay_row.addWidget(self.txt_payment)
        pay_row.addWidget(btn_exact)

        self.lbl_change = QLabel("Change: -")
        self.lbl_change.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_change.setStyleSheet("color: #71A02B; border: none;")

        side_layout.addWidget(lbl_payment)
        side_layout.addLayout(pay_row)
        side_layout.addWidget(self.lbl_change)
        side_layout.addStretch()

        btn_pay = QPushButton("Pay and Print Receipt")
        btn_pay.setObjectName("primary")
        btn_pay.setMinimumHeight(44)
        btn_pay.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pay.clicked.connect(self.do_pay)

        btn_back = QPushButton("Back to Store")
        btn_back.clicked.connect(self.back_to_store.emit)
        btn_cancel = QPushButton("Cancel Sale")
        btn_cancel.setObjectName("danger")
        btn_cancel.clicked.connect(self.cancel_sale)
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(btn_back)
        bottom_row.addWidget(btn_cancel)

        side_layout.addWidget(btn_pay)
        side_layout.addLayout(bottom_row)

        body.addWidget(side)
        main_layout.addLayout(body)

    def add_total_row(self, layout, text, big=False):
        row = QHBoxLayout()
        lbl = QLabel(text)
        value = QLabel("₱0.00")
        value.setAlignment(Qt.AlignmentFlag.AlignRight)
        size = 15 if big else 11
        weight = QFont.Weight.Bold if big else QFont.Weight.Normal
        lbl.setFont(QFont("Segoe UI", size, weight))
        value.setFont(QFont("Segoe UI", size, weight))
        lbl.setStyleSheet("border: none; color: #212529;")
        value.setStyleSheet("border: none; color: #71A02B;" if big else "border: none; color: #212529;")
        row.addWidget(lbl)
        row.addWidget(value)
        layout.addLayout(row)
        return value

    def on_show(self):
        self.lbl_txn.setText(f"Transaction No: {self.backend.transaction.transaction_id}")

        self.cmb_promo.blockSignals(True)
        self.cmb_promo.clear()
        self.cmb_promo.addItems(self.backend.promo_names())
        self.cmb_promo.blockSignals(False)

        self.cmb_customer.blockSignals(True)
        self.cmb_customer.setCurrentIndex(0)
        self.cmb_customer.blockSignals(False)
        self.backend.set_customer_type("regular")
        self.cmb_promo.setEnabled(False)

        self.txt_payment.blockSignals(True)
        self.txt_payment.clear()
        self.txt_payment.blockSignals(False)

        self.load_items()
        self.update_totals()
        self.txt_payment.setFocus()

    def load_items(self):
        lines = self.backend.cart_lines()
        self.tbl_items.setRowCount(len(lines))
        for row, line in enumerate(lines):
            cells = [line["name"], str(line["quantity"]),
                     peso(line["unit_price"]), peso(line["line_total"])]
            for col, text in enumerate(cells):
                cell = QTableWidgetItem(text)
                if col > 0:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tbl_items.setItem(row, col, cell)

    def apply_customer_type(self, *args):
        kind = self.cmb_customer.currentData()
        self.cmb_promo.setEnabled(kind == "promo")
        promo_name = self.cmb_promo.currentText() if kind == "promo" else None

        try:
            self.backend.set_customer_type(kind, promo_name)
        except POSError as e:
            show_error(self, e)
            self.cmb_customer.blockSignals(True)
            self.cmb_customer.setCurrentIndex(0)
            self.cmb_customer.blockSignals(False)
            self.cmb_promo.setEnabled(False)
            self.backend.set_customer_type("regular")
        self.update_totals()

    def update_totals(self):
        totals = self.backend.totals()
        self.lbl_subtotal.setText(peso(totals["subtotal"]))
        self.lbl_discount.setText(f"-{peso(totals['discount'])}")
        self.lbl_vat.setText(peso(totals["vat"]))
        self.lbl_total.setText(peso(totals["total"]))
        self.update_change()

    def fill_exact(self):
        self.txt_payment.setText(f"{self.backend.totals()['total']:.2f}")

    def update_change(self, *args):
        text = self.txt_payment.text().strip()
        if not text:
            self.lbl_change.setText("Change: -")
            return
        try:
            paid = money(text)
            total = self.backend.totals()["total"]
            if paid < total:
                self.lbl_change.setText(f"Short by {peso(total - paid)}")
            else:
                self.lbl_change.setText(f"Change: {peso(self.backend.change_for(text))}")
        except POSError:
            self.lbl_change.setText("Change: -")

    @pyqtSlot()
    def do_pay(self):
        try:
            receipt = self.backend.checkout(self.txt_payment.text())
        except POSError as e:
            show_error(self, e)
            return

        TextDialog("Receipt", receipt, self).exec()

        try:
            self.backend.start_transaction()
        except POSError as e:
            show_error(self, e)
        self.sale_done.emit()

    @pyqtSlot()
    def cancel_sale(self):
        answer = QMessageBox.question(self, "Cancel sale", "Cancel this whole sale?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.backend.cancel_transaction()
        try:
            self.backend.start_transaction()
        except POSError as e:
            show_error(self, e)
        self.sale_done.emit()


class MainWindow(QMainWindow):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.warnings_shown = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"{STORE_NAME} - Point of Sales")
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pythonico.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1300, 800)
        self.setMinimumSize(1100, 720)
        self.center_window()

        self.stack = QStackedWidget()
        self.login_page = LoginPage(self.backend)
        self.register_page = RegistrationWindow(self.backend)
        self.store_page = StorePage(self.backend)
        self.checkout_page = CheckoutPage(self.backend)
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.register_page)
        self.stack.addWidget(self.store_page)
        self.stack.addWidget(self.checkout_page)
        self.setCentralWidget(self.stack)

        self.login_page.logged_in.connect(self.after_login)
        self.login_page.go_register.connect(self.show_register)
        self.register_page.back_to_login.connect(self.show_login)
        self.register_page.account_created.connect(self.after_register)
        self.store_page.go_checkout.connect(self.show_checkout)
        self.store_page.logged_out.connect(self.do_logout)
        self.checkout_page.back_to_store.connect(self.show_store)
        self.checkout_page.sale_done.connect(self.show_store)

        self.stack.setCurrentWidget(self.login_page)

    def center_window(self):
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def after_login(self):
        try:
            self.backend.start_transaction()
        except POSError as e:
            show_error(self, e)
            self.backend.logout()
            return
        self.show_store()

        user = self.backend.current_user
        if user.can("manage_users") and not self.warnings_shown:
            self.warnings_shown = True
            if self.backend.load_warnings:
                show_info(self, "Notice", "\n\n".join(self.backend.load_warnings))

    def show_store(self):
        self.store_page.on_show()
        self.stack.setCurrentWidget(self.store_page)

    def show_checkout(self):
        self.checkout_page.on_show()
        self.stack.setCurrentWidget(self.checkout_page)

    def show_login(self):
        self.stack.setCurrentWidget(self.login_page)

    def show_register(self):
        self.register_page.on_show()
        self.stack.setCurrentWidget(self.register_page)

    def after_register(self, username):
        self.login_page.txt_user.setText(username)
        self.show_login()
        self.login_page.txt_pass.setFocus()

    def do_logout(self):
        self.backend.logout()
        self.show_login()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)
    app.setFont(QFont("Segoe UI", 10))

    try:
        backend = POSBackend()
    except POSError as e:
        QMessageBox.critical(None, "Cannot start", str(e))
        sys.exit(1)

    window = MainWindow(backend)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()