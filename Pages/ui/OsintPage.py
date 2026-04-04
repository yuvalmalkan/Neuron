__author__ = "Yuval Malkan"

import sys
import os
import time

from uiConstants import *
from uiElements import shadow, Card, GlowInput, CyberButton, NavButton, ResultDisplay

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap
from RoomsPage import RoomsPanel

# ──────────────────────────────────────────
#  OSINT TAB  (= Main Dashboard)
# ──────────────────────────────────────────
class OsintDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("osintDashboard")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # ── HEADER ──────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("OSINT ENGINE")
        title.setFont(QFont(FONT_TITLE, 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_TITLE};")

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
        search_title.setStyleSheet(f"color: {TEXT_TITLE}; background: transparent; border: none;")
        sc_layout.addWidget(search_title)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.name_input = GlowInput("Full Name")
        self.phone_input = GlowInput("Phone Number")
        self.email_input = GlowInput("Email Address")

        input_row.addWidget(self.name_input, 2)
        input_row.addWidget(self.phone_input, 1)
        input_row.addWidget(self.email_input, 2)
        sc_layout.addLayout(input_row)

        # Second row
        input_row2 = QHBoxLayout()
        input_row2.setSpacing(10)

        self.address_input = GlowInput("Home Address")
        self.extra_input = GlowInput("Additional information (social networks, nickname...)")

        input_row2.addWidget(self.address_input, 1)
        input_row2.addWidget(self.extra_input, 2)
        sc_layout.addLayout(input_row2)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        # Use semantic variant tags instead of raw color constants
        self.scan_btn = CyberButton("▶  SCAN", "primary")
        self.clear_btn = CyberButton("✕  CLEAR", "danger")
        self.save_btn = CyberButton("⬇  Save", "primary")

        self.scan_btn.clicked.connect(self._on_scan)
        self.clear_btn.clicked.connect(self._on_clear)

        btn_row.addWidget(self.scan_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        sc_layout.addLayout(btn_row)

        root.addWidget(search_card)

        # ── RESULTS ──────────────────────────────
        result_label = QLabel("SCAN RESULTS")
        result_label.setFont(QFont(FONT_TITLE, 15))
        result_label.setStyleSheet(f"color: {TEXT_PLACEHOLDER};")
        root.addWidget(result_label)

        self.result_box = ResultDisplay()
        root.addWidget(self.result_box, 1)

    # ── SLOTS ────────────────────────────────
    def _on_scan(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        address = self.address_input.text().strip()
        extra = self.extra_input.text().strip()

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
    def __init__(self, title, hex_color="#4ADE80", parent=None):
        super().__init__(parent)
        self.setObjectName("placeholderPage")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(title)
        lbl.setFont(QFont(FONT_MONO, 18))
        lbl.setStyleSheet(f"color: {hex_color}44;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("SOON...")
        sub.setFont(QFont(FONT_MONO, 11))
        sub.setStyleSheet(f"color: {TEXT_PLACEHOLDER};")
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
        self._build_layout()

    def _build_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── SIDEBAR ──────────────────────────────
        sidebar = QWidget()
        sidebar.setFixedWidth(180)
        sidebar.setObjectName("sidebar")

        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(10)

        logo_area = QWidget()
        logo_area.setFixedHeight(80)
        logo_area.setObjectName("logoArea")

        # Path to logo
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        logo_path = os.path.join(root_dir, "Assets", "Photos", "neuronBanner2.png")

        logo_layout = QHBoxLayout(logo_area)
        logo_layout.setContentsMargins(16, 0, 16, 0)

        logo_label = QLabel()
        logo_pixmap = QPixmap(logo_path)

        # לסדר איכות תמונה
        ratio = self.devicePixelRatioF()
        physical_height = int(60 * ratio)
        scaled_logo = logo_pixmap.scaledToHeight(physical_height, Qt.TransformationMode.SmoothTransformation)
        scaled_logo.setDevicePixelRatio(ratio)
        logo_label.setPixmap(scaled_logo)

        logo_layout.addWidget(logo_label)
        logo_layout.addStretch()
        sb_layout.addWidget(logo_area)

        self.pages = QStackedWidget()
        self.nav_buttons = []

        nav_items = [
            (">", "OSINT", OsintDashboard()),
            (">", "ROOMS", RoomsPanel()),
            (">", "NETWORK", PlaceholderPage("◉  NETWORK", "#ff9f1c")),
            (">", "SETTINGS", PlaceholderPage("◎  SETTINGS", "#8892a0")),
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
            if is_active:
                self.pages.setCurrentIndex(i)

# ──────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)

    load_application_font()
    app.setStyle("Fusion")

    # Apply the global QSS!
    app.setStyleSheet(load_stylesheet("main"))

    # Dark palette for native widgets using semantic variables
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(WINDOW_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_TITLE))
    palette.setColor(QPalette.ColorRole.Base, QColor(CARD_BG))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(SIDEBAR_BG))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(INPUT_FOCUS))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(WINDOW_BG))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())