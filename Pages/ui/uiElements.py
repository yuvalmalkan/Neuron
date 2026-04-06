__author__ = "Yuval Malkan"


from uiConstants import *
from PyQt6.QtWidgets import (
    QLineEdit, QPushButton, QFrame, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QCursor





def shadow(widget, color="#00d4ff", blur=20, offset=(0, 0)):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setColor(QColor(color))
    fx.setOffset(*offset)
    widget.setGraphicsEffect(fx)
    return fx

# ──────────────────────────────────────────
#  REUSABLE STYLED CARD
# ──────────────────────────────────────────
class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Style handles globally via QSS

# ──────────────────────────────────────────
#  GLOWING INPUT FIELD
# ──────────────────────────────────────────
class GlowInput(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFont(QFont(FONT_MONO, 11))
        self.setMinimumHeight(44)
        # States (:focus, ::placeholder) handled globally via QSS

# ──────────────────────────────────────────
#  CYBER BUTTON
# ──────────────────────────────────────────
class CyberButton(QPushButton):
    def __init__(self, text, variant="primary", parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(44)
        self.setFont(QFont(FONT_MONO, 10))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Set property for QSS to target specific variants ("primary" or "danger")
        self.setProperty("variant", variant)

# ──────────────────────────────────────────
#  SIDEBAR NAV BUTTON
# ──────────────────────────────────────────
class NavButton(QPushButton):
    def __init__(self, icon_text, label, parent=None):
        super().__init__(parent)
        self.label = label
        self.icon_text = icon_text
        self.setCheckable(True)
        self.setMinimumHeight(52)
        self.setFont(QFont(FONT_TITLE, 10))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setText(f"  {icon_text}  {label}")





# ──────────────────────────────────────────
#  RESULT DISPLAY WIDGET
# ──────────────────────────────────────────
class ResultDisplay(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont(FONT_MONO, 10))
        self.setMinimumHeight(300)
        self.setPlaceholderText("[Neuron - Waiting for scan]\n")






# ──────────────────────────────────────────
#  CUSTOM AUTHENTICATION WIDGETS
# ──────────────────────────────────────────
class AuthInput(GlowInput):
    def __init__(self, placeholder="", is_password=False, parent=None):
        super().__init__(placeholder, parent)
        if is_password:
            self.setEchoMode(QLineEdit.EchoMode.Password)



class StandardAuthButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(40)

        from uiConstants import FONT_TITLE
        self.setFont(QFont(FONT_TITLE, 10, QFont.Weight.Bold))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))




class LinkButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        from uiConstants import FONT_MONO
        self.setFont(QFont(FONT_MONO, 9))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))