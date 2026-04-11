__author__ = "Yuval Malkan"

import sys
import os

# 1. Setup paths so all your local imports (like 'from uiConstants import *') keep working natively
root_dir = os.path.dirname(os.path.abspath(__file__))
ui_dir = os.path.join(root_dir, "Pages", "ui")
logic_dir = os.path.join(root_dir, "Pages", "logic")

# Add the subdirectories to sys.path so Python knows where to look
if ui_dir not in sys.path:
    sys.path.append(ui_dir)
if logic_dir not in sys.path:
    sys.path.append(logic_dir)

# 2. Now we can safely import everything
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

# Import your setup constants
from uiConstants import (
    load_application_font, load_stylesheet,
    WINDOW_BG, TEXT_TITLE, CARD_BG, SIDEBAR_BG, INPUT_FOCUS
)

# Import your application windows
from OsintPage import MainWindow
from Login import Login


def main():
    app = QApplication(sys.argv)

    # ── GLOBAL APP SETUP ──
    load_application_font()
    app.setStyle("Fusion")

    # Load and apply global stylesheet
    stylesheet = load_stylesheet("main")
    if stylesheet:
        app.setStyleSheet(stylesheet)

    # Apply global color palette for native widgets
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(WINDOW_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_TITLE))
    palette.setColor(QPalette.ColorRole.Base, QColor(CARD_BG))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(SIDEBAR_BG))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(INPUT_FOCUS))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(WINDOW_BG))
    app.setPalette(palette)

    # ── LAUNCH WINDOW ──
    # You are currently testing the dashboard, so we launch MainWindow.
    # Once you wire up the server backend, you can change this to: window = Login()
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()