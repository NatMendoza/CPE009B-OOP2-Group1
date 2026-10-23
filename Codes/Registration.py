import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox, QDialog,
    QVBoxLayout, QHBoxLayout, QFormLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QFont, QMovie, QColor
from PyQt6.QtCore import pyqtSlot, pyqtSignal, Qt

from errors import POSError


class AdminApprovalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Approval")
        self.setMinimumWidth(380)

        note = QLabel("Only an admin can create accounts.\nPlease enter the admin login.")
        note.setStyleSheet("color: #6C757D;")

        form = QFormLayout()
        self.txt_admin_user = QLineEdit()
        self.txt_admin_user.setPlaceholderText("Admin username")
        self.txt_admin_pass = QLineEdit()
        self.txt_admin_pass.setPlaceholderText("Admin password")
        self.txt_admin_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_admin_pass.returnPressed.connect(self.check_and_accept)
        self.cmb_role = QComboBox()
        self.cmb_role.addItems(["Cashier", "Manager", "Admin"])
        form.addRow("Admin Username:", self.txt_admin_user)
        form.addRow("Admin Password:", self.txt_admin_pass)
        form.addRow("Role of new account:", self.cmb_role)

        btn_approve = QPushButton("Approve")
        btn_approve.setObjectName("primary")
        btn_approve.clicked.connect(self.check_and_accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_approve)

        layout = QVBoxLayout(self)
        layout.addWidget(note)
        layout.addLayout(form)
        layout.addLayout(btn_row)

    def check_and_accept(self):
        if not self.admin_user() or not self.admin_pass():
            QMessageBox.warning(self, "Missing Information",
                                "Please enter the admin username and password.")
            return
        self.accept()

    def admin_user(self):
        return self.txt_admin_user.text().strip()

    def admin_pass(self):
        return self.txt_admin_pass.text()

    def role(self):
        return self.cmb_role.currentText().lower()


