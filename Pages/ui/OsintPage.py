__author__ = "Yuval Malkan"

import sys

from Pages.ui.uiConstants import *
from Pages.ui.uiElements import NavButton
from Pages.ui.RoomsPage import RoomsPanel
from Pages.ui.NetworkPage import NetworkPage
from Pages.logic.RoomsLogic import ChatBackend
from Pages.logic.OsintLogic import parse_target_input

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QStackedWidget, QSizePolicy, QPlainTextEdit,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QKeyEvent
import SessionManager


# ──────────────────────────────────────────
#  MESSAGE WIDGETS
# ──────────────────────────────────────────

class UserBubble(QWidget):
    """Right-aligned bubble — what the user typed."""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(80, 2, 12, 2)
        row.addStretch()

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont(FONT_MONO, 15))
        lbl.setStyleSheet(f"""
            background: {INPUT_BG};
            color: {TEXT_BODY};
            border: 1px solid {INPUT_BORDER};
            border-radius: 10px;
            padding: 8px 12px;
        """)
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        row.addWidget(lbl)


class SystemBubble(QWidget):
    """Left-aligned system result — plain terminal text."""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 2, 80, 2)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont(FONT_MONO, 15))
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl.setStyleSheet(f"""
            background: {CARD_BG};
            color: {TEXT_TERMINAL};
            border: 1px solid {CARD_BORDER};
            border-radius: 10px;
            padding: 10px 14px;
        """)
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        row.addWidget(lbl)
        row.addStretch()


class TypingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 2, 80, 2)

        self._lbl = QLabel("scanning")
        self._lbl.setFont(QFont(FONT_MONO, 10))
        self._lbl.setStyleSheet(f"""
            background: {CARD_BG};
            color: {TEXT_PLACEHOLDER};
            border: 1px solid {CARD_BORDER};
            border-radius: 10px;
            padding: 10px 14px;
        """)
        row.addWidget(self._lbl)
        row.addStretch()

        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(400)

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        self._lbl.setText("scanning" + "." * self._dots)

    def stop(self):
        self._timer.stop()




class TerminalBubble(QWidget):
    """Plain terminal text — no bubble styling."""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 2, 80, 2)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont(FONT_MONO, 12))
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl.setStyleSheet(f"""
            background: transparent;
            color: {TEXT_TERMINAL};
            border: none;
            padding: 0px;
        """)
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        row.addWidget(lbl)
        row.addStretch()






class AnimatedSystemBubble(QWidget):
    """System response with typing animation"""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 2, 80, 2)

        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        self._lbl.setFont(QFont(FONT_MONO, 15))
        self._lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._lbl.setStyleSheet(f"""
            background: {CARD_BG};
            color: {TEXT_TERMINAL};
            border: 1px solid {CARD_BORDER};
            border-radius: 10px;
            padding: 10px 14px;
        """)
        self._lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        row.addWidget(self._lbl)
        row.addStretch()

        # Typing animation
        self._full_text = text
        self._current_text = ""
        self._index = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._type_next_char)
        self._timer.start(20)  # Speed in milliseconds per character

    def _type_next_char(self):
        if self._index < len(self._full_text):
            self._current_text += self._full_text[self._index]
            self._lbl.setText(self._current_text)
            self._index += 1
        else:
            self._timer.stop()

    def stop(self):
        """Stop animation and show full text."""
        self._timer.stop()
        self._lbl.setText(self._full_text)






#  INPUT BAR

class _TextEdit(QPlainTextEdit):
    """Enter = submit, Shift+Enter = newline."""
    enter_pressed = pyqtSignal()

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(e)
            else:
                self.enter_pressed.emit()
        else:
            super().keyPressEvent(e)


