__author__ = "Yuval Malkan"


from uiConstants import *


import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QScrollArea,
    QStackedWidget, QSizePolicy, QGraphicsDropShadowEffect, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QIcon, QPixmap, QCursor








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
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            }}
        """)


# ──────────────────────────────────────────
#  GLOWING INPUT FIELD
# ──────────────────────────────────────────
class GlowInput(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFont(QFont(FONT_MONO, 11))
        self.setMinimumHeight(44)
        self._apply_style(False)

    def _apply_style(self, focused: bool):
        border = ACCENT_CYAN if focused else BORDER_COLOR
        glow   = f"border: 1px solid {border}; "
        self.setStyleSheet(f"""
            QLineEdit {{
                background: #0d1117;
                {glow}
                border-radius: 8px;
                color: {TEXT_PRIMARY};
                padding: 0 14px;
                selection-background-color: {ACCENT_CYAN}44;
            }}
            QLineEdit::placeholder {{
                color: {TEXT_MUTED};
            }}
        """)

    def focusInEvent(self, e):
        self._apply_style(True)
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        self._apply_style(False)
        super().focusOutEvent(e)


# ──────────────────────────────────────────
#  CYBER BUTTON
# ──────────────────────────────────────────
class CyberButton(QPushButton):
    def __init__(self, text, accent=ACCENT_CYAN, parent=None):
        super().__init__(text, parent)
        self.accent = accent
        self.setMinimumHeight(44)
        self.setFont(QFont(FONT_MONO, 10))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_style(False)

    def _apply_style(self, hovered: bool):
        bg = self.accent + "22" if not hovered else self.accent + "44"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                border: 1px solid {self.accent};
                border-radius: 8px;
                color: {self.accent};
                padding: 0 20px;
                letter-spacing: 1px;
            }}
            QPushButton:pressed {{
                background: {self.accent}66;
            }}
        """)

    def enterEvent(self, e):
        self._apply_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._apply_style(False)
        super().leaveEvent(e)


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
        self._refresh()

    def _refresh(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {ACCENT_CYAN}18;
                    border: none;
                    border-left: 3px solid {ACCENT_CYAN};
                    border-radius: 0px;
                    color: {ACCENT_CYAN};
                    text-align: left;
                    padding-left: 16px;
                    font-weight: bold;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0px;
                    color: {TEXT_DIM};
                    text-align: left;
                    padding-left: 16px;
                }}
                QPushButton:hover {{
                    background: {BORDER_COLOR};
                    color: {TEXT_PRIMARY};
                }}
            """)

    def nextCheckState(self):
        pass  # controlled externally





# ──────────────────────────────────────────
#  RESULT DISPLAY WIDGET
# ──────────────────────────────────────────
class ResultDisplay(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont(FONT_MONO, 10))
        self.setMinimumHeight(300)
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
                color: {TERMINAL_GREEN};
                padding: 14px;
                selection-background-color: {ACCENT_CYAN}33;
            }}
            QScrollBar:vertical {{
                background: {BG_CARD};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {ACCENT_CYAN}66;
                border-radius: 3px;
            }}
        """)


        self.setPlaceholderText("[Neuron - Waiting for scan]\n")


