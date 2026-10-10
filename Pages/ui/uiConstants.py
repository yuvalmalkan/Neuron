__author__ = "Yuval Malkan"

import os
from PyQt6.QtGui import QFontDatabase
import logging
from Constants import debug


base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



# window & Layout
WINDOW_BG       = "#161616"
SIDEBAR_BG      = "#1F1F1F"
SIDEBAR_BORDER  = "#2E2E2E"

# cards & containers
CARD_BG         = "#1F1F1F"
CARD_BORDER     = "#2E2E2E"

# inputs
INPUT_BG        = "#2E2E2E"
INPUT_BORDER    = "#3D3D3D"
INPUT_FOCUS     = "#D4D4D4"
INPUT_SELECTION = "#D4D4D444"

# primary buttons
BTN_PRIMARY_BG     = "-"
BTN_PRIMARY_BORDER = "#D4D4D4"
BTN_PRIMARY_TEXT   = BTN_PRIMARY_BORDER
BTN_PRIMARY_HOVER  = "#D4D4D422"
BTN_PRIMARY_PRESS  = "#D4D4D444"

# danger buttons
BTN_DANGER_BG      = "-"
BTN_DANGER_BORDER  = "#3D3D3D"
BTN_DANGER_TEXT    = BTN_DANGER_BORDER
BTN_DANGER_HOVER   = "#C0392B44"
BTN_DANGER_PRESS   = "#C0392B66"

# navigation topbar
NAV_TEXT_IDLE      = "#3D3D3D"
NAV_TEXT_HOVER     = "#888888"
NAV_BG_ACTIVE      = SIDEBAR_BG
NAV_BG_HOVER       = SIDEBAR_BG
NAV_TEXT_ACTIVE    = "#E8E8E8"
NAV_BORDER_ACTIVE  = "#D4D4D4"

# login/auth pages
LOGIN_WINDOW_BG    = "#161616"
LOGIN_CARD_BG      = "rgba(22, 22, 22, 0.85)"
LOGIN_TEXT_TITLE   = "#E8E8E8"
LOGIN_TEXT_INPUT   = "#E8E8E8"

# typography
TEXT_TITLE       = "#E8E8E8"
TEXT_BODY        = "#E8E8E8"
TEXT_PLACEHOLDER = "#555555"

# data type colors
TEXT_IP          = "#AAAAAA"   # ip addresses, hostnames
TEXT_PORT        = "#888888"   # port numbers
TEXT_OK          = "#5A7A5A"   # success, resolved, online
TEXT_ALERT       = "#C0392B"   # critical errors, warnings
TEXT_HANDLE      = "#CCCCCC"   # usernames, social
TEXT_MUTED       = "#3D3D3D"   # timestamps
TEXT_TERMINAL    = "#D4D4D4"   # general terminal prompt

# misc
SCROLLBAR_BG     = "#161616"
SCROLLBAR_HANDLE = "#2E2E2E66"

# fonts
FONT_MONO  = "SF Pro"
FONT_TITLE = "SF Pro"

# assets
BwBgNeurons   = os.path.join(root_dir, "Assets", "Photos", "neuronbgbw.jpg")
BlueBgNeurons = os.path.join(root_dir, "Assets", "Photos", "neuronbgblue.jpg")


def load_stylesheet(filename):
    qss_path = os.path.join(base_dir, "Styles", f"{filename}.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            qss = f.read()

        replacements = {
            # layout
            "@WINDOW_BG@":          WINDOW_BG,
            "@SIDEBAR_BG@":         SIDEBAR_BG,
            "@SIDEBAR_BORDER@":     SIDEBAR_BORDER,
            # cards
            "@CARD_BG@":            CARD_BG,
            "@CARD_BORDER@":        CARD_BORDER,
            # inputs
            "@INPUT_BG@":           INPUT_BG,
            "@INPUT_BORDER@":       INPUT_BORDER,
            "@INPUT_FOCUS@":        INPUT_FOCUS,
            "@INPUT_SELECTION@":    INPUT_SELECTION,
            # buttons primary
            "@BTN_PRIMARY_BG@":     BTN_PRIMARY_BG,
            "@BTN_PRIMARY_BORDER@": BTN_PRIMARY_BORDER,
            "@BTN_PRIMARY_TEXT@":   BTN_PRIMARY_TEXT,
            "@BTN_PRIMARY_HOVER@":  BTN_PRIMARY_HOVER,
            "@BTN_PRIMARY_PRESS@":  BTN_PRIMARY_PRESS,
            # buttons danger
            "@BTN_DANGER_BG@":      BTN_DANGER_BG,
            "@BTN_DANGER_BORDER@":  BTN_DANGER_BORDER,
            "@BTN_DANGER_TEXT@":    BTN_DANGER_TEXT,
            "@BTN_DANGER_HOVER@":   BTN_DANGER_HOVER,
            "@BTN_DANGER_PRESS@":   BTN_DANGER_PRESS,
            # nav
            "@NAV_TEXT_IDLE@":      NAV_TEXT_IDLE,
            "@NAV_TEXT_HOVER@":     NAV_TEXT_HOVER,
            "@NAV_BG_HOVER@":       NAV_BG_HOVER,
            "@NAV_TEXT_ACTIVE@":    NAV_TEXT_ACTIVE,
            "@NAV_BG_ACTIVE@":      NAV_BG_ACTIVE,
            "@NAV_BORDER_ACTIVE@":  NAV_BORDER_ACTIVE,
            # typography
            "@TEXT_TITLE@":         TEXT_TITLE,
            "@TEXT_BODY@":          TEXT_BODY,
            "@TEXT_PLACEHOLDER@":   TEXT_PLACEHOLDER,
            "@TEXT_TERMINAL@":      TEXT_TERMINAL,
            # data type colors
            "@TEXT_IP@":            TEXT_IP,
            "@TEXT_PORT@":          TEXT_PORT,
            "@TEXT_OK@":            TEXT_OK,
            "@TEXT_ALERT@":         TEXT_ALERT,
            "@TEXT_HANDLE@":        TEXT_HANDLE,
            "@TEXT_MUTED@":         TEXT_MUTED,
            # scrollbar
            "@SCROLLBAR_BG@":       SCROLLBAR_BG,
            "@SCROLLBAR_HANDLE@":   SCROLLBAR_HANDLE,
            # fonts & assets
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