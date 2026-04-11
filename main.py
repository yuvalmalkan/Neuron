__author__ = "Yuval Malkan"

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from Pages.ui.uiConstants import (
    load_application_font, load_stylesheet,
    WINDOW_BG, TEXT_TITLE, CARD_BG, SIDEBAR_BG, INPUT_FOCUS
)
from Pages.ui.OsintPage import MainWindow


def main():
    app = QApplication(sys.argv)

    load_application_font()
    app.setStyle("Fusion")

    stylesheet = load_stylesheet("main")
    if stylesheet:
        app.setStyleSheet(stylesheet)

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


if __name__ == "__main__":
    main()