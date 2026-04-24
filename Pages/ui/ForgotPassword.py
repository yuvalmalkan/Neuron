__author__ = "Yuval Malkan"

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from Pages.ui.uiElements import GlowInput, GlowingButton
import logging
import pickle
from Constants import *
from UserDatabase import UserDatabase



class ForgotPasswordForm(QWidget):
    #todo write forgot password form, with a 5 minute code sent to email and input field to enter code and new password
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)


        self.email_input = GlowInput("Email Address")

        self.sendOTP_btn = GlowingButton("SEND VERIFICATION CODE", "primary")

        self.switch_btn = GlowingButton("SWITCH BACK TO LOGIN", "danger")

        self.switch_btn.clicked.connect(lambda: self.window().show_login())
        self.sendOTP_btn.clicked.connect(lambda: SendOTP(self))



        layout.addWidget(self.email_input)
        layout.addSpacing(30)
        layout.addWidget(self.sendOTP_btn)
        layout.addStretch()

        layout.addWidget(self.switch_btn)


        #todo make it so when the send code is clicked a text will appear saying "Verification code sent to email" and then show the input fields for the code and new password, and a button to submit the new password




def SendOTP(form: ForgotPasswordForm):
    """Handle send OTP button click."""
    from PyQt6.QtWidgets import QMessageBox

    logging.debug("sendOTP clicked")
    email = form.email_input.text().strip()

    if not email:
        QMessageBox.warning(None, "Validation Error", "Please enter an email address")
        return

    try:

        from Constants import user_db

        isExist = user_db.is_email_exists(email)

        if isExist:
            logging.debug(f"User exists: {email}")
            QMessageBox.information(None, "Success", f"Verification code sent to {email}")
        else:
            logging.warning(f"User does not exist: {email}")
            QMessageBox.critical(None, "Error", "Email not found in database")

    except Exception as e:
        logging.error(f"Error checking email: {e}")
        QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")


"""
def IsUserExistByEmail(email):
#
    if user_db.get_user_by_email(email):  # User exists
        return True  
    else:
        return False 

"""