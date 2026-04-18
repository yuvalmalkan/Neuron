__author__ = "Yuval Malkan"

import logging
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
    Handle signup button click event.
    Validates credentials and creates new user account.

    Args:
        form: SignupForm instance to access input fields
    """
    from Pages.logic.SignupLogic import handle_signup, validate_password
    from UserDatabase import UserDatabase
    from Constants import (
        RESP_SIGNUP_OK, RESP_SIGNUP_USER_EXISTS, RESP_SIGNUP_EMAIL_EXISTS,
        RESP_SIGNUP_INVALID_USERNAME, RESP_SIGNUP_INVALID_EMAIL, RESP_SIGNUP_INVALID_PASSWORD
    )

    # Get values from input fields
    username = form.user_input.text().strip()
    email = form.email_address.text().strip()
    password = form.pass_input.text()
    password_confirm = form.pass_confirm.text()

    logging.debug(f"Signup clicked for username: {username}, email: {email}")

    # Validate input fields are not empty
    if not username or not email or not password or not password_confirm:
        logging.warning("Signup attempt with empty credentials")
        QMessageBox.warning(None, "Validation Error", "Please fill in all fields")
        return

    # Validate passwords match
    if password != password_confirm:
        logging.warning(f"Signup failed: passwords do not match for {username}")
        QMessageBox.warning(None, "Validation Error", "Passwords do not match")
        form.pass_input.clear()
        form.pass_confirm.clear()
        return

    try:
        # Initialize database connection
        db = UserDatabase()

        # Call signup handler
        success, response_code, user = handle_signup(username, email, password, db)

        if success:
            logging.info(f"User {username} signed up successfully")
            QMessageBox.information(None, "Success", f"Welcome to Neuron, {username}!\nPlease log in with your credentials.")
            # Clear all fields on successful signup
            form.user_input.clear()
            form.email_address.clear()
            form.pass_input.clear()
            form.pass_confirm.clear()
            # TODO: Navigate back to login form
        else:
            # Provide specific error messages based on response code using constants
            if response_code == RESP_SIGNUP_USER_EXISTS:
                error_msg = "Username already exists. Please choose a different one."
                logging.warning(f"Signup failed: {error_msg}")
            elif response_code == RESP_SIGNUP_EMAIL_EXISTS:
                error_msg = "Email address already registered. Please use a different email or log in."
                logging.warning(f"Signup failed: {error_msg}")
            elif response_code == RESP_SIGNUP_INVALID_USERNAME:
                error_msg = "Invalid username format. Username must be 3-20 characters and contain only letters, numbers, and underscores."
                logging.warning(f"Signup failed: {error_msg}")
            elif response_code == RESP_SIGNUP_INVALID_EMAIL:
                error_msg = "Invalid email address format. Please enter a valid email."
                logging.warning(f"Signup failed: {error_msg}")
            elif response_code == RESP_SIGNUP_INVALID_PASSWORD:
                error_msg = "Password must be:\n- At least 8 characters long\n- Contain uppercase and lowercase letters\n- Contain at least one digit"
                logging.warning(f"Signup failed: {error_msg}")
            else:
                error_msg = "Signup failed. Please try again."
                logging.error(f"Signup failed with response code: {response_code}")

            QMessageBox.critical(None, "Signup Failed", error_msg)
            # Clear sensitive fields on failed signup
            form.pass_input.clear()
            form.pass_confirm.clear()

    except Exception as e:
        logging.error(f"Unexpected error during signup: {e}")
        QMessageBox.critical(None, "Error", f"An unexpected error occurred: {str(e)}")
