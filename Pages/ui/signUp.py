__author__ = "Yuval Malkan"

import logging
from PyQt6.QtWidgets import *
from Pages.ui.uiElements import *
#from Pages.ui.Login import Login
import SessionManager



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
        # Pass the form as context so SignupClicked can access input fields
        self.signup_btn.clicked.connect(lambda: SignupClicked(self))

        layout.addWidget(self.user_input)
        layout.addWidget(self.email_address)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.pass_confirm)
        layout.addSpacing(10)
        layout.addWidget(self.signup_btn)
        layout.addWidget(self.switch_btn)


def SignupClicked(form: SignupForm):
    """
    Handle signup button click event - SENDS TO SERVER.

    Args:
        form: SignupForm instance to access input fields
    """
    from Pages.logic.SignupLogic import validate_password
    from Constants import RESP_SIGNUP_USER_EXISTS, RESP_SIGNUP_EMAIL_EXISTS
    import Client

    username = form.user_input.text().strip()
    email = form.email_address.text().strip()
    password = form.pass_input.text()
    password_confirm = form.pass_confirm.text()

    # Validation
    if not all([username, email, password, password_confirm]):
        QMessageBox.warning(None, "Validation Error", "Please fill in all fields")
        return

    if password != password_confirm:
        QMessageBox.warning(None, "Validation Error", "Passwords do not match")
        form.pass_input.clear()
        form.pass_confirm.clear()
        return

    if not validate_password(password):
        QMessageBox.warning(None, "Validation Error", "Password must be at least 8 characters")
        return

    try:
        # Connect to server if not already connected
        if not Client.is_connected():
            if not Client.connect_to_server():
                QMessageBox.critical(None, "Connection Error", "Could not connect to server. Is it running?")
                return

        # Send signup request to server
        response = Client.signup(username, email, password)

        # Check response
        if response.get('status') == 'success':
            logging.info(f"User {username} signed up successfully")

            # Store session for auto-login
            SessionManager.set_session(
                response.get('user_id'),
                response.get('username'),
                response.get('email')
            )

            QMessageBox.information(None, "Success", "Account created! Please log in.")
            # Switch back to login form
            form.window().show_login()


        else:
            response_code = response.get('code')

            if response_code == RESP_SIGNUP_USER_EXISTS:
                error_msg = "Username already exists"
            elif response_code == RESP_SIGNUP_EMAIL_EXISTS:
                error_msg = "Email already registered"
            else:
                error_msg = response.get('message', 'Signup failed. Please try again.')

            QMessageBox.critical(None, "Signup Failed", error_msg)

    except Exception as e:
        logging.error(f"Unexpected error during signup: {e}")
        QMessageBox.critical(None, "Error", f"An unexpected error occurred: {str(e)}")