class InputBar(QWidget):
    submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(140)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 0, 16, 14)
        outer.setSpacing(8)

        wrap = QFrame()
        wrap.setStyleSheet(f"""
            QFrame {{
                background: {INPUT_BG};
                border: 1px solid {INPUT_BORDER};
                border-radius: 30px;
            }}
        """)
        inner = QHBoxLayout(wrap)
        inner.setContentsMargins(14, 6, 6, 6)
        inner.setSpacing(6)

        self.field = _TextEdit()
        self.field.setPlaceholderText("Enter Phone, Email, @Username...")
        self.field.setFont(QFont(FONT_MONO, 15))
        self.field.setFixedHeight(80)
        self.field.setStyleSheet(f"""
            QPlainTextEdit {{
                background: transparent;
                border: none;
                color: {TEXT_BODY};
            }}
        """)
        self.field.enter_pressed.connect(self._submit)



        inner.addWidget(self.field)
        outer.addWidget(wrap)

    def _submit(self):
        text = self.field.toPlainText().strip()
        if text:
            self.field.clear()
            self.submitted.emit(text)

    def set_enabled(self, v: bool):
        self.field.setEnabled(v)







class WelcomeBubble(QWidget):
    """Welcome message"""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 2, 80, 2)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont(FONT_MONO, 40, QFont.Weight.Bold))
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl.setStyleSheet(f"""
            background: transparent;
            color: {TEXT_TITLE};
            border: none;
            padding: 0px;
        """)
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        row.addWidget(lbl)
        row.addStretch()








