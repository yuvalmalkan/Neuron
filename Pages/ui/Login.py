__author__ = "Yuval Malkan"


import sys
import logging
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStackedWidget, QLineEdit, QPushButton, QMessageBox, QGraphicsBlurEffect
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

from Pages.ui.uiConstants import *
from Pages.ui.uiElements import Card, GlowInput, GlowingButton, HyperButton
from Pages.ui.signUp import SignupForm
from Pages.ui.ForgotPassword import ForgotPasswordForm
from Pages.ui.OsintPage import MainWindow

from Pages.logic.LoginLogic import handle_login
from Pages.logic.ForgotPasswordLogic import ForgotPasswordClicked
from UserDatabase import UserDatabase
from Constants import RESP_LOGIN_USER_NOT_FOUND, RESP_LOGIN_FAIL
from Pages.ui.uiConstants import BwBgNeurons
from PyQt6.QtGui import QPixmap, QBrush

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
        # Apply background to main window, not central widget
        self.setStyleSheet(f"""
            QMainWindow {{
                background-image: url({BwBgNeurons});
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
                background-size: cover;
                background-color: #000000;
            }}
        """)

        central = QWidget()
        central.setStyleSheet("QWidget { background-color: transparent; }")
        self.setCentralWidget(central)

        # Single unified layout for the whole window
        root = QHBoxLayout(central)
        root.setContentsMargins(80, 0, 80, 0)
        root.setSpacing(40)

        # ── LEFT SIDE (ANIMATION) ─────────────────
        self.typing_label = TypingLabel("N  E  U  R  O  N \nA Project By Yuval Malkan")
        #\n\nOSINT\nNetwork\nCommunication\nPowered By AI! \n
        root.addWidget(self.typing_label, 1)

        # ── RIGHT SIDE (AUTH CARD) ─────────────────
        card_container = QVBoxLayout()
        card_container.setAlignment(Qt.AlignmentFlag.AlignCenter)




#

        self.auth_card = Card()
        self.auth_card.setFixedSize(450, 480)
        self.auth_card.setStyleSheet("QWidget { background-color: rgba(0, 0, 0, 0.7); }")


        card_layout = QVBoxLayout(self.auth_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        hdr = QHBoxLayout()
        title = QLabel("SYSTEM LOGIN")
        title.setFont(QFont(FONT_TITLE, 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_TITLE}; background-color: transparent;")
        hdr.addWidget(title)
        hdr.addStretch()

        card_layout.addLayout(hdr)

        self.stacked_forms = QStackedWidget()
        self.stacked_forms.setStyleSheet("background-color: transparent;")
        self.login_form = LoginForm(self.show_signup)
        self.signup_form = SignupForm(self.show_login)
        self.forgot_password_form = ForgotPasswordForm()

        self.stacked_forms.addWidget(self.login_form)
        self.stacked_forms.addWidget(self.signup_form)
        self.stacked_forms.addWidget(self.forgot_password_form)

        card_layout.addWidget(self.stacked_forms)


        card_container.addWidget(self.auth_card)
        root.addLayout(card_container, 1)

    def show_signup(self):
        self.stacked_forms.setCurrentIndex(1)
        self.auth_card.setFixedSize(450, 560)



    def show_login(self):
        self.stacked_forms.setCurrentIndex(0)
        self.auth_card.setFixedSize(450, 480)


    def show_forgot_password(self):
        self.stacked_forms.setCurrentIndex(2)
        self.auth_card.setFixedSize(450, 520)











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



        self.login_btn.clicked.connect(lambda: LoginClicked(self))
        self.forgot_button.clicked.connect(lambda: ForgotPasswordClicked(self))

        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.forgot_button)
        layout.addSpacing(10)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.switch_btn)











def LoginClicked(form: LoginForm):
    """
    Handle login button click event.
    Validates credentials and authenticates user.

    Args:
        form: LoginForm instance to access username and password inputs
    """


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