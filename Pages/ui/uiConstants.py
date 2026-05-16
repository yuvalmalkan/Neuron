__author__ = "Yuval Malkan"

import os
from PyQt6.QtGui import QFontDatabase
import logging
from Constants import debug


base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── SEMANTIC COLORS ───────────────────────

# Window & Layout
WINDOW_BG       = "#090B11"
SIDEBAR_BG      = "#0F1117"
SIDEBAR_BORDER  = "#1E2132"

# Cards & Containers
CARD_BG         = "#0F1117"
CARD_BORDER     = "#1E2132"

# Inputs
INPUT_BG        = "#1E2132"
INPUT_BORDER    = "#2E3347"
INPUT_FOCUS     = "#84A0C6"
INPUT_SELECTION = "#84A0C644"

# Buttons (Primary - e.g., Scan, Save)
BTN_PRIMARY_BG     = "-"
BTN_PRIMARY_BORDER = "#84A0C6"
BTN_PRIMARY_TEXT   = BTN_PRIMARY_BORDER
BTN_PRIMARY_HOVER  = "#84A0C622"
BTN_PRIMARY_PRESS  = "#84A0C644"

# Buttons (Danger - e.g., Clear)
BTN_DANGER_BG      = "-"
BTN_DANGER_BORDER  = "#2E3347"
BTN_DANGER_TEXT    = BTN_DANGER_BORDER
BTN_DANGER_HOVER   = "#E2787844"
BTN_DANGER_PRESS   = "#E2787866"

# Navigation Topbar
NAV_TEXT_IDLE      = "#2E3347"
NAV_TEXT_HOVER     = "#6B7394"
NAV_BG_ACTIVE      = SIDEBAR_BG
NAV_BG_HOVER       = SIDEBAR_BG
NAV_TEXT_ACTIVE    = "#C6C8D1"
NAV_BORDER_ACTIVE  = "#84A0C6"

# Login/Auth Pages
LOGIN_WINDOW_BG    = "#090B11"
LOGIN_CARD_BG      = "rgba(9, 11, 17, 0.85)"
LOGIN_TEXT_TITLE   = "#C6C8D1"
LOGIN_TEXT_INPUT   = "#C6C8D1"

# Typography
TEXT_TITLE       = "#C6C8D1"
TEXT_BODY        = "#C6C8D1"
TEXT_PLACEHOLDER = "#6B7394"

# ── DATA TYPE COLORS (multi-color terminal output) ─────────────────
TEXT_IP          = "#89B8C2"   # IP addresses / hostnames
TEXT_PORT        = "#A093C7"   # ports / numeric IDs
TEXT_OK          = "#84A0C6"   # success / resolved
TEXT_ALERT       = "#E27878"   # critical / errors
TEXT_HANDLE      = "#84A0C6"   # usernames / handles
TEXT_MUTED       = "#2E3347"   # timestamps / secondary info
TEXT_TERMINAL    = "#84A0C6"   # general terminal output accent

# Misc
SCROLLBAR_BG     = "#090B11"
SCROLLBAR_HANDLE = "#1E213266"

# Fonts
FONT_MONO  = "SF Pro"
FONT_TITLE = "SF Pro"

# Assets
BwBgNeurons = os.path.join(root_dir, "Assets", "Photos", "neuronbgbw.jpg")


def load_stylesheet(filename):
    qss_path = os.path.join(base_dir, "Styles", f"{filename}.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            qss = f.read()

        replacements = {
            "@WINDOW_BG@":          WINDOW_BG,
            "@SIDEBAR_BG@":         SIDEBAR_BG,
            "@SIDEBAR_BORDER@":     SIDEBAR_BORDER,
            "@CARD_BG@":            CARD_BG,
            "@CARD_BORDER@":        CARD_BORDER,
            "@INPUT_BG@":           INPUT_BG,
            "@INPUT_BORDER@":       INPUT_BORDER,
            "@INPUT_FOCUS@":        INPUT_FOCUS,
            "@INPUT_SELECTION@":    INPUT_SELECTION,
            "@BTN_PRIMARY_BG@":     BTN_PRIMARY_BG,
            "@BTN_PRIMARY_BORDER@": BTN_PRIMARY_BORDER,
            "@BTN_PRIMARY_TEXT@":   BTN_PRIMARY_TEXT,
            "@BTN_PRIMARY_HOVER@":  BTN_PRIMARY_HOVER,
            "@BTN_PRIMARY_PRESS@":  BTN_PRIMARY_PRESS,
            "@BTN_DANGER_BG@":      BTN_DANGER_BG,
            "@BTN_DANGER_BORDER@":  BTN_DANGER_BORDER,
            "@BTN_DANGER_TEXT@":    BTN_DANGER_TEXT,
            "@BTN_DANGER_HOVER@":   BTN_DANGER_HOVER,
            "@BTN_DANGER_PRESS@":   BTN_DANGER_PRESS,
            "@NAV_TEXT_IDLE@":      NAV_TEXT_IDLE,
            "@NAV_TEXT_HOVER@":     NAV_TEXT_HOVER,
            "@NAV_BG_HOVER@":       NAV_BG_HOVER,
            "@NAV_TEXT_ACTIVE@":    NAV_TEXT_ACTIVE,
            "@NAV_BG_ACTIVE@":      NAV_BG_ACTIVE,
            "@NAV_BORDER_ACTIVE@":  NAV_BORDER_ACTIVE,
            "@TEXT_TITLE@":         TEXT_TITLE,
            "@TEXT_BODY@":          TEXT_BODY,
            "@TEXT_PLACEHOLDER@":   TEXT_PLACEHOLDER,
            "@TEXT_TERMINAL@":      TEXT_TERMINAL,
            "@SCROLLBAR_BG@":       SCROLLBAR_BG,
            "@SCROLLBAR_HANDLE@":   SCROLLBAR_HANDLE,
            "@FONT_MONO@":          FONT_MONO,
            "@FONT_TITLE@":         FONT_TITLE,
            "@BwBgNeurons@":        BwBgNeurons,
        }

        for key, val in replacements.items():
            qss = qss.replace(key, val)

        return qss

    except FileNotFoundError:
        logging.debug(f"Error: {filename}.qss not found at {qss_path}")
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