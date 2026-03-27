__author__ = "Yuval Malkan"

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from uiElements import AuthInput, StandardAuthButton, LinkButton


class SignupForm(QWidget):
    def __init__(self, switch_callback, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        self.user_input = AuthInput("Desired Username")
        self.badge_input = AuthInput("Organization Badge Number")
        self.pass_input = AuthInput("Passcode", is_password=True)
        self.pass_confirm = AuthInput("Confirm Passcode", is_password=True)

        self.signup_btn = StandardAuthButton("SUBMIT CLEARANCE REQUEST")
        self.switch_btn = LinkButton("Return to Secure Login")
        self.switch_btn.clicked.connect(switch_callback)

        layout.addWidget(self.user_input)
        layout.addWidget(self.badge_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.pass_confirm)
        layout.addSpacing(10)
        layout.addWidget(self.signup_btn)
        layout.addWidget(self.switch_btn)