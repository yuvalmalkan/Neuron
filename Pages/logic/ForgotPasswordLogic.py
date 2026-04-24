__author__ = "Yuval Malkan"

import logging


def ForgotPasswordClicked(form):
    """Handle forgot password button click."""
    logging.debug("Forgot password clicked")

    login_window = form.window()
    login_window.show_forgot_password()



def HandleForgotPassword(form):
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
            #todo send otp to email


        else:
            logging.warning(f"User does not exist: {email}")
            QMessageBox.critical(None, "Error", "Email not found in database")



    except Exception as e:
        logging.error(f"Error checking email: {e}")
        QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")




def SendOTP(form):
    """Send OTP button click."""
    pass