__author__ = "Yuval Malkan"

import logging
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame,
    QScrollArea, QStackedWidget, QDialog, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTime, QTimer
from PyQt6.QtGui import QFont, QCursor, QColor

from Pages.ui.uiConstants import (
    FONT_MONO, FONT_TITLE, load_stylesheet, WINDOW_BG, CARD_BG,
    CARD_BORDER, TEXT_OK, TEXT_MUTED, TEXT_BODY, TEXT_ALERT
)
from Pages.ui.uiElements import GlowInput, GlowingButton
from Pages.logic.RoomsLogic import ChatBackend


class UserSearchItem(QPushButton):
    user_clicked = pyqtSignal(str)

    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.username = username
        self.setFixedHeight(50)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; 
                border: none;
                border-bottom: 1px solid {CARD_BORDER}; 
                text-align: left;
            }} 
            QPushButton:hover {{ 
                background: rgba(132, 160, 198, 0.1); 
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(15, 0, 15, 0)

        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {TEXT_OK}; font-size: 10px; background: transparent;")
        status_dot.setFixedWidth(15)

        name_lbl = QLabel(username)
        name_lbl.setFont(QFont(FONT_MONO, 11))
        name_lbl.setStyleSheet(f"color: {TEXT_BODY}; border: none; background: transparent;")

        status_text = QLabel("ONLINE")
        status_text.setFont(QFont(FONT_MONO, 8))
        status_text.setStyleSheet(f"color: {TEXT_MUTED}; border: none; background: transparent;")

        lay.addWidget(status_dot)
        lay.addWidget(name_lbl)
        lay.addStretch()
        lay.addWidget(status_text)

        self.clicked.connect(self._emit_user)

    def _emit_user(self):
        self.user_clicked.emit(self.username)


class BaseModal(QDialog):
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(350, 200)

        self.card = QFrame(self)
        self.card.setFixedSize(350, 200)
        self.card.setStyleSheet(
            f"QFrame {{ background-color: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 12px; }}")

        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.card.setGraphicsEffect(shadow)

        self.lay = QVBoxLayout(self.card)
        self.lay.setContentsMargins(25, 25, 25, 25)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont(FONT_TITLE, 12, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {TEXT_BODY}; border: none;")

        msg_lbl = QLabel(message)
        msg_lbl.setFont(QFont(FONT_MONO, 10))
        msg_lbl.setStyleSheet(f"color: {TEXT_MUTED}; border: none;")
        msg_lbl.setWordWrap(True)

        self.lay.addWidget(title_lbl)
        self.lay.addWidget(msg_lbl)
        self.lay.addStretch()

        self.btn_layout = QHBoxLayout()
        self.lay.addLayout(self.btn_layout)


class RequestModal(BaseModal):
    def __init__(self, target_user: str, parent=None):
        super().__init__("Initiate Link", f"Request a secure 1-on-1 session with {target_user}?", parent)
        cancel_btn = GlowingButton("CANCEL", variant="danger")
        cancel_btn.clicked.connect(self.reject)
        send_btn = GlowingButton("SEND REQUEST", variant="primary")
        send_btn.clicked.connect(self.accept)
        self.btn_layout.addWidget(cancel_btn)
        self.btn_layout.addWidget(send_btn)


class IncomingModal(BaseModal):
    def __init__(self, sender_user: str, parent=None):
        super().__init__("Incoming Transmission", f"Incoming secure chat request from {sender_user}.", parent)
        decline_btn = GlowingButton("DECLINE", variant="danger")
        decline_btn.clicked.connect(self.reject)
        accept_btn = GlowingButton("APPROVE", variant="primary")
        accept_btn.clicked.connect(self.accept)
        self.btn_layout.addWidget(decline_btn)
        self.btn_layout.addWidget(accept_btn)


class DiscoveryView(QWidget):
    request_chat = pyqtSignal(str)
    modal_opened = pyqtSignal()
    modal_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(450, 500)
        self.card.setStyleSheet(
            f"QFrame {{ background: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 16px; }}")

        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(30, 30, 30, 30)
        card_lay.setSpacing(20)

        header = QLabel("// SECURE DIRECTORY")
        header.setFont(QFont(FONT_TITLE, 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {TEXT_BODY}; letter-spacing: 2px; border: none;")
        card_lay.addWidget(header)

        self.search_input = GlowInput("Search active nodes...")
        card_lay.addWidget(self.search_input)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")

        self.user_container = QWidget()
        self.user_container.setStyleSheet("background: transparent;")
        self.user_layout = QVBoxLayout(self.user_container)
        self.user_layout.setContentsMargins(0, 0, 0, 0)
        self.user_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.user_container)
        card_lay.addWidget(self.scroll)
        main_layout.addWidget(self.card)

    def update_users(self, online_users: list):
        current_users = []
        for i in range(self.user_layout.count()):
            widget = self.user_layout.itemAt(i).widget()
            if isinstance(widget, UserSearchItem):
                current_users.append(widget.username)

        if current_users == online_users:
            return

        while self.user_layout.count():
            item = self.user_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for u in online_users:
            item = UserSearchItem(u)
            item.user_clicked.connect(self._on_user_clicked)
            self.user_layout.addWidget(item)

    def _on_user_clicked(self, username: str):
        self.modal_opened.emit()
        self._req_modal = RequestModal(username, self)

        if self._req_modal.exec() == QDialog.DialogCode.Accepted:
            self.request_chat.emit(username)

        self._req_modal.deleteLater()
        self.modal_closed.emit()


class EphemeralChatView(QFrame):
    message_sent = pyqtSignal(str)
    session_ended = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatView")
        self.setStyleSheet(f"background: {WINDOW_BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header = QFrame()
        self._header.setFixedHeight(65)
        self._header.setStyleSheet(f"background: {CARD_BG}; border-bottom: 1px solid {CARD_BORDER};")

        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(25, 0, 25, 0)

        self._peer_label = QLabel("// PEER_NAME")
        self._peer_label.setFont(QFont(FONT_MONO, 12, QFont.Weight.Bold))
        self._peer_label.setStyleSheet(f"color: {TEXT_BODY}; border: none;")

        secure_lbl = QLabel(" E2E SECURE ")
        secure_lbl.setFont(QFont(FONT_MONO, 8))
        secure_lbl.setStyleSheet(f"color: {TEXT_OK}; border: 1px solid {TEXT_OK}; border-radius: 4px;")

        self._end_btn = QPushButton("END SESSION ✕")
        self._end_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._end_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {TEXT_ALERT}; border: 1px solid {TEXT_ALERT}; border-radius: 6px; padding: 6px 12px; font-weight: bold; }}")
        self._end_btn.clicked.connect(self.session_ended.emit)

        h_lay.addWidget(self._peer_label)
        h_lay.addSpacing(15)
        h_lay.addWidget(secure_lbl)
        h_lay.addStretch()
        h_lay.addWidget(self._end_btn)

        self._msg_scroll = QScrollArea()
        self._msg_scroll.setWidgetResizable(True)
        self._msg_scroll.setStyleSheet(f"border: none; background: {WINDOW_BG};")

        self._msg_container = QWidget()
        self._msg_container.setStyleSheet("background: transparent;")
        self._msg_lay = QVBoxLayout(self._msg_container)
        self._msg_lay.setContentsMargins(20, 20, 20, 20)
        self._msg_lay.setSpacing(15)
        self._msg_lay.addStretch()
        self._msg_scroll.setWidget(self._msg_container)

        input_bar = QFrame()
        input_bar.setFixedHeight(80)
        input_bar.setStyleSheet(f"background: {CARD_BG}; border-top: 1px solid {CARD_BORDER};")

        i_lay = QHBoxLayout(input_bar)
        i_lay.setContentsMargins(20, 15, 20, 15)
        i_lay.setSpacing(15)

        self._input = GlowInput("// Encrypting payload...")
        self._input.returnPressed.connect(self._send)

        self._send_btn = GlowingButton("TRANSMIT ▶", variant="primary")
        self._send_btn.setFixedWidth(130)
        self._send_btn.clicked.connect(self._send)

        i_lay.addWidget(self._input)
        i_lay.addWidget(self._send_btn)

        root.addWidget(self._header)
        root.addWidget(self._msg_scroll)
        root.addWidget(input_bar)

    def set_peer(self, username: str):
        self._peer_label.setText(f"// {username.upper()}")

    def clear_chat(self):
        while self._msg_lay.count() > 1:
            item = self._msg_lay.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

    def add_message(self, sender: str, text: str, is_mine: bool = False, timestamp: str = None):
        if not timestamp:
            timestamp = QTime.currentTime().toString("HH:mm")

        bubble = QFrame()
        b_lay = QVBoxLayout(bubble)
        b_lay.setContentsMargins(0, 0, 0, 0)

        header = QLabel(f"{sender}  ·  {timestamp}")
        header.setFont(QFont(FONT_MONO, 8))
        header.setStyleSheet(f"color: {TEXT_OK if is_mine else TEXT_MUTED};")

        msg = QLabel(text)
        msg.setFont(QFont(FONT_MONO, 12))
        msg.setWordWrap(True)
        msg.setMaximumWidth(600)

        bg_color = WINDOW_BG if is_mine else CARD_BG
        border_color = CARD_BORDER if is_mine else "transparent"
        msg.setStyleSheet(
            f"background: {bg_color}; color: {TEXT_BODY}; border: 1px solid {border_color}; border-radius: 12px; padding: 12px 16px;")

        b_lay.addWidget(header)
        b_lay.addWidget(msg)

        outer_lay = QHBoxLayout()
        if is_mine: outer_lay.addStretch()
        outer_lay.addWidget(bubble)
        if not is_mine: outer_lay.addStretch()

        wrapper = QWidget()
        wrapper.setLayout(outer_lay)
        self._msg_lay.addWidget(wrapper)

        QTimer.singleShot(50, lambda: self._msg_scroll.verticalScrollBar().setValue(
            self._msg_scroll.verticalScrollBar().maximum()
        ))

    def _send(self):
        text = self._input.text().strip()
        if text:
            self.add_message("YOU", text, is_mine=True)
            self.message_sent.emit(text)
            self._input.clear()


class RoomsPanel(QWidget):
    def __init__(self, backend: ChatBackend, parent=None):
        super().__init__(parent)
        self.setObjectName("RoomsPanel")
        self.backend = backend

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()

        self.discovery_view = DiscoveryView()
        self.chat_view = EphemeralChatView()

        self.stack.addWidget(self.discovery_view)
        self.stack.addWidget(self.chat_view)
        layout.addWidget(self.stack)

        # Basic signal connections
        self.discovery_view.request_chat.connect(self.backend.send_chat_request)
        self.discovery_view.modal_opened.connect(self._pause_polling)
        self.discovery_view.modal_closed.connect(self._resume_polling)

        self.chat_view.message_sent.connect(self.backend.send_message)
        self.chat_view.session_ended.connect(self._end_session)

        # Connect UI logic to Backend responses
        self.backend.online_users_received.connect(self._update_discovery_list)
        self.backend.incoming_request.connect(self._handle_incoming_request)
        self.backend.request_accepted.connect(self._start_session_ui)
        self.backend.message_received.connect(self._on_message_received)
        self.backend.session_ended.connect(self._on_peer_ended_session)

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._poll_users_if_active)
        self.poll_timer.start(5000)

        self.backend.fetch_online_users()

    def _poll_users_if_active(self):
        if self.stack.currentIndex() == 0:
            self.backend.fetch_online_users()

    def _pause_polling(self):
        self.poll_timer.stop()

    def _resume_polling(self):
        if self.stack.currentIndex() == 0:
            self._poll_users_if_active()
            self.poll_timer.start(5000)

    def _update_discovery_list(self, users: list):
        filtered = [u for u in users if u != self.backend.username]
        self.discovery_view.update_users(filtered)

    def _handle_incoming_request(self, sender: str):
        if self.stack.currentIndex() == 0:
            self._pause_polling()
            self._inc_modal = IncomingModal(sender, self)

            if self._inc_modal.exec() == QDialog.DialogCode.Accepted:
                self.backend.accept_chat(sender)
                self._start_session_ui(sender)
            else:
                self.backend.decline_chat(sender)
                self._resume_polling()

            self._inc_modal.deleteLater()

    def _start_session_ui(self, peer: str):
        self.chat_view.clear_chat()
        self.chat_view.set_peer(peer)
        self.chat_view.add_message("SYSTEM", f"Encrypted 1-on-1 session established with {peer}.", is_mine=False)
        self.stack.setCurrentIndex(1)
        self._pause_polling()

    def _on_message_received(self, msg: dict):
        if self.stack.currentIndex() == 1 and msg["sender"] == self.backend.active_peer:
            self.chat_view.add_message(msg["sender"], msg["text"], is_mine=False, timestamp=msg["timestamp"])

    def _on_peer_ended_session(self, peer: str):
        if self.stack.currentIndex() == 1:
            self.chat_view.add_message("SYSTEM", f"Peer terminated the connection.", is_mine=False)

    def _end_session(self):
        self.backend.end_session()
        self.chat_view.clear_chat()
        self.stack.setCurrentIndex(0)
        self._resume_polling()