# ──────────────────────────────────────────
#  OSINT TAB  (= Main Dashboard)
# ──────────────────────────────────────────
class OsintDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG_DARK};")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # ── HEADER ──────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("OSINT ENGINE")
        title.setFont(QFont(FONT_TITLE, 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")


        hdr.addWidget(title)
        hdr.addStretch()
        root.addLayout(hdr)



        # ── SEARCH CARD ──────────────────────────
        search_card = Card()
        sc_layout = QVBoxLayout(search_card)
        sc_layout.setContentsMargins(20, 16, 20, 16)
        sc_layout.setSpacing(14)



        search_title = QLabel("Find Target")
        search_title.setFont(QFont(FONT_TITLE, 11, QFont.Weight.Bold))
        search_title.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent; border: none;")
        sc_layout.addWidget(search_title)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.name_input    = GlowInput("Full Name")
        self.phone_input   = GlowInput("Phone Number")
        self.email_input   = GlowInput("Email Address")

        input_row.addWidget(self.name_input, 2)
        input_row.addWidget(self.phone_input, 1)
        input_row.addWidget(self.email_input, 2)
        sc_layout.addLayout(input_row)

        # Second row
        input_row2 = QHBoxLayout()
        input_row2.setSpacing(10)

        self.address_input = GlowInput("Home Address")
        self.extra_input   = GlowInput("Additional information (social networks, nickname...)")

        input_row2.addWidget(self.address_input, 1)
        input_row2.addWidget(self.extra_input, 2)
        sc_layout.addLayout(input_row2)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.scan_btn  = CyberButton("▶  SCAN", ACCENT_CYAN)
        self.clear_btn = CyberButton("✕  CLEAR", ACCENT_RED)
        self.save_btn  = CyberButton("⬇  Save", ACCENT_CYAN)

        self.scan_btn.clicked.connect(self._on_scan)
        self.clear_btn.clicked.connect(self._on_clear)

        btn_row.addWidget(self.scan_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        sc_layout.addLayout(btn_row)

        root.addWidget(search_card)

        # ── RESULTS ──────────────────────────────
        result_label = QLabel("Scan Results")
        result_label.setFont(QFont(FONT_TITLE, 10))
        result_label.setStyleSheet(f"color: {TEXT_MUTED};")
        root.addWidget(result_label)

        self.result_box = ResultDisplay()
        root.addWidget(self.result_box, 1)

    # ── SLOTS ────────────────────────────────
    def _on_scan(self):
        name    = self.name_input.text().strip()
        phone   = self.phone_input.text().strip()
        email   = self.email_input.text().strip()
        address = self.address_input.text().strip()
        extra   = self.extra_input.text().strip()

        if not any([name, phone, email, address]):
            self.result_box.setPlainText("Error - Please enter at least one field")
            return

        lines = []
        lines.append("=" * 56)
        lines.append("  PROJECT NEURON  |  OSINT SCAN INITIATED")
        lines.append("=" * 56)
        if name:    lines.append(f"  NAME    : {name}")
        if phone:   lines.append(f"  PHONE   : {phone}")
        if email:   lines.append(f"  EMAIL   : {email}")
        if address: lines.append(f"  ADDRESS : {address}")
        if extra:   lines.append(f"  EXTRA   : {extra}")
        lines.append("-" * 56)
        lines.append("  [ ממתין לחיבור Gemini API... ]")
        lines.append("  → כאן יוצגו תוצאות הסריקה מהמקורות")
        lines.append("=" * 56)

        self.result_box.setPlainText("\n".join(lines))

    def _on_clear(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.address_input.clear()
        self.extra_input.clear()
        self.result_box.clear()


# ──────────────────────────────────────────
#  PLACEHOLDER TABS
# ──────────────────────────────────────────
class PlaceholderPage(QWidget):
    def __init__(self, title, accent=ACCENT_CYAN, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG_DARK};")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(title)
        lbl.setFont(QFont(FONT_MONO, 18))
        lbl.setStyleSheet(f"color: {accent}44;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("SOON...")
        sub.setFont(QFont(FONT_MONO, 11))
        sub.setStyleSheet(f"color: {TEXT_MUTED};")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl)
        layout.addWidget(sub)


# ──────────────────────────────────────────
#  MAIN WINDOW
# ──────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Neuron")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 780)
        self._apply_global_style()
        self._build_layout()

    def _apply_global_style(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background: {BG_DARK}; }}
            QScrollArea {{ background: transparent; border: none; }}
            QWidget {{ font-family: '{FONT_TITLE}'; }}
        """)

    def _build_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── SIDEBAR ──────────────────────────────
        sidebar = QWidget()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background: {BG_PANEL};
                border-right: 1px solid {BORDER_COLOR};
    
            }}
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo
        logo_area = QWidget()
        logo_area.setFixedHeight(100)
        logo_area.setStyleSheet(f"""
            background: {BG_PANEL};
            border-bottom: 1px solid {BORDER_COLOR};
        """)
        logo_layout = QHBoxLayout(logo_area)
        logo_layout.setContentsMargins(16, 0, 16, 0)


        logo_layout.addStretch()
        sb_layout.addWidget(logo_area)




        self.pages = QStackedWidget()
        self.nav_buttons = []

        nav_items = [
            ("⬡", "OSINT", OsintDashboard()),
            ("◈", "ROOMS",       PlaceholderPage("◈  ROOMS", ACCENT_GREEN)),
            ("◉", "NETWORK",      PlaceholderPage("◉  NETWORK", "#ff9f1c")),
            ("◎", "SETTINGS",            PlaceholderPage("◎  SETTINGS", TEXT_DIM)),
        ]

        for icon, label, page in nav_items:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda _, b=btn: self._switch_page(b))
            sb_layout.addWidget(btn)
            self.pages.addWidget(page)
            self.nav_buttons.append(btn)

        sb_layout.addStretch()




        root.addWidget(sidebar)
        root.addWidget(self.pages, 1)

        # Select first tab
        self._switch_page(self.nav_buttons[0])

    def _switch_page(self, clicked_btn: NavButton):
        for i, btn in enumerate(self.nav_buttons):
            is_active = btn is clicked_btn
            btn.setChecked(is_active)
            btn._refresh()
            if is_active:
                self.pages.setCurrentIndex(i)


# ──────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)

    load_application_font()

    app.setStyle("Fusion")



    # Dark palette for native widgets
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(BG_DARK))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base,            QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG_PANEL))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT_CYAN))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(BG_DARK))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())