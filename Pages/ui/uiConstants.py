__author__ = "Yuval Malkan"

import os
from PyQt6.QtGui import QFontDatabase

# ── SEMANTIC COLORS ───────────────────────

# Window & Layout
WINDOW_BG       = "#050A05"
SIDEBAR_BG      = "#0C140C"
SIDEBAR_BORDER  = "#1A2E1A"

# Cards & Containers
CARD_BG         = "#0C140C"
CARD_BORDER     = "#1A2E1A"

# Inputs
INPUT_BG        = "#0d1117"
INPUT_BORDER    = "#1A2E1A"
INPUT_FOCUS     = "#4ADE80"
INPUT_SELECTION = "#4ADE8044"

# Buttons (Primary - e.g., Scan, Save)
BTN_PRIMARY_BG     = "#4ADE8022"
BTN_PRIMARY_BORDER = "#4ADE80"
BTN_PRIMARY_TEXT   = "#4ADE80"
BTN_PRIMARY_HOVER  = "#4ADE8044"
BTN_PRIMARY_PRESS  = "#4ADE8066"

# Buttons (Danger - e.g., Clear)
BTN_DANGER_BG      = "#EF233C22"
BTN_DANGER_BORDER  = "#EF233C"
BTN_DANGER_TEXT    = "#EF233C"
BTN_DANGER_HOVER   = "#EF233C44"
BTN_DANGER_PRESS   = "#EF233C66"

# Navigation Sidebar
NAV_TEXT_IDLE      = "#8892a0"
NAV_TEXT_HOVER     = "#CAF0F8"
NAV_BG_HOVER       = "#1A2E1A"
NAV_TEXT_ACTIVE    = "#4ADE80"
NAV_BG_ACTIVE      = SIDEBAR_BG
NAV_BORDER_ACTIVE  = "#4ADE80"

# Typography
TEXT_TITLE       = "#CAF0F8"
TEXT_BODY        = "#CAF0F8"
TEXT_PLACEHOLDER = "#5a6474"
TEXT_TERMINAL    = "#22C55E"

# Misc
SCROLLBAR_BG     = "#0C140C"
SCROLLBAR_HANDLE = "#4ADE8066"


# ── FONTS ─────────────────────────────────
FONT_MONO  = "SF Pro"
FONT_TITLE = "SF Pro"


def load_stylesheet():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    qss_path = os.path.join(base_dir, "Styles", "main.qss")

    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            qss = f.read()

        replacements = {
            "@WINDOW_BG@": WINDOW_BG,
            "@SIDEBAR_BG@": SIDEBAR_BG,
            "@SIDEBAR_BORDER@": SIDEBAR_BORDER,
            "@CARD_BG@": CARD_BG,
            "@CARD_BORDER@": CARD_BORDER,
            "@INPUT_BG@": INPUT_BG,
            "@INPUT_BORDER@": INPUT_BORDER,
            "@INPUT_FOCUS@": INPUT_FOCUS,
            "@INPUT_SELECTION@": INPUT_SELECTION,
            "@BTN_PRIMARY_BG@": BTN_PRIMARY_BG,
            "@BTN_PRIMARY_BORDER@": BTN_PRIMARY_BORDER,
            "@BTN_PRIMARY_TEXT@": BTN_PRIMARY_TEXT,
            "@BTN_PRIMARY_HOVER@": BTN_PRIMARY_HOVER,
            "@BTN_PRIMARY_PRESS@": BTN_PRIMARY_PRESS,
            "@BTN_DANGER_BG@": BTN_DANGER_BG,
            "@BTN_DANGER_BORDER@": BTN_DANGER_BORDER,
            "@BTN_DANGER_TEXT@": BTN_DANGER_TEXT,
            "@BTN_DANGER_HOVER@": BTN_DANGER_HOVER,
            "@BTN_DANGER_PRESS@": BTN_DANGER_PRESS,
            "@NAV_TEXT_IDLE@": NAV_TEXT_IDLE,
            "@NAV_TEXT_HOVER@": NAV_TEXT_HOVER,
            "@NAV_BG_HOVER@": NAV_BG_HOVER,
            "@NAV_TEXT_ACTIVE@": NAV_TEXT_ACTIVE,
            "@NAV_BG_ACTIVE@": NAV_BG_ACTIVE,
            "@NAV_BORDER_ACTIVE@": NAV_BORDER_ACTIVE,
            "@TEXT_TITLE@": TEXT_TITLE,
            "@TEXT_BODY@": TEXT_BODY,
            "@TEXT_PLACEHOLDER@": TEXT_PLACEHOLDER,
            "@TEXT_TERMINAL@": TEXT_TERMINAL,
            "@SCROLLBAR_BG@": SCROLLBAR_BG,
            "@SCROLLBAR_HANDLE@": SCROLLBAR_HANDLE,
            "@FONT_MONO@": FONT_MONO,
            "@FONT_TITLE@": FONT_TITLE,
        }

        for key, val in replacements.items():
            qss = qss.replace(key, val)

        return qss

    except FileNotFoundError:
        print(f"[-] Error: main.qss not found at {qss_path}")
        return ""


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