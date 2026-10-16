
import sys
import os
import csv
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox,
    QVBoxLayout, QHBoxLayout, QFormLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QIcon, QFont, QGuiApplication, QMovie, QColor
from PyQt6.QtCore import pyqtSlot, Qt


class RegistrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.title = "Group 1 - Account Registration"
        self.width = 620
        self.height = 760
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, 'pythonico.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(self.width, self.height)
        self.center_window()

        # ---------- Overall window background ----------
        self.setObjectName("root")
        self.setStyleSheet("""
            QWidget#root {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6C63FF, stop:1 #3B8BEB
                );
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(30, 30, 30, 30)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ---------- Card container ----------
        card = QFrame(self)
        card.setObjectName("card")
        card.setFixedWidth(520)
        card.setStyleSheet("""
            QFrame#card {
                background-color: #FFFFFF;
                border: 2px solid #E0E4F0;
                border-radius: 18px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(35)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 90))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 30, 35, 30)
        card_layout.setSpacing(14)

        # ---------- Accent strip ----------
        accent_strip = QFrame()
        accent_strip.setFixedHeight(6)
        accent_strip.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #6C63FF, stop:1 #3B8BEB
            );
            border-radius: 3px;
            border: none;
        """)
        card_layout.addWidget(accent_strip)
        card_layout.addSpacing(4)

        # ---------- Title ----------
        title_label = QLabel("Account Registration")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont('Segoe UI', 22)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2E3A59; border: none;")

        subtitle_label = QLabel("Create your account to get started")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont('Segoe UI', 10))
        subtitle_label.setStyleSheet("color: #8A93A6; border: none;")

        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle_label)

        # ---------- GIF / Avatar area ----------
        self.gif_label = QLabel()
        self.gif_label.setFixedSize(140, 140)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setScaledContents(True)

        gif_path = r"NONE"
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.gif_label.setMovie(self.movie)
            self.movie.start()
            self.gif_label.setStyleSheet("border: none;")
        else:
            # Nice fallback avatar circle if the gif isn't available
            self.gif_label.setText("New\nAccount")
            self.gif_label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
            self.gif_label.setStyleSheet("""
                background-color: #EEF1FB;
                color: #6C63FF;
                border-radius: 70px;
                border: 3px solid #D9DEF7;
            """)

        avatar_row = QHBoxLayout()
        avatar_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_row.addWidget(self.gif_label)
        card_layout.addLayout(avatar_row)
        card_layout.addSpacing(10)

        # ---------- Form ----------
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        label_style = "color: #3A4256; font-weight: 600; border: none;"
        input_style = """
            QLineEdit {
                border: 2px solid #DDE3F0;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                color: #2E3A59;
                background-color: #FAFBFF;
            }
            QLineEdit:focus {
                border: 2px solid #6C63FF;
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
                color: #6C63FF;
                padding: 0px;
            }
            QPushButton:hover {
                color: #463CC9;
            }
        """

        self.inputs = {}
        for label_text, field_name, is_password, placeholder in fields:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setFont(QFont('Segoe UI', 10))

            txt = QLineEdit()
            txt.setMinimumHeight(34)
            txt.setPlaceholderText(placeholder)
            txt.setStyleSheet(input_style)

            if is_password:
                txt.setEchoMode(QLineEdit.EchoMode.Password)
                # Show/hide password toggle sitting inside the field row
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
        card_layout.addSpacing(10)

        # ---------- Buttons ----------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)

        self.btn_submit = QPushButton("Submit")
        self.btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_submit.setMinimumHeight(40)
        self.btn_submit.setStyleSheet("""
            QPushButton {
                background-color: #6C63FF;
                color: white;
                font-weight: 600;
                font-size: 13px;
                border-radius: 10px;
                border: none;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #574FDB;
            }
            QPushButton:pressed {
                background-color: #463CC9;
            }
        """)
        self.btn_submit.clicked.connect(self.submit_form)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setMinimumHeight(40)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #6C63FF;
                font-weight: 600;
                font-size: 13px;
                border-radius: 10px;
                border: 2px solid #6C63FF;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #F1F0FF;
            }
            QPushButton:pressed {
                background-color: #E4E2FF;
            }
        """)
        self.btn_clear.clicked.connect(self.clear_form)

        btn_row.addWidget(self.btn_clear)
        btn_row.addWidget(self.btn_submit)
        card_layout.addLayout(btn_row)

        # ---------- Footer note ----------
        footer_label = QLabel("Your information is stored locally and kept private")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setFont(QFont('Segoe UI', 8))
        footer_label.setStyleSheet("color: #A6ACC0; border: none;")
        card_layout.addSpacing(4)
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
                color: #2E3A59;
                font-size: 13px;
            }
            QPushButton {
                background-color: #6C63FF;
                color: white;
                font-weight: 600;
                border-radius: 8px;
                border: none;
                padding: 6px 18px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #574FDB;
            }
        """)
        return box

    def center_window(self):
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width) // 2
        y = (screen.height() - self.height) // 2
        self.move(x, y)

    @pyqtSlot()
    def submit_form(self):
        data = {}
        empty_fields = []

        for field_name, input_widget in self.inputs.items():
            val = input_widget.text().strip()
            data[field_name] = val
            if not val:
                empty_fields.append(field_name)

        if empty_fields:
            box = self.styled_message_box(
                QMessageBox.Icon.Warning,
                "Missing Information",
                "All fields are required! Please fill in all empty fields before submitting."
            )
            box.exec()
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'accounts.csv')

        try:
            file_exists = os.path.isfile(file_path)
            with open(file_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow([
                        "First Name", "Last Name", "Username",
                        "Password", "Email", "Contact"
                    ])

                role = "Manager" if "mgr" in data ['txt_username'].lower() or "admin" in data['txt_username'].lower() else "Cashier"
                
                writer.writerow([
                    data['txt_first_name'],
                    data['txt_last_name'],
                    data['txt_username'],
                    data['txt_password'],
                    data['txt_email'],
                    data['txt_contact']
                ])

            box = self.styled_message_box(
                QMessageBox.Icon.Information,
                "Success",
                "Account registered and saved successfully!"
            )
            box.exec()
            self.clear_form()

        except Exception as e:
            box = self.styled_message_box(
                QMessageBox.Icon.Critical,
                "Database Error",
                f"Failed to save account record: {str(e)}"
            )
            box.exec()

    @pyqtSlot()
    def clear_form(self):
        for txt in self.inputs.values():
            txt.clear()
