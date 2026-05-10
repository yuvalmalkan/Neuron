__author__ = "Yuval Malkan"

import logging
from MalkanMail import *
import random
import time
from Constants import RESP_ERROR, RESP_VERIFY_OK


pendingUsers = {}
forgot_pending = {}


def ForgotPasswordClicked(form):
    """Handle forgot password button click."""
    logging.debug("Forgot password clicked")

    login_window = form.window()
    login_window.show_forgot_password()







def HandleSendOTPClicked(form):
    """Handle send OTP button click."""
    from PyQt6.QtWidgets import QMessageBox

    logging.debug("HandleSendOTPClicked clicked")
    email = form.email_input.text().strip()

    if not email:
        QMessageBox.warning(None, "Validation Error", "Please enter an email address")
        return

    try:

        from Constants import user_db

        isExist = user_db.is_email_exists(email)

        if isExist:
            logging.debug(f"User exists: {email}")

            SendOTP(form)


            QMessageBox.information(None, "Success", f"Verification code sent to {email}")
            #todo send otp to email






        else:
            logging.warning(f"User does not exist: {email}")
            QMessageBox.critical(None, "Error", "Email not found in database")



    except Exception as e:
        logging.error(f"Error checking email: {e}")
        QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")






def SendOTP(form):
    """Send OTP and store it with expiration time."""

    global pendingUsers

    email = form.email_input.text().strip()

    OTPCode = random.randint(100000, 999999)

    expiration_time = time.time() + (10 * 60)  # 10 minutes

    pendingUsers[email] = {
        'code': OTPCode,
        'expiredTime': expiration_time
    }

    send_email(email, "Neuron - Password Reset Verification Code", f"Your verification code is: {OTPCode}")
    logging.debug(f"OTP sent to {email}, expires at {expiration_time}")





def VerifyOTP(email, codeAttempt):
    """
    Verifys the OTP code entered by user.

    Args:
        email: User's email address
        codeAttempt: The OTP code the user entered (should be converted to int)

    Returns:
        tuple: (response_code, message)
    """


    global pendingUsers

    if email in pendingUsers:
        user_data = pendingUsers[email]

        # Check if code expired
        if time.time() > user_data['expiredTime']:
            del pendingUsers[email]
            logging.warning(f"OTP expired for {email}")
            return (RESP_ERROR, "Code expired, please request a new one")


        # Check if code matches
        elif user_data['code'] == codeAttempt:
            # Code is valid - user can now reset password
            logging.info(f"OTP verified successfully for {email}")
            return (RESP_VERIFY_OK, "Code verified successfully")


        else:
            logging.warning(f"Incorrect OTP attempt for {email}")
            return (RESP_ERROR, "Incorrect verification code")

    else:
        logging.warning(f"No pending OTP for {email}")
        return (RESP_ERROR, "No pending verification code for this email")