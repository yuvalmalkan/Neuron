__author__ = "Yuval Malkan"

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStackedWidget, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

from Pages.ui.uiConstants import *
from Pages.ui.uiElements import Card, GlowInput, GlowingButton, HyperButton
from Pages.ui.signUp import SignupForm
from Pages.ui.OsintPage import MainWindow

from Pages.logic.LoginLogic import *



# ──────────────────────────────────────────
#  TYPING ANIMATION WIDGET
# ──────────────────────────────────────────
class TypingLabel(QLabel):
    def __init__(self, text_to_type, parent=None):
        super().__init__(parent)
        self.full_text = text_to_type
        self.current_text = ""
        self.index = 0

        self.setFont(QFont(FONT_TITLE, 45, QFont.Weight.Bold))
        self.setStyleSheet(f"color: {TEXT_TITLE};")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Setup the timer for the typing effect
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._type_next_char)
        self.timer.start(40)  # Speed in milliseconds per character

    def _type_next_char(self):
        if self.index < len(self.full_text):
            self.current_text += self.full_text[self.index]
            self.setText(self.current_text + " ")  # Add a terminal block cursor
            self.index += 1
        else:
            self.timer.stop()
            # Blinking cursor effect can be added here later







# ──────────────────────────────────────────
#  START PAGE MAIN WINDOW
# ──────────────────────────────────────────
class Login(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neuron")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 780)

        self._build_layout()

    def _build_layout(self):
        central = QWidget()
        self.setCentralWidget(central)

        # Single unified layout for the whole window
        root = QHBoxLayout(central)
        root.setContentsMargins(80, 0, 80, 0)  # Margins to keep things away from the screen edges
        root.setSpacing(40)

        # ── LEFT SIDE (ANIMATION) ─────────────────
        self.typing_label = TypingLabel("N  E  U  R  O  N \nA Project By Yuval Malkan")
        root.addWidget(self.typing_label, 1)


        # ── RIGHT SIDE (AUTH CARD) ─────────────────
        card_container = QVBoxLayout()
        card_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.auth_card = Card()
        self.auth_card.setFixedSize(450, 480)

        card_layout = QVBoxLayout(self.auth_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        hdr = QHBoxLayout()
        title = QLabel("SYSTEM LOGIN")
        title.setFont(QFont(FONT_TITLE, 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_TITLE};")
        hdr.addWidget(title)
        hdr.addStretch()
        card_layout.addLayout(hdr)


        """
        sub_lbl = QLabel("GET INTO NEURON")
        sub_lbl.setFont(QFont(FONT_MONO, 10))
        sub_lbl.setStyleSheet(f"color: #EF233C; letter-spacing: 2px;")
        card_layout.addWidget(sub_lbl)
        card_layout.addSpacing(10)

        """

        self.stacked_forms = QStackedWidget()
        self.login_form = LoginForm(self.show_signup)
        self.signup_form = SignupForm(self.show_login)

        self.stacked_forms.addWidget(self.login_form)
        self.stacked_forms.addWidget(self.signup_form)

        card_layout.addWidget(self.stacked_forms)

        # Add the card container to the right side of the root layout
        card_container.addWidget(self.auth_card)
        root.addLayout(card_container, 1)



    def show_signup(self):
        self.stacked_forms.setCurrentIndex(1)
        self.auth_card.setFixedSize(450, 560)



    def show_login(self):
        self.stacked_forms.setCurrentIndex(0)
        self.auth_card.setFixedSize(450, 480)












# ──────────────────────────────────────────
#  LOGIN FORM
# ──────────────────────────────────────────
class LoginForm(QWidget):
    def __init__(self, switch_callback, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        self.user_input = GlowInput("Username")
        self.pass_input = GlowInput("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.forgot_button = HyperButton("Forgot Password?", "primary")
        self.login_btn = GlowingButton("LOGIN INTO NEURON", "primary")
        self.switch_btn = GlowingButton("NEW USER? SIGN UP", "danger")

        self.switch_btn.clicked.connect(switch_callback)
        # Pass the form as context so LoginClicked can access input fields
        self.login_btn.clicked.connect(lambda: LoginClicked(self))
        self.forgot_button.clicked.connect(ForgotPasswordClicked)

        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.forgot_button)
        layout.addSpacing(10)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.switch_btn)


#--------
#forgot password class
#--------

class ForgotPasswordForm(QWidget):
    #todo write forgot password form, with a 5 minute code sent to email and input field to enter code and new password
    pass





def LoginClicked(form: LoginForm):
    """
    Handle login button click event.
    Validates credentials and authenticates user.

    Args:
        form: LoginForm instance to access username and password inputs
    """
    import logging
    from Pages.logic.LoginLogic import handle_login
    from UserDatabase import UserDatabase

    # Get username and password from input fields
    username = form.user_input.text().strip()
    password = form.pass_input.text()

    logging.debug(f"Login clicked for user: {username}")

    # Validate input fields
    if not username or not password:
        logging.warning("Login attempt with empty credentials")
        QMessageBox.warning(None, "Validation Error", "Please enter both username and password")
        return






def LoginClicked(form: LoginForm):
    """
    Handle login button click event.
    Validates credentials and authenticates user.

    Args:
        form: LoginForm instance to access username and password inputs
    """
    import logging
    from Pages.logic.LoginLogic import handle_login
    from UserDatabase import UserDatabase
    from Constants import RESP_LOGIN_OK, RESP_LOGIN_FAIL, RESP_LOGIN_USER_NOT_FOUND

    # Get username and password from input fields
    username = form.user_input.text().strip()
    password = form.pass_input.text()

    logging.debug(f"Login clicked for user: {username}")

    # Validate input fields
    if not username or not password:
        logging.warning("Login attempt with empty credentials")
        QMessageBox.warning(None, "Validation Error", "Please enter both username and password")
        return

    try:
        # Initialize database connection with explicit path
        import os
        # Get the root directory (go up 2 levels from Pages/ui/)
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(root_dir, 'Databases', 'users.pkl')
        db = UserDatabase(db_path)

        # Call login handler
        success, response_code, user = handle_login(username, password, db)

        if success:
            logging.info(f"User {username} logged in successfully")
            #QMessageBox.information(None, "Success", f"Welcome back, {user.username}!")
            login_window = form.window()
            login_window.close()


            osint_window = MainWindow()
            osint_window.show()



        else:
            # Provide specific error messages based on response code using constants
            if response_code == RESP_LOGIN_USER_NOT_FOUND:
                error_msg = "Username not found"
                logging.warning(f"Login failed: {error_msg} ({username})")
            elif response_code == RESP_LOGIN_FAIL:
                error_msg = "Incorrect password"
                logging.warning(f"Login failed: {error_msg} ({username})")
            else:
                error_msg = "Login failed. Please try again."
                logging.error(f"Login failed with response code: {response_code}")

            QMessageBox.critical(None, "Login Failed", error_msg)
            # Clear password field on failed login
            form.pass_input.clear()

    except Exception as e:
        logging.error(f"Unexpected error during login: {e}")
        QMessageBox.critical(None, "Error", f"An unexpected error occurred: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during login: {e}")
        QMessageBox.critical(None, "Error", f"An unexpected error occurred: {str(e)}")








#todo add email recovery with 6 digit code
def ForgotPasswordClicked():
    """Handle forgot password button click."""
    import logging
    logging.debug("Forgot password clicked")
    QMessageBox.information(None, "Forgot Password", "Password recovery feature coming soon")
    QMessageBox.inp










if __name__ == "__main__":
    app = QApplication(sys.argv)

    load_application_font()
    app.setStyle("Fusion")
    app.setStyleSheet(load_stylesheet("main"))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(WINDOW_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_TITLE))
    palette.setColor(QPalette.ColorRole.Base, QColor(CARD_BG))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(SIDEBAR_BG))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(INPUT_FOCUS))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(WINDOW_BG))
    app.setPalette(palette)

    window = Login()
    window.show()
    sys.exit(app.exec())