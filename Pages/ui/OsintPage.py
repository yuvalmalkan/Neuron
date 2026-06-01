__author__ = "Yuval Malkan"

import sys
import threading
import logging
import Client
from Constants import CMD_OSINT_USCAN, CMD_OSINT_ESCAN, CMD_OSINT_PSCAN
from Pages.ui.uiConstants import *
from Pages.ui.uiElements import NavButton
from Pages.ui.RoomsPage import RoomsPanel
from Pages.ui.NetworkPage import NetworkPage
from Pages.logic.RoomsLogic import ChatBackend
from Pages.logic.OsintLogic import parse_target_input, build_target_summary, format_osint_results, generate_ai_summary

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QStackedWidget, QSizePolicy, QPlainTextEdit,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QKeyEvent
import SessionManager



class UserBubble(QWidget):
    """right aligned bubble, what the user typed."""
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
    """left aligned system result, plain terminal text."""
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
    def __init__(self, label: str = "scanning", parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 2, 80, 2)

        self._label = label
        self._lbl = QLabel(label)
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
        self._lbl.setText(self._label + "." * self._dots)

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

        self._full_text = text
        self._index = 0
        self._BATCH = 20  # characters per tick

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._type_next)
        self._timer.start(8)

    def _type_next(self):
        if self._index < len(self._full_text):
            self._index = min(self._index + self._BATCH, len(self._full_text))
            self._lbl.setText(self._full_text[:self._index])
        else:
            self._timer.stop()

    def stop(self):
        self._timer.stop()
        self._lbl.setText(self._full_text)



#input bar
class _TextEdit(QPlainTextEdit):
    """enter = submit, Shift+Enter = newline."""
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