class OsintDashboard(QWidget):
    # Signal for thread-safe updates
    results_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("osintDashboard")
        self._typing: TypingIndicator | None = None
        self._build_ui()

        # Connect signals
        self.results_ready.connect(self._on_results_ready)
        self.error_occurred.connect(self._on_error)

    def _on_results_ready(self, result_text: str):
        """Called when results are ready (thread-safe)"""
        self.show_results(result_text)

    def _on_error(self, error_msg: str):
        """Called when error occurs (thread-safe)"""
        self._hide_typing()
        self._add(AnimatedSystemBubble(f"Error: {error_msg}"))
        self._bar.set_enabled(True)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Main container centered on screen
        main_wrapper = QHBoxLayout()
        main_wrapper.addStretch()

        #centered container
        content_container = QWidget()
        content_container.setFixedWidth(1000)
        content_container.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Scroll area for messages
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {SCROLLBAR_BG};
                width: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {SCROLLBAR_HANDLE};
                border-radius: 2px;
                min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._mlayout = QVBoxLayout(self._container)
        self._mlayout.setContentsMargins(0, 16, 0, 8)
        self._mlayout.setSpacing(8)
        self._mlayout.addStretch()

        #Add welcome message
        username = SessionManager.get_username()
        welcome_text = f"Welcome Back {username}!"
        self._add( WelcomeBubble(welcome_text))

        self._scroll.setWidget(self._container)
        content_layout.addWidget(self._scroll, 1)

        main_wrapper.addWidget(content_container)
        main_wrapper.addStretch()

        root.addLayout(main_wrapper, 1)

        # Floating input bar - bottom center
        floating_container = QWidget()
        floating_container.setStyleSheet("background: transparent;")
        floating_layout = QVBoxLayout(floating_container)
        floating_layout.setContentsMargins(0, 0, 0, 0)
        floating_layout.addStretch()

        input_wrapper = QHBoxLayout()
        input_wrapper.addStretch()

        self._bar = InputBar()
        self._bar.submitted.connect(self._on_submit)
        self._bar.setFixedWidth(800)

        input_wrapper.addWidget(self._bar)
        input_wrapper.addStretch()

        floating_layout.addLayout(input_wrapper)
        floating_layout.addSpacing(50)

        root.addWidget(floating_container, 0)




    #SUBMIT
    def _on_submit(self, raw: str):
        import Client

        self._add(UserBubble(raw))
        self._bar.set_enabled(False)

        fields = parse_target_input(raw)

        if not any(fields.get(k) for k in ("phone", "email", "username", "name")):
            self._add(AnimatedSystemBubble("Please enter at least one of: phone, email, @username, or name."))
            self._bar.set_enabled(True)
            return

        self._add(AnimatedSystemBubble(self._build_summary(fields)))
        self._show_typing()

        # Send scan request to server
        if fields.get("username"):
            username = fields["username"]
            try:
                Client.osint_username_scan(username)
                # Start listening thread for results
                self._start_listening_for_results()
            except Exception as e:
                logging.error(f"Failed to send scan request: {e}")
                self._hide_typing()
                self._add(AnimatedSystemBubble(f"Error: {str(e)}"))
                self._bar.set_enabled(True)

    def _build_summary(self, fields: dict) -> str:
        lines = ["TARGET QUEUED", "─" * 28]
        if fields.get("name"):     lines.append(f"  name      {fields['name']}")
        if fields.get("phone"):    lines.append(f"  phone     {fields['phone']}")
        if fields.get("email"):    lines.append(f"  email     {fields['email']}")
        if fields.get("username"): lines.append(f"  username  @{fields['username']}")
        return "\n".join(lines)








    # ── PUBLIC — called by OsintWorker when results arrive ────────────

    def show_results(self, text: str):
        """
        Call this from your worker signal when the server returns the full result.
        text: plain string (formatted however OsintLogic produces it).
        """
        self._hide_typing()
        self._add(AnimatedSystemBubble(text))
        self._bar.set_enabled(True)

    # ── HELPERS ──────────────────────────────

    def _add(self, widget: QWidget):
        self._mlayout.insertWidget(self._mlayout.count() - 1, widget)
        QTimer.singleShot(30, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))

    def _show_typing(self):
        self._hide_typing()
        self._typing = TypingIndicator()
        self._add(self._typing)

    def _hide_typing(self):
        if self._typing:
            self._typing.stop()
            self._mlayout.removeWidget(self._typing)
            self._typing.deleteLater()
            self._typing = None

    def _start_listening_for_results(self):
        """Listen for OSINT results from server in a separate thread."""
        import Client
        import json
        import threading
        import logging
        from Constants import RESP_OSINT_RESULT, RESP_OSINT_ERROR

        def listen():
            try:
                logging.info("Listening thread started...")
                response = Client.receive_response()
                logging.info(f"Received response: {response}")

                if response.get('response') == RESP_OSINT_RESULT:
                    report = response.get('report', {})
                    result_text = self._format_results(report)
                    self.results_ready.emit(result_text)
                elif response.get('response') == RESP_OSINT_ERROR:
                    error_msg = response.get('message', 'Unknown error')
                    self.error_occurred.emit(error_msg)
                else:
                    logging.warning(f"Unexpected response type: {response.get('response')}")
                    self.error_occurred.emit("Unexpected response from server")

            except Exception as e:
                logging.error(f"Error in listening thread: {e}", exc_info=True)
                self.error_occurred.emit(str(e))

        listener_thread = threading.Thread(target=listen, daemon=True)
        listener_thread.start()

    def _format_results(self, report: dict) -> str:
        """Format OSINT report into readable text with all results and links."""
        username = report.get('query', '?')
        elapsed = report.get('elapsed_seconds', '?')
        summary = report.get('summary', {})

        lines = [
            f"OSINT SCAN COMPLETE — @{username}  ({elapsed}s)",
            "─" * 70,
        ]

        # Telegram section
        tg = summary.get('telegram', {})
        if tg.get('found'):
            lines.append("\n[TELEGRAM]")
            lines.append(f"  ✓ Found")
            lines.append(f"  ID: {tg.get('user_id')}")
            lines.append(f"  Name: {tg.get('name') or 'N/A'}")
            if tg.get('bio'):
                lines.append(f"  Bio: {tg.get('bio')}")
            lines.append(f"  Verified: {'✓ Yes' if tg.get('is_verified') else '✗ No'}")
            lines.append(f"  Premium: {'✓ Yes' if tg.get('is_premium') else '✗ No'}")
            if tg.get('is_scam'):
                lines.append(f"  ⚠ SCAM FLAG")
            if tg.get('is_fake'):
                lines.append(f"  ⚠ FAKE FLAG")
            if tg.get('profile_url'):
                lines.append(f"  Profile: {tg['profile_url']}")
        else:
            lines.append("\n[TELEGRAM]\n  ✗ Not found")

        # All platforms - show EVERY account with link
        platforms = summary.get('platforms', [])
        if platforms:
            lines.append(f"\n[SOCIAL MEDIA & PLATFORMS] ({len(platforms)} total accounts found)")
            lines.append("─" * 70)

            for i, platform in enumerate(platforms, 1):
                site = platform.get('site', 'Unknown')
                url = platform.get('url', 'No URL')
                source = platform.get('source', '?')

                lines.append(f"\n  {i}. {site}")
                lines.append(f"     🔗 {url}")

                # Show details if available
                if platform.get('details'):
                    for key, val in list(platform['details'].items())[:3]:
                        lines.append(f"     • {key}: {val}")
        else:
            lines.append("\n[SOCIAL MEDIA & PLATFORMS]\n  No accounts found")

        lines.append("\n" + "─" * 70)

        return "\n".join(lines)



