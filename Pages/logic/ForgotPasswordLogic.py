__author__ = "Yuval Malkan"

import logging


def ForgotPasswordClicked(form):
    """Handle forgot password button click."""
    logging.debug("Forgot password clicked")

    login_window = form.window()
    login_window.show_forgot_password()
