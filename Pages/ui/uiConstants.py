__author__ = "Yuval Malkan"

import os
from PyQt6.QtGui import QFontDatabase

# ── COLORS ────────────────────────────────
BG_DARK      = "#0A0F1E"
BG_PANEL     = "#0D1B3E"
BG_CARD      = "#141820"
BORDER_COLOR = "#1A2F5E"

#ACCENT_BLUE  = "#1500d5"

TERMINAL_GREEN = "#22C55E"
ACCENT_CYAN  = "#00B4D8"
ACCENT_GREEN = "#48CAE4"
ACCENT_RED   = "#EF233C"

TEXT_PRIMARY = "#CAF0F8"
TEXT_MUTED   = "#5a6474"
TEXT_DIM     = "#8892a0"

# ── FONTS ─────────────────────────────────
FONT_MONO  = "SF Pro"
FONT_TITLE = "SF Pro"


def load_application_font():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    font_path = os.path.join(base_dir, "Assets", "Fonts", "SF-Pro.ttf")

    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            print(f"[+] Success: Loaded custom font families -> {families}")
        else:
            print(f"[-] Error: Failed to load font from {font_path}")
    else:
        print(f"[-] Error: Font file not found at {font_path}")