__author__ = "Yuval Malkan"

from uiConstants import FONT_MONO, FONT_TITLE, load_stylesheet
from uiElements import NavButton
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit,
    QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy,
    QToolButton, QSpacerItem,
)
from uiElements import shadow, Card, GlowInput, CyberButton, NavButton, ResultDisplay
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QIcon


# ─────────────────────────────────────────────────────────────
#  MEMBER AVATAR  (small pill shown in chat header)
# ─────────────────────────────────────────────────────────────
class MemberAvatar(QFrame):
    """Compact initials badge with online/offline dot."""

    def __init__(self, initials: str, name: str, online: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("MemberAvatar")
        self.setProperty("online", online)
        self.setFixedSize(28, 36)
        self.setToolTip(name)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        badge = QLabel(initials)
        badge.setObjectName("AvatarBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFont(QFont(FONT_MONO, 7))
        badge.setFixedSize(26, 22)

        dot = QLabel()
        dot.setObjectName("StatusDot")
        dot.setProperty("online", online)
        dot.setFixedSize(6, 6)
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dot_wrap = QHBoxLayout()
        dot_wrap.setContentsMargins(0, 0, 0, 0)
        dot_wrap.addStretch()
        dot_wrap.addWidget(dot)
        dot_wrap.addStretch()

        lay.addWidget(badge)
        lay.addLayout(dot_wrap)


# ─────────────────────────────────────────────────────────────
#  ROOM LIST ITEM  (inside rooms sidebar)
# ─────────────────────────────────────────────────────────────
class RoomItemWidget(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, name: str, preview: str = "", unread: int = 0, parent=None):
        super().__init__(parent)
        self.room_name = name
        self.setObjectName("RoomItem")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(54)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 10, 8)
        lay.setSpacing(3)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)

        name_lbl = QLabel(name)
        name_lbl.setObjectName("RoomName")
        name_lbl.setFont(QFont(FONT_MONO, 9))
        top.addWidget(name_lbl)
        top.addStretch()

        if unread:
            badge = QLabel(str(unread))
            badge.setObjectName("UnreadBadge")
            badge.setFont(QFont(FONT_MONO, 7))
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedSize(18, 14)
            top.addWidget(badge)

        preview_lbl = QLabel(preview)
        preview_lbl.setObjectName("RoomPreview")
        preview_lbl.setFont(QFont(FONT_MONO, 8))

        lay.addLayout(top)
        lay.addWidget(preview_lbl)

    def mousePressEvent(self, event):
        self.clicked.emit(self.room_name)
        super().mousePressEvent(event)

    def set_active(self, active: bool):
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


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

        inner = QVBoxLayout()
        inner.setSpacing(3)

        header = QHBoxLayout()
        sender_lbl = QLabel(sender)
        sender_lbl.setObjectName("MsgSender")
        sender_lbl.setProperty("mine", is_mine)
        sender_lbl.setFont(QFont(FONT_MONO, 8))
        time_lbl = QLabel(time)
        time_lbl.setObjectName("MsgTime")
        time_lbl.setFont(QFont(FONT_MONO, 7))
        header.addWidget(sender_lbl)
        header.addSpacing(6)
        header.addWidget(time_lbl)
        header.addStretch()

        bubble = QLabel(text)
        bubble.setObjectName("BubbleText")
        bubble.setProperty("mine", is_mine)
        bubble.setFont(QFont(FONT_MONO, 10))
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(420)

        inner.addLayout(header)
        inner.addWidget(bubble)

        if status:
            status_lbl = QLabel(status)
            status_lbl.setObjectName("MsgStatus")
            status_lbl.setFont(QFont(FONT_MONO, 7))
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            inner.addWidget(status_lbl)

        if is_mine:
            outer.addStretch()
        outer.addLayout(inner)
        if not is_mine:
            outer.addStretch()


