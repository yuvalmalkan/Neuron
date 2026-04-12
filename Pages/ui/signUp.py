__author__ = "Yuval Malkan"



from PyQt6.QtWidgets import *
from Pages.ui.uiElements import *




class SignupForm(QWidget):
    def __init__(self, switch_callback, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        self.user_input = GlowInput("Username")
        self.email_address = GlowInput("Email Address")

        self.pass_input = GlowInput("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.pass_confirm = GlowInput("Confirm Password")
        self.pass_confirm.setEchoMode(QLineEdit.EchoMode.Password)

        self.signup_btn = GlowingButton("SIGN UP", "primary")
        self.switch_btn = GlowingButton("RETURN TO LOGIN", "danger")
        self.switch_btn.clicked.connect(switch_callback)

        layout.addWidget(self.user_input)
        layout.addWidget(self.email_address)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.pass_confirm)
        layout.addSpacing(10)
        layout.addWidget(self.signup_btn)
        layout.addWidget(self.switch_btn)



def SignupClicked():
    QMessageBox.information(None, "", "Signup clicked")