#MAIN WINDOW
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Neuron")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 780)

        self.username = SessionManager.get_username()

        self.chat_backend = ChatBackend(host="127.0.0.1", port=34401)#todo change it later to other ip
        if self.username:
            self.chat_backend.connect(self.username)

        self._build_layout()

    def _build_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QWidget()
        topbar.setFixedHeight(50)
        topbar.setObjectName("topbar")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(20, 0, 20, 0)
        tl.setSpacing(15)

        logo = QLabel("PROJECT NEURON")
        logo.setFont(QFont(FONT_TITLE, 14, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {TEXT_TITLE};")
        tl.addWidget(logo)
        tl.addSpacing(30)

        self.pages = QStackedWidget()
        self.nav_buttons = []

        nav_items  = [("", "OSINT"), ("", "ROOMS"), ("", "NETWORK")]
        pages_list = [
            OsintDashboard(),
            RoomsPanel(backend=self.chat_backend),
            NetworkPage(),
        ]

        tl.addStretch()
        for (icon, label), page in zip(nav_items, pages_list):
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda _, b=btn: self._switch_page(b))
            tl.addWidget(btn)
            self.pages.addWidget(page)
            self.nav_buttons.append(btn)
            tl.addStretch()

        tl.addSpacing(30)

        user_lbl = QLabel(self.username.upper() if self.username else "USER")
        user_lbl.setFont(QFont(FONT_TITLE, 14, QFont.Weight.Bold))
        user_lbl.setStyleSheet(f"color: {TEXT_TITLE}; padding-right: 10px;")
        tl.addWidget(user_lbl)

        root.addWidget(topbar)
        root.addWidget(self.pages, 1)
        self._switch_page(self.nav_buttons[0])

    def _switch_page(self, clicked_btn: NavButton):
        for i, btn in enumerate(self.nav_buttons):
            active = btn is clicked_btn
            btn.setChecked(active)
            if active:
                self.pages.setCurrentIndex(i)

    def closeEvent(self, event):
        if hasattr(self, "chat_backend"):
            self.chat_backend.disconnect()
        super().closeEvent(event)


# ──────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_application_font()
    app.setStyle("Fusion")
    app.setStyleSheet(load_stylesheet("main"))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(WINDOW_BG))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT_TITLE))
    palette.setColor(QPalette.ColorRole.Base,            QColor(CARD_BG))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(SIDEBAR_BG))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(INPUT_FOCUS))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(WINDOW_BG))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())