# ─────────────────────────────────────────────────────────────
#  ROOMS SIDEBAR  (collapsible)
# ─────────────────────────────────────────────────────────────
class RoomsSidebar(QFrame):
    room_selected = pyqtSignal(str)
    create_room   = pyqtSignal()
    collapse_toggled = pyqtSignal(bool)  # True = collapsed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RoomsSidebar")
        self.setFixedWidth(200)
        self._collapsed = False
        self._items: list[RoomItemWidget] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # header row
        header = QFrame()
        header.setObjectName("SidebarHeader")
        header.setFixedHeight(44)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(12, 0, 8, 0)

        title = QLabel("CHANNELS")
        title.setObjectName("SidebarTitle")
        title.setFont(QFont(FONT_MONO, 8))

        self._plus_btn = QToolButton()
        self._plus_btn.setObjectName("SidebarIconBtn")
        self._plus_btn.setText("+")
        self._plus_btn.setFont(QFont(FONT_MONO, 13))
        self._plus_btn.setFixedSize(24, 24)
        self._plus_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._plus_btn.clicked.connect(self.create_room.emit)

        self._collapse_btn = QToolButton()
        self._collapse_btn.setObjectName("SidebarIconBtn")
        self._collapse_btn.setText("◀")
        self._collapse_btn.setFont(QFont(FONT_MONO, 9))
        self._collapse_btn.setFixedSize(24, 24)
        self._collapse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._collapse_btn.clicked.connect(self._toggle_collapse)

        h_lay.addWidget(title)
        h_lay.addStretch()
        h_lay.addWidget(self._plus_btn)
        h_lay.addWidget(self._collapse_btn)

        # scrollable room list
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setObjectName("RoomsScroll")

        self._list_container = QWidget()
        self._list_container.setObjectName("RoomsListContainer")
        self._list_lay = QVBoxLayout(self._list_container)
        self._list_lay.setContentsMargins(6, 6, 6, 6)
        self._list_lay.setSpacing(4)
        self._list_lay.addStretch()

        self._scroll.setWidget(self._list_container)

        root.addWidget(header)
        root.addWidget(self._scroll)

    def add_room(self, name: str, preview: str = "", unread: int = 0):
        item = RoomItemWidget(name, preview, unread)
        item.clicked.connect(self._on_room_clicked)
        self._list_lay.insertWidget(self._list_lay.count() - 1, item)
        self._items.append(item)


    def _on_room_clicked(self, name: str):
        for item in self._items:
            item.set_active(item.room_name == name)
        self.room_selected.emit(name)

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        if self._collapsed:
            self.setFixedWidth(50)
            self._collapse_btn.setText("▶")

        else:
            self.setFixedWidth(200)
            self._collapse_btn.setText("◀")
        self.collapse_toggled.emit(self._collapsed)


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

        # ── header ──────────────────────────────────────────
        self._header = QFrame()
        self._header.setObjectName("ChatHeader")
        self._header.setFixedHeight(52)
        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(16, 0, 16, 0)
        h_lay.setSpacing(10)

        self._room_label = QLabel("// SELECT A ROOM")
        self._room_label.setObjectName("ChatRoomLabel")
        self._room_label.setFont(QFont(FONT_MONO, 10))
        h_lay.addWidget(self._room_label)
        h_lay.addStretch()

        # members strip
        self._members_strip = QHBoxLayout()
        self._members_strip.setSpacing(4)
        h_lay.addLayout(self._members_strip)

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
        self._msg_lay.setContentsMargins(16, 12, 16, 12)
        self._msg_lay.setSpacing(10)
        self._msg_lay.addStretch()

        self._msg_scroll.setWidget(self._msg_container)

        # ── input bar ────────────────────────────────────────
        input_bar = QFrame()
        input_bar.setObjectName("InputBar")
        input_bar.setFixedHeight(70)
        i_lay = QHBoxLayout(input_bar)
        i_lay.setContentsMargins(14, 8, 14, 8)
        i_lay.setSpacing(8)

        self._input = GlowInput("input_bar")
        self._input.setObjectName("ChatInput")
        self._input.setPlaceholderText("// transmit message...")
        self._input.setFont(QFont(FONT_MONO, 20))
        self._input.returnPressed.connect(self._send)

        self._send_btn = QPushButton("SEND  ▶")
        self._send_btn.setObjectName("SendButton")
        self._send_btn.setFont(QFont(FONT_MONO, 9))
        self._send_btn.setFixedHeight(36)
        self._send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._send_btn.clicked.connect(self._send)

        i_lay.addWidget(self._input)
        i_lay.addWidget(self._send_btn)

        root.addWidget(self._header)
        root.addWidget(self._msg_scroll)
        root.addWidget(input_bar)

    # public ─────────────────────────────────────────────────
    def set_room(self, name: str):
        self._room_label.setText(f"// {name}")

    def set_members(self, members: list[dict]):
        """members = [{"initials": "YM", "name": "Y.Malkan", "online": True}, ...]"""
        while self._members_strip.count():
            item = self._members_strip.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for m in members:
            av = MemberAvatar(m["initials"], m["name"], m.get("online", True))
            self._members_strip.addWidget(av)
        online = sum(1 for m in members if m.get("online", True))
        count = QLabel(f"{online}/{len(members)}")
        count.setObjectName("MembersCount")
        count.setFont(QFont(FONT_MONO, 7))
        self._members_strip.addWidget(count)

    def add_message(self, sender: str, text: str, time: str,
                    is_mine: bool = False, status: str = ""):
        bubble = MessageBubble(sender, text, time, is_mine, status)
        self._msg_lay.insertWidget(self._msg_lay.count() - 1, bubble)
        # scroll to bottom
        self._msg_scroll.verticalScrollBar().setValue(
            self._msg_scroll.verticalScrollBar().maximum()
        )

    def _send(self):
        text = self._input.text().strip()
        if text:
            self.message_sent.emit(text)
            self._input.clear()


