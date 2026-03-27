__author__ = "Yuval Malkan"

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from uiConstants import *
from uiElements import Card, AuthInput, StandardAuthButton, LinkButton
from signUp import SignupForm


# ──────────────────────────────────────────
#  LOGIN FORM
# ──────────────────────────────────────────
class LoginForm(QWidget):
    def __init__(self, switch_callback, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        self.user_input = AuthInput("Agent ID / Username")
        self.pass_input = AuthInput("Passcode", is_password=True)

        self.login_btn = StandardAuthButton("INITIALIZE SECURE SESSION")
        self.switch_btn = LinkButton("Request Access Clearance (Sign Up)")
        self.switch_btn.clicked.connect(switch_callback)

        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_input)
        layout.addSpacing(10)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.switch_btn)


# ──────────────────────────────────────────
#  START PAGE MAIN WINDOW
# ──────────────────────────────────────────
class StartPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Neuron - Auth")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 780)

        self._build_layout()

    def _build_layout(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.auth_card = Card()
        self.auth_card.setFixedSize(400, 450)

        card_layout = QVBoxLayout(self.auth_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        welcome_lbl = QLabel("PROJECT NEURON")
        welcome_lbl.setFont(QFont(FONT_TITLE, 18, QFont.Weight.Bold))
        welcome_lbl.setStyleSheet(f"color: {TEXT_TITLE};")
        welcome_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub_lbl = QLabel("RESTRICTED ACCESS")
        sub_lbl.setFont(QFont(FONT_MONO, 10))
        sub_lbl.setStyleSheet("color: #EF233C; letter-spacing: 2px;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(welcome_lbl)
        card_layout.addWidget(sub_lbl)
        card_layout.addSpacing(10)

        self.stacked_forms = QStackedWidget()
        self.login_form = LoginForm(self.show_signup)
        self.signup_form = SignupForm(self.show_login)

        self.stacked_forms.addWidget(self.login_form)
        self.stacked_forms.addWidget(self.signup_form)

        card_layout.addWidget(self.stacked_forms)
        main_layout.addWidget(self.auth_card)

    def show_signup(self):
        self.stacked_forms.setCurrentIndex(1)
        self.auth_card.setFixedSize(400, 520)

    def show_login(self):
        self.stacked_forms.setCurrentIndex(0)
        self.auth_card.setFixedSize(400, 450)





if __name__ == "__main__":
    app = QApplication(sys.argv)


    app.setStyleSheet(load_stylesheet("loginSignup"))

    window = StartPage()
    window.show()
    sys.exit(app.exec())