class AiSummaryBubble(QWidget):
    """AI-generated intelligence summary"""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 2, 80, 2)

        wrapper = QFrame()
        wrapper.setStyleSheet(f"""
            QFrame {{
                background: {CARD_BG};
                border: 1px solid {TEXT_TITLE};
                border-radius: 10px;
                padding: 0px;
            }}
        """)
        inner = QVBoxLayout(wrapper)
        inner.setContentsMargins(14, 10, 14, 10)
        inner.setSpacing(6)

        header = QLabel("NEURON'S ARTIFICIAL INTELLIGENCE SUMMARY")
        header.setFont(QFont(FONT_MONO, 11, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {TEXT_TITLE}; background: transparent; border: none;")
        inner.addWidget(header)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {TEXT_TITLE}; background: {TEXT_TITLE}; border: none; max-height: 1px;")
        inner.addWidget(divider)

        body = QLabel(text)
        body.setWordWrap(True)
        body.setFont(QFont(FONT_MONO, 14))
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        body.setStyleSheet(f"color: {TEXT_BODY}; background: transparent; border: none;")
        body.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        inner.addWidget(body)

        row.addWidget(wrapper)
        row.addStretch()


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
    results_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    ai_summary_ready = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("osintDashboard")
        self._typing: TypingIndicator | None = None
        self._ai_typing: TypingIndicator | None = None
        self._listener_thread = None
        self._build_ui()


        self.results_ready.connect(self._on_results_ready, Qt.ConnectionType.QueuedConnection)
        self.error_occurred.connect(self._on_error, Qt.ConnectionType.QueuedConnection)
        self.ai_summary_ready.connect(self._on_ai_summary_ready, Qt.ConnectionType.QueuedConnection)

    def _on_results_ready(self, result_text: str):
        self._hide_typing()
        self._add(SystemBubble(result_text))
        self._bar.set_enabled(True)

        threading.Thread(
            target=self._run_ai_summary,
            args=(result_text,),
            daemon=True
        ).start()
        self._show_ai_typing()

    def _on_error(self, error_msg: str):
        self._hide_typing()
        self._hide_ai_typing()
        self._add(SystemBubble(f"Error: {error_msg}"))
        self._bar.set_enabled(True)

    def _run_ai_summary(self, raw_results: str):
        summary = generate_ai_summary(raw_results)
        self.ai_summary_ready.emit(summary)

    def _on_ai_summary_ready(self, summary_text: str):
        self._hide_ai_typing()
        self._add(AiSummaryBubble(summary_text))

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        main_wrapper = QHBoxLayout()
        main_wrapper.addStretch()

        content_container = QWidget()
        content_container.setFixedWidth(1000)
        content_container.setMaximumWidth(1000)
        content_container.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

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

        username = SessionManager.get_username()
        self._add(WelcomeBubble(f"Welcome Back {username}!"))

        self._scroll.setWidget(self._container)
        content_layout.addWidget(self._scroll, 1)

        main_wrapper.addWidget(content_container)
        main_wrapper.addStretch()

        root.addLayout(main_wrapper, 1)

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

    def _on_submit(self, raw: str):
        from Constants import CMD_OSINT_USCAN, CMD_OSINT_ESCAN, CMD_OSINT_PSCAN

        self._add(UserBubble(raw))
        self._bar.set_enabled(False)

        fields = parse_target_input(raw)

        if not any(fields.get(k) for k in ("phone", "email", "username", "name")):
            self._add(AnimatedSystemBubble("Please enter at least one of: phone, email, @username, or name."))
            self._bar.set_enabled(True)
            return

        self._add(AnimatedSystemBubble(build_target_summary(fields)))
        self._show_typing()

        has_username = bool(fields.get("username"))
        has_email = bool(fields.get("email"))
        has_phone = bool(fields.get("phone"))
        self._scan_username = fields.get("username")
        self._scan_email = fields.get("email")
        self._scan_phone = fields.get("phone")

        scans = []
        if has_username:
            scans.append(("username", self._scan_username))
        if has_email:
            scans.append(("email", self._scan_email))
        if has_phone:
            scans.append(("phone", self._scan_phone))

        if not scans:
            self._hide_typing()
            self._bar.set_enabled(True)
            return

        self._listener_thread = threading.Thread(
            target=self._launch_all,
            args=(scans,),
            daemon=True
        )
        self._listener_thread.start()

    def _launch_username(self):
        import Client
        from Constants import RESP_OSINT_RESULT, RESP_OSINT_ERROR
        try:
            Client.osint_username_scan(self._scan_username)
            response = Client.receive_osint_response(timeout=180)
            if response.get('response') == RESP_OSINT_RESULT:
                self.results_ready.emit(format_osint_results(response.get('report', {})))
            elif response.get('response') == RESP_OSINT_ERROR:
                self.error_occurred.emit(response.get('message', 'Unknown error'))
            else:
                self.error_occurred.emit("Unexpected response from server")
        except Exception as e:
            logging.error(f"Username scan error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))

    def _launch_email(self):
        import Client
        from Constants import RESP_OSINT_RESULT, RESP_OSINT_ERROR
        try:
            Client.osint_email_scan(self._scan_email)
            response = Client.receive_osint_response(timeout=180)
            if response.get('response') == RESP_OSINT_RESULT:
                self.results_ready.emit(format_osint_results(response.get('report', {})))
            elif response.get('response') == RESP_OSINT_ERROR:
                self.error_occurred.emit(response.get('message', 'Unknown error'))
            else:
                self.error_occurred.emit("Unexpected response from server")
        except Exception as e:
            logging.error(f"Email scan error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))

    def _launch_phone(self):
        import Client
        from Constants import RESP_OSINT_RESULT, RESP_OSINT_ERROR, RESP_OSINT_PHONE_RESULT
        try:
            Client.osint_phone_scan(self._scan_phone)
            response = Client.receive_osint_response(timeout=180)
            if response.get('response') in (RESP_OSINT_RESULT, RESP_OSINT_PHONE_RESULT):
                self.results_ready.emit(format_osint_results(response.get('report', {})))
            elif response.get('response') == RESP_OSINT_ERROR:
                self.error_occurred.emit(response.get('message', 'Unknown error'))
            else:
                self.error_occurred.emit("Unexpected response from server")
        except Exception as e:
            logging.error(f"Phone scan error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))

    def _launch_all(self, scans: list):
        import Client
        from Constants import RESP_OSINT_RESULT, RESP_OSINT_ERROR, RESP_OSINT_PHONE_RESULT

        DIVIDER = "\n" + "═" * 60 + "\n"
        parts = []

        for scan_type, target in scans:
            try:
                logging.debug(f"_launch_all: starting {scan_type} for {target}")
                if scan_type == "username":
                    sock = Client.osint_raw_scan(CMD_OSINT_USCAN, {"target_username": target})
                elif scan_type == "email":
                    sock = Client.osint_raw_scan(CMD_OSINT_ESCAN, {"target_email": target})
                elif scan_type == "phone":
                    sock = Client.osint_raw_scan(CMD_OSINT_PSCAN, {"target_phone": target})
                else:
                    continue

                resp = Client.receive_from_socket(sock, 180)
                logging.debug(f"_launch_all: response={resp.get('response')} for {scan_type}")

                if resp.get('response') in (RESP_OSINT_RESULT, RESP_OSINT_PHONE_RESULT):
                    try:
                        formatted = format_osint_results(resp.get('report', {}))
                        parts.append(formatted)
                        logging.debug(f"_launch_all: formatted {scan_type} OK ({len(formatted)} chars)")
                    except Exception as fmt_err:
                        logging.error(f"_launch_all: format_osint_results crashed for {scan_type}: {fmt_err}", exc_info=True)
                        import json as _json
                        raw_dump = _json.dumps(resp.get('report', {}), indent=2, default=str)
                        parts.append(f"[{scan_type} result formatting error: {fmt_err}]\n\nRaw report:\n{raw_dump}")
                elif resp.get('response') == RESP_OSINT_ERROR:
                    parts.append(f"Error ({scan_type}): {resp.get('message', 'Unknown error')}")
                else:
                    parts.append(f"Unexpected response for {scan_type} scan")
            except Exception as e:
                logging.error(f"_launch_all: {scan_type} scan error: {e}", exc_info=True)
                parts.append(f"Error ({scan_type}): {str(e)}")

        logging.debug(f"_launch_all: complete, {len(parts)} parts, emitting")
        if parts:
            self.results_ready.emit(DIVIDER.join(parts))
        else:
            self.error_occurred.emit("All scans failed")

    def show_results(self, text: str):
        self._hide_typing()
        self._add(SystemBubble(text))
        self._bar.set_enabled(True)

    def _add(self, widget: QWidget):
        self._mlayout.insertWidget(self._mlayout.count() - 1, widget)
        QTimer.singleShot(30, self._safe_scroll)

    def _safe_scroll(self):
        try:
            self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()
            )
        except RuntimeError:
            pass

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

    def _show_ai_typing(self):
        self._hide_ai_typing()
        self._ai_typing = TypingIndicator(label="analyzing")
        self._add(self._ai_typing)

    def _hide_ai_typing(self):
        if self._ai_typing:
            self._ai_typing.stop()
            self._mlayout.removeWidget(self._ai_typing)
            self._ai_typing.deleteLater()
            self._ai_typing = None

    def _listen_worker(self):
        import Client
        from Constants import RESP_OSINT_RESULT, RESP_OSINT_ERROR
        try:
            response = Client.receive_osint_response(timeout=180)
            if response.get('response') == RESP_OSINT_RESULT:
                self.results_ready.emit(format_osint_results(response.get('report', {})))
            elif response.get('response') == RESP_OSINT_ERROR:
                self.error_occurred.emit(response.get('message', 'Unknown error'))
            else:
                self.error_occurred.emit("Unexpected response from server")
        except Exception as e:
            logging.error(f"Listener error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))


#main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neuron")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 780)

        self.username = SessionManager.get_username()

        self.chat_backend = ChatBackend(host=Client.serverIp, port=34401)  # todo change it later to other ip
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

        nav_items = [("", "OSINT"), ("", "ROOMS"), ("", "NETWORK")]
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



if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_application_font()
    app.setStyle("Fusion")
    app.setStyleSheet(load_stylesheet("main"))

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