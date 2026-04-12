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
#  LOGIN FORM
# ──────────────────────────────────────────
class LoginForm(QWidget):
    def __init__(self, switch_callback , parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        self.user_input = GlowInput("Username")
        self.pass_input = GlowInput("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        #self.forgot_button = QPushButton("FORGOT PASSWORD? ")
        self.forgot_button = HyperButton("Forgot Password?", "primary")

        self.login_btn = GlowingButton("LOGIN INTO NEURON", "primary")
        self.switch_btn = GlowingButton("NEW USER? SIGN UP", "danger")




        self.switch_btn.clicked.connect(switch_callback)
        self.login_btn.clicked.connect(LoginClicked)
        self.forgot_button.clicked.connect(ForgotPasswordClicked)

        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.forgot_button)
        layout.addSpacing(10)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.switch_btn)


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







def ForgotPasswordClicked():
    QMessageBox.information(None, "", "Forgot password clicked")





def LoginClicked():
    QMessageBox.information(None, "", "Login clicked")






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