__author__ = "Yuval Malkan"

import logging

from uiConstants import FONT_MONO, FONT_TITLE, load_stylesheet
from uiElements import shadow, Card, GlowInput, GlowingButton, NavButton, ResultDisplay
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea,
    QToolButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor


# ─────────────────────────────────────────────────────────────
#  ROOM TAB BUTTON  (horizontal top bar)
# ─────────────────────────────────────────────────────────────
class RoomTabButton(QPushButton):
    def __init__(self, name: str, unread: int = 0, parent=None):
        super().__init__(parent)
        self.room_name = name
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("RoomTabButton")
        self.setFont(QFont(FONT_MONO, 9))
        self.setFixedHeight(36)

        label = f"  {name}  "
        if unread:
            label = f"  {name}  [{unread}]  "
        self.setText(label)


# ─────────────────────────────────────────────────────────────
#  ROOMS TOP BAR
# ─────────────────────────────────────────────────────────────
class RoomsTopBar(QFrame):
    room_selected = pyqtSignal(str)
    create_room   = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RoomsTopBar")
        self.setFixedHeight(48)
        self._buttons: list[RoomTabButton] = []

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(6)

        # scrollable tab strip
        self._scroll = QScrollArea()
        self._scroll.setObjectName("TopBarScroll")
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFixedHeight(40)

        self._tab_container = QWidget()
        self._tab_container.setObjectName("TabContainer")
        self._tab_lay = QHBoxLayout(self._tab_container)
        self._tab_lay.setContentsMargins(0, 0, 0, 0)
        self._tab_lay.setSpacing(6)
        self._tab_lay.addStretch()

        self._scroll.setWidget(self._tab_container)
        lay.addWidget(self._scroll, 1)

        # new room button
        self._new_btn = QToolButton()
        self._new_btn.setObjectName("NewRoomBtn")
        self._new_btn.setText("+  NEW ROOM")
        self._new_btn.setFont(QFont(FONT_MONO, 8))
        self._new_btn.setFixedHeight(30)
        self._new_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._new_btn.clicked.connect(self.create_room.emit)
        lay.addWidget(self._new_btn)

    def add_room(self, name: str, unread: int = 0):
        btn = RoomTabButton(name, unread)
        btn.clicked.connect(lambda _, n=name: self._on_tab_clicked(n))
        # insert before the trailing stretch
        self._tab_lay.insertWidget(self._tab_lay.count() - 1, btn)
        self._buttons.append(btn)

    def _on_tab_clicked(self, name: str):
        for btn in self._buttons:
            btn.setChecked(btn.room_name == name)
        self.room_selected.emit(name)

    def select_first(self):
        if self._buttons:
            self._on_tab_clicked(self._buttons[0].room_name)