# ─────────────────────────────────────────────────────────────
#  ROOMS PANEL  (top-level, drop into QStackedWidget)
# ─────────────────────────────────────────────────────────────
class RoomsPanel(QWidget):
    """
    Drop-in panel for the main QStackedWidget.
    Emits no signals upward — just swap it in as a page.
    The rooms sidebar is collapsible via the ◀ button.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RoomsPanel")

        # load rooms-specific stylesheet on top of global QSS
        rooms_qss = load_stylesheet("rooms")   # Styles/rooms.qss
        if rooms_qss:
            self.setStyleSheet(rooms_qss)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = RoomsSidebar()
        self._chat    = ChatView()

        root.addWidget(self._sidebar)
        root.addWidget(self._chat)

        # wire signals
        self._sidebar.room_selected.connect(self._on_room_selected)
        self._sidebar.create_room.connect(self._on_create_room)
        self._chat.message_sent.connect(self._on_message_sent)

        # seed demo data
        self._seed_demo()

    # ── demo seed (remove when wiring real backend) ──────────
    def _seed_demo(self):
        self._sidebar.add_room("ALPHA TEAM",     "Running lookup now...", 3)
        self._sidebar.add_room("SURVEILLANCE",   "Target confirmed at loc B.")
        self._sidebar.add_room("FIELD DEBRIEF",  "Awaiting full report...", 1)
        self._sidebar.add_room("INTEL REVIEW",   "Phase 2 complete.")

        self._chat.set_room("ALPHA TEAM")
        self._chat.set_members([
            {"initials": "YM", "name": "Y.MALKAN",  "online": True},
            {"initials": "RC", "name": "R.COHEN",   "online": True},
            {"initials": "AL", "name": "A.LEVY",    "online": False},
            {"initials": "DB", "name": "D.BEN-ARI", "online": True},
        ])
        self._chat.add_message("Y.MALKAN", "Phone OSINT complete. Target located in TLV district.",
                               "09:42")
        self._chat.add_message("R.COHEN",  "Confirmed. Cross-referencing with account scan now.",
                               "09:45")
        self._chat.add_message("YOU", "Running username scan across platforms. ETA 2 min.",
                               "09:51", is_mine=True, status="DELIVERED · READ BY 2")

    # ── slots ────────────────────────────────────────────────
    def _on_room_selected(self, name: str):
        self._chat.set_room(name)

    def _on_create_room(self):
        # TODO: open create-room dialog with email invite
        print("[RoomsPanel] Create room triggered")

    def _on_message_sent(self, text: str):
        from PyQt6.QtCore import QTime
        t = QTime.currentTime().toString("HH:mm")
        self._chat.add_message("YOU", text, t, is_mine=True, status="SENT")
