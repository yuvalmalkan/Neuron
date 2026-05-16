__author__ = "Yuval Malkan"


import os
from PyQt6.QtGui import QFontDatabase
import logging
from Constants import debug


base_dir = os.path.dirname(os.path.abspath(__file__))

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))





# ── SEMANTIC COLORS ───────────────────────

# Window & Layout
WINDOW_BG       = "#000000"
SIDEBAR_BG      = "#0D0D0D"
SIDEBAR_BORDER  = "#1C1C1C"

# Cards & Containers
CARD_BG         = "#0D0D0D"
CARD_BORDER     = "#1C1C1C"

# Inputs
INPUT_BG        = "#3D3D3B"
INPUT_BORDER    = "#2E2E2E"
INPUT_FOCUS     = "#F7F7F7"
INPUT_SELECTION = "#4ADE8044"

# Buttons (Primary - e.g., Scan, Save)
BTN_PRIMARY_BG     = "-"
BTN_PRIMARY_BORDER = "#EEEEEE"
BTN_PRIMARY_TEXT   = BTN_PRIMARY_BORDER
BTN_PRIMARY_HOVER  = "#BB000044"
BTN_PRIMARY_PRESS  = "#4ADE8066"

# Buttons (Danger - e.g., Clear)
BTN_DANGER_BG      = "-"
BTN_DANGER_BORDER  = "#3D3D3B"
BTN_DANGER_TEXT    = BTN_DANGER_BORDER
BTN_DANGER_HOVER   = "#EF233C44"
BTN_DANGER_PRESS   = "#EF233C66"

# Navigation Topbar
NAV_TEXT_IDLE      = "#3D3D3B"
NAV_TEXT_HOVER     = "#AAAAAA"
NAV_BG_ACTIVE      = SIDEBAR_BG
NAV_BG_HOVER       = SIDEBAR_BG
NAV_TEXT_ACTIVE    = "#D4D4D4"
NAV_BORDER_ACTIVE  = "#EEEEEE"

# Typography
TEXT_TITLE       = "#DDDDDD"
TEXT_BODY        = "#DDDDDD"
TEXT_PLACEHOLDER = "#E8E8E8"
#TEXT_TERMINAL    = "#22C55E"
TEXT_TERMINAL = "#1F6FEB"



# Misc
SCROLLBAR_BG     = "#0C140C"
SCROLLBAR_HANDLE = "#4ADE8066"


# FONTS
FONT_MONO  = "SF Pro"
FONT_TITLE = "SF Pro"


#Assets
BwBgNeurons = os.path.join(root_dir, "Assets", "Photos", "neuronbgbw.jpg")







def load_stylesheet(filename):

    qss_path = os.path.join(base_dir, "Styles", f"{filename}.qss")

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
            "@BwBgNeurons@": BwBgNeurons,
        }

        for key, val in replacements.items():
            qss = qss.replace(key, val)

        return qss

    except FileNotFoundError:
        logging.debug(f"Error: main.qss not found at {qss_path}")
        return ""


def load_application_font():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    font_path = os.path.join(base_dir, "Assets", "Fonts", "SF-Pro.ttf")

    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)

            logging.debug(f"Loaded custom font families {families}")
        else:
            logging.debug(f"Failed to load font from {font_path}")
    else:
        logging.debug(f"Font file not found at {font_path}")