# ─────────────────────────────────────────────────────────────
#  MESSAGE BUBBLE
# ─────────────────────────────────────────────────────────────
class MessageBubble(QFrame):
    def __init__(self, sender: str, text: str, time: str,
                 is_mine: bool = False, status: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("MsgBubble")
        self.setProperty("mine", is_mine)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        inner = QVBoxLayout()
        inner.setSpacing(4)

        # sender + time row
        header = QHBoxLayout()
        header.setSpacing(8)
        sender_lbl = QLabel(sender)
        sender_lbl.setObjectName("MsgSender")
        sender_lbl.setProperty("mine", is_mine)
        sender_lbl.setFont(QFont(FONT_MONO, 9))

        time_lbl = QLabel(time)
        time_lbl.setObjectName("MsgTime")
        time_lbl.setFont(QFont(FONT_MONO, 8))

        header.addWidget(sender_lbl)
        header.addWidget(time_lbl)
        header.addStretch()

        # bubble text — larger font, generous padding
        bubble = QLabel(text)
        bubble.setObjectName("BubbleText")
        bubble.setProperty("mine", is_mine)
        bubble.setFont(QFont(FONT_MONO, 13))
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(560)
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        inner.addLayout(header)
        inner.addWidget(bubble)

        if status:
            status_lbl = QLabel(status)
            status_lbl.setObjectName("MsgStatus")
            status_lbl.setFont(QFont(FONT_MONO, 8))
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            inner.addWidget(status_lbl)

        if is_mine:
            outer.addStretch()
        outer.addLayout(inner)
        if not is_mine:
            outer.addStretch()


# ─────────────────────────────────────────────────────────────
#  CHAT VIEW
# ─────────────────────────────────────────────────────────────
class ChatView(QFrame):
    message_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatView")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── chat header: room name + members list ────────────
        self._header = QFrame()
        self._header.setObjectName("ChatHeader")
        self._header.setFixedHeight(58)

        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(20, 0, 20, 0)
        h_lay.setSpacing(0)

        name_block = QVBoxLayout()
        name_block.setSpacing(2)
        name_block.setContentsMargins(0, 0, 0, 0)

        self._room_label = QLabel("// SELECT A ROOM")
        self._room_label.setObjectName("ChatRoomLabel")
        self._room_label.setFont(QFont(FONT_MONO, 11))

        self._members_label = QLabel("")
        self._members_label.setObjectName("MembersLabel")
        self._members_label.setFont(QFont(FONT_MONO, 8))

        name_block.addWidget(self._room_label)
        name_block.addWidget(self._members_label)

        h_lay.addLayout(name_block)
        h_lay.addStretch()

        secure_lbl = QLabel("E2E")
        secure_lbl.setObjectName("SecureTag")
        secure_lbl.setFont(QFont(FONT_MONO, 7))
        secure_lbl.setFixedHeight(18)
        h_lay.addWidget(secure_lbl)

        # ── messages scroll area ─────────────────────────────
        self._msg_scroll = QScrollArea()
        self._msg_scroll.setWidgetResizable(True)
        self._msg_scroll.setObjectName("MsgScroll")
        self._msg_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._msg_container = QWidget()
        self._msg_container.setObjectName("MsgContainer")
        self._msg_lay = QVBoxLayout(self._msg_container)
        self._msg_lay.setContentsMargins(20, 16, 20, 16)
        self._msg_lay.setSpacing(14)
        self._msg_lay.addStretch()

        self._msg_scroll.setWidget(self._msg_container)

        # ── input bar ────────────────────────────────────────
        input_bar = QFrame()
        input_bar.setObjectName("InputBar")
        input_bar.setFixedHeight(70)
        i_lay = QHBoxLayout(input_bar)
        i_lay.setContentsMargins(16, 10, 16, 10)
        i_lay.setSpacing(10)

        self._input = GlowInput("// transmit message...")
        self._input.setObjectName("ChatInput")
        self._input.setFont(QFont(FONT_MONO, 13))
        self._input.returnPressed.connect(self._send)

        self._send_btn = QPushButton("SEND  ▶")
        self._send_btn.setObjectName("SendButton")
        self._send_btn.setFont(QFont(FONT_MONO, 10))
        self._send_btn.setFixedHeight(44)
        self._send_btn.setFixedWidth(110)
        self._send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._send_btn.clicked.connect(self._send)

        i_lay.addWidget(self._input), text, time, is_mine, status)
        self._msg_lay.insertWidget(self._msg_lay.count() - 1, bubble)
        # scroll to bottom after layout settles
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self._msg_scroll.verticalScrollBar().setValue(
            self._msg_scroll.verticalScrollBar().maximum()
        ))

    def _send(self):
        text = self._input.text().strip()
        if text:
            self.message_sent.emit(text)
            self._input.clear()


# ─────────────────────────────────────────────────────────────
#  ROOMS PANEL  (top-level, drop into QStackedWidget)
# ─────────────────────────────────────────────────────────────
class RoomsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RoomsPanel")

        rooms_qss = load_stylesheet("rooms")
        if rooms_qss:
            self.setStyleSheet(rooms_qss)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._top_bar = RoomsTopBar()
        self._chat    = ChatView()

        root.addWidget(self._top_bar)
        root.addWidget(self._chat, 1)

        self._top_bar.room_selected.connect(self._on_room_selected)
        self._top_bar.create_room.connect(self._on_create_room)
        self._chat.message_sent.connect(self._on_message_sent)

        self._seed_demo()

    # ── demo seed ────────────────────────────────────────────
    def _seed_demo(self):
        self._top_bar.add_room("ALPHA TEAM", unread=3)
        self._top_bar.add_room("SURVEILLANCE")
        self._top_bar.add_room("FIELD DEBRIEF", unread=1)
        self._top_bar.add_room("INTEL REVIEW")
        self._top_bar.select_first()

        self._chat.set_members([
            {"name": "Y.MALKAN"},
            {"name": "R.COHEN"},
            {"name": "A.LEVY"},
            {"name": "D.BEN-ARI"},
        ])
        self._chat.add_message(
            "Y.MALKAN", "Phone OSINT complete. Target located in TLV district.", "09:42")
        self._chat.add_message(
            "R.COHEN", "Confirmed. Cross-referencing with account scan now.", "09:45")
        self._chat.add_message(
            "YOU", "Running username scan across platforms. ETA 2 min.",
            "09:51", is_mine=True, status="DELIVERED · READ BY 2")

    # ── slots ────────────────────────────────────────────────
    def _on_room_selected(self, name: str):
        self._chat.set_room(name)

    def _on_create_room(self):
        logging.debug("[RoomsPanel] Create room triggered")

    def _on_message_sent(self, text: str):
        from PyQt6.QtCore import QTime
        t = QTime.currentTime().toString("HH:mm")
        self._chat.add_message("YOU", text, t, is_mine=True, status="SENT")