class RegistrationWindow(QWidget):
    account_created = pyqtSignal(str)
    back_to_login = pyqtSignal()

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.initUI()

    def initUI(self):
        self.setObjectName("root")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget#root {
                background-color: #1A1A1A;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame(self)
        card.setObjectName("card")
        card.setFixedWidth(500)
        card.setStyleSheet("""
            QFrame#card {
                background-color: #FFFFFF;
                border: 1.5px solid #CED4DA;
                border-radius: 14px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 25, 30, 25)
        card_layout.setSpacing(12)

        accent_strip = QFrame()
        accent_strip.setFixedHeight(5)
        accent_strip.setStyleSheet("""
            background: #71A02B;
            border-radius: 2px;
            border: none;
        """)
        card_layout.addWidget(accent_strip)
        card_layout.addSpacing(2)

        title_label = QLabel("Account Registration")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont('Segoe UI', 20)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #111111; border: none;")

        subtitle_label = QLabel("Create your account to get started")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont('Segoe UI', 10))
        subtitle_label.setStyleSheet("color: #71A02B; font-weight: 600; border: none;")

        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle_label)

        self.gif_label = QLabel()
        self.gif_label.setFixedSize(100, 100)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setScaledContents(True)

        gif_path = r"NONE"
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.gif_label.setMovie(self.movie)
            self.movie.start()
            self.gif_label.setStyleSheet("border: none;")
        else:
            self.gif_label.setText("New\nAccount")
            self.gif_label.setFont(QFont('Segoe UI', 13, QFont.Weight.Bold))
            self.gif_label.setStyleSheet("""
                background-color: #F1F3F5;
                color: #71A02B;
                border-radius: 50px;
                border: 2px solid #71A02B;
            """)

        avatar_row = QHBoxLayout()
        avatar_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_row.addWidget(self.gif_label)
        card_layout.addLayout(avatar_row)
        card_layout.addSpacing(6)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        label_style = "color: #343A40; font-weight: 600; border: none;"
        input_style = """
            QLineEdit {
                border: 1.5px solid #CED4DA;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
                color: #111111;
                background-color: #FAFAFA;
            }
            QLineEdit:focus {
                border: 1.5px solid #71A02B;
                background-color: #FFFFFF;
            }
        """

        fields = [
            ("First Name:", "txt_first_name", False, "Enter your first name"),
            ("Last Name:", "txt_last_name", False, "Enter your last name"),
            ("Username:", "txt_username", False, "Choose a username"),
            ("Password:", "txt_password", True, "Choose a password"),
            ("Email Address:", "txt_email", False, "you@example.com"),
            ("Contact Number:", "txt_contact", False, "e.g. 09XXXXXXXXX")
        ]

        toggle_btn_style = """
            QPushButton {
                border: none;
                background: transparent;
                font-size: 11px;
                font-weight: 600;
                color: #71A02B;
                padding: 0px;
            }
            QPushButton:hover {
                color: #5F8A22;
            }
        """

        self.inputs = {}
        for label_text, field_name, is_password, placeholder in fields:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setFont(QFont('Segoe UI', 10))

            txt = QLineEdit()
            txt.setMinimumHeight(32)
            txt.setPlaceholderText(placeholder)
            txt.setStyleSheet(input_style)

            if is_password:
                txt.setEchoMode(QLineEdit.EchoMode.Password)
                field_row = QHBoxLayout()
                field_row.setContentsMargins(0, 0, 0, 0)
                field_row.setSpacing(0)

                toggle_btn = QPushButton("Show")
                toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                toggle_btn.setFixedWidth(45)
                toggle_btn.setStyleSheet(toggle_btn_style)

                def make_toggle(line_edit, button):
                    def toggle():
                        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
                            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
                            button.setText("Hide")
                        else:
                            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
                            button.setText("Show")
                    return toggle

                toggle_btn.clicked.connect(make_toggle(txt, toggle_btn))

                field_row.addWidget(txt)
                field_row.addWidget(toggle_btn)
                self.inputs[field_name] = txt
                form_layout.addRow(lbl, field_row)
            else:
                self.inputs[field_name] = txt
                form_layout.addRow(lbl, txt)

        card_layout.addLayout(form_layout)
        card_layout.addSpacing(6)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_submit = QPushButton("Submit")
        self.btn_submit.setObjectName("primary")
        self.btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_submit.setMinimumHeight(38)
        self.btn_submit.clicked.connect(self.submit_form)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setMinimumHeight(38)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #212529;
                font-weight: 600;
                font-size: 13px;
                border-radius: 8px;
                border: 1.5px solid #CED4DA;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #F1F3F5;
                border-color: #71A02B;
                color: #71A02B;
            }
        """)
        self.btn_clear.clicked.connect(self.clear_form)

        btn_row.addWidget(self.btn_clear)
        btn_row.addWidget(self.btn_submit)
        card_layout.addLayout(btn_row)

        self.btn_back = QPushButton("Already have an account? Back to Login")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #71A02B;
                font-size: 12px;
                font-weight: 600;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #5F8A22;
            }
        """)
        self.btn_back.clicked.connect(self.back_to_login.emit)
        card_layout.addWidget(self.btn_back)

        footer_label = QLabel("Your information is stored locally and kept private")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setFont(QFont('Segoe UI', 8))
        footer_label.setStyleSheet("color: #ADB5BD; border: none;")
        card_layout.addWidget(footer_label)

        outer_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    @staticmethod
    def styled_message_box(icon, title, text):
        box = QMessageBox()
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setStyleSheet("""
            QMessageBox {
                background-color: #FFFFFF;
            }
            QMessageBox QLabel {
                color: #111111;
                font-size: 13px;
            }
            QPushButton {
                background-color: #71A02B;
                color: white;
                font-weight: 600;
                border-radius: 6px;
                border: none;
                padding: 6px 16px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #5F8A22;
            }
        """)
        box.exec()

    def on_show(self):
        self.clear_form()

    @pyqtSlot()
    def submit_form(self):
        data = {}
        empty_fields = []

        for field_name, input_widget in self.inputs.items():
            if field_name == "txt_password":
                val = input_widget.text()
            else:
                val = input_widget.text().strip()
            data[field_name] = val
            if not val:
                empty_fields.append(field_name)

        if empty_fields:
            self.styled_message_box(
                QMessageBox.Icon.Warning,
                "Missing Information",
                "All fields are required! Please fill in all empty fields before submitting."
            )
            return

        approval = AdminApprovalDialog(self)
        if not approval.exec():
            return

        full_name = f"{data['txt_first_name']} {data['txt_last_name']}"

        try:
            self.backend.login(approval.admin_user(), approval.admin_pass())
            self.backend.create_user(
                data['txt_username'],
                data['txt_password'],
                approval.role(),
                full_name,
                data['txt_email'],
                data['txt_contact']
            )
        except POSError as e:
            self.styled_message_box(
                QMessageBox.Icon.Warning,
                "Could not create account",
                str(e)
            )
            return
        finally:
            self.backend.logout()

        self.styled_message_box(
            QMessageBox.Icon.Information,
            "Success",
            "Account registered and saved successfully!"
        )
        username = data['txt_username']
        self.clear_form()
        self.account_created.emit(username)

    @pyqtSlot()
    def clear_form(self):
        for txt in self.inputs.values():
            txt.clear()