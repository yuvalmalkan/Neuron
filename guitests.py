import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QFrame, QScrollArea,
    QSizePolicy, QSpacerItem, QGridLayout
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QCursor

# ── Global QSS ────────────────────────────────────────────────────────────────
QSS = """
* {
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
    font-size: 13px;
    color: #c2c0b6;
}

QMainWindow, QWidget#root {
    background: #0f1117;
}

/* ── Sidebar ── */
QWidget#sidebar {
    background: #0c0d10;
    border-right: 1px solid rgba(255,255,255,0.07);
}

QPushButton#nav_btn {
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 8px;
    font-size: 18px;
    color: rgba(255,255,255,0.35);
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
}
QPushButton#nav_btn:hover {
    background: rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.7);
}
QPushButton#nav_btn[active="true"] {
    background: rgba(74,108,247,0.25);
    color: #4a6cf7;
}

QLabel#logo {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4a6cf7,stop:1 #7c3aed);
    border-radius: 8px;
    color: white;
    font-size: 14px;
    font-weight: bold;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    qproperty-alignment: AlignCenter;
}

/* ── Topbar ── */
QWidget#topbar {
    background: #0f1117;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    min-height: 52px;
    max-height: 52px;
}

/* Mode tabs */
QWidget#tab_container {
    background: rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 2px;
}
QPushButton#mode_tab {
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 5px 16px;
    font-size: 12px;
    font-weight: 500;
    color: rgba(255,255,255,0.4);
    min-height: 28px;
}
QPushButton#mode_tab:hover {
    color: rgba(255,255,255,0.7);
}
QPushButton#mode_tab[active="true"] {
    background: #4a6cf7;
    color: white;
}

QLabel#greeting {
    color: rgba(255,255,255,0.4);
    font-size: 12px;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 3px 12px;
}

QLabel#avatar {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4a6cf7,stop:1 #7c3aed);
    border-radius: 14px;
    color: white;
    font-size: 11px;
    font-weight: bold;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    qproperty-alignment: AlignCenter;
}

/* ── Main panels ── */
QWidget#main_area {
    background: #0f1117;
}

QWidget#search_panel {
    background: #0f1117;
}

QWidget#right_panel {
    background: #0f1117;
    border-left: 1px solid rgba(255,255,255,0.07);
    max-width: 280px;
    min-width: 280px;
}

/* ── Search ── */
QLineEdit#search_input {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    color: rgba(255,255,255,0.85);
    selection-background-color: #4a6cf7;
    min-height: 40px;
}
QLineEdit#search_input:focus {
    border: 1px solid #4a6cf7;
    background: rgba(255,255,255,0.05);
}
QLineEdit#search_input::placeholder {
    color: rgba(255,255,255,0.2);
}

QPushButton#scan_btn {
    background: #4a6cf7;
    border: none;
    border-radius: 10px;
    color: white;
    font-size: 12px;
    font-weight: 600;
    padding: 10px 18px;
    min-height: 40px;
}
QPushButton#scan_btn:hover {
    background: #5a7af8;
}
QPushButton#scan_btn:pressed {
    background: #3a5ce6;
}

/* ── Tag pills ── */
QPushButton#tag_btn {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    color: rgba(255,255,255,0.35);
    font-size: 11px;
    padding: 3px 10px;
    min-height: 22px;
}
QPushButton#tag_btn:hover {
    border-color: #4a6cf7;
    color: #4a6cf7;
}

/* ── Result cards ── */
QFrame#result_card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
}

QLabel#section_label {
    color: rgba(255,255,255,0.5);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
}

QLabel#panel_title {
    color: rgba(255,255,255,0.3);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
}

/* ── Stat cards ── */
QFrame#stat_card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
}

QLabel#stat_number {
    font-size: 22px;
    font-weight: 600;
}

QLabel#stat_label {
    color: rgba(255,255,255,0.3);
    font-size: 11px;
}

/* ── Recent items ── */
QWidget#recent_item {
    background: transparent;
    border-radius: 8px;
}
QWidget#recent_item:hover {
    background: rgba(255,255,255,0.04);
}

/* ── AI summary box ── */
QFrame#ai_box {
    background: rgba(74,108,247,0.08);
    border: 1px solid rgba(74,108,247,0.2);
    border-radius: 10px;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: transparent;
    width: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,0.15);
    border-radius: 2px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
"""


def make_label(text, object_name=None, color=None, font_size=None, bold=False, align=Qt.AlignmentFlag.AlignLeft):
    lbl = QLabel(text)
    if object_name:
        lbl.setObjectName(object_name)
    if color:
        lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    if font_size or bold:
        f = lbl.font()
        if font_size:
            f.setPointSize(font_size)
        if bold:
            f.setBold(True)
        lbl.setFont(f)
    lbl.setAlignment(align)
    return lbl


def make_chip(text, color="#4a6cf7", bg_alpha="0.15"):
    chip = QLabel(text)
    chip.setStyleSheet(f"""
        background: rgba(74,108,247,{bg_alpha});
        color: {color};
        border: 1px solid rgba(74,108,247,0.3);
        border-radius: 20px;
        padding: 2px 8px;
        font-size: 11px;
    """)
    chip.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return chip


def make_stat_card(number, label, color):
    card = QFrame()
    card.setObjectName("stat_card")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(12, 12, 12, 12)
    lay.setSpacing(2)

    num = QLabel(number)
    num.setObjectName("stat_number")
    num.setStyleSheet(f"font-size: 22px; font-weight: 600; color: {color}; background: transparent; border: none;")
    lbl = QLabel(label)
    lbl.setObjectName("stat_label")

    lay.addWidget(num)
    lay.addWidget(lbl)
    return card


def make_result_card(icon, section_title, content_widget):
    card = QFrame()
    card.setObjectName("result_card")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(12, 12, 12, 12)
    lay.setSpacing(8)

    header = QHBoxLayout()
    icon_lbl = QLabel(icon)
    icon_lbl.setStyleSheet("font-size: 14px; background: transparent; border: none;")
    icon_lbl.setFixedSize(26, 26)
    title = QLabel(section_title)
    title.setObjectName("section_label")
    header.addWidget(icon_lbl)
    header.addWidget(title)
    header.addStretch()

    lay.addLayout(header)
    lay.addWidget(content_widget)
    return card


class NeuronDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neuron — Intelligence Platform")
        self.setMinimumSize(960, 620)
        self.resize(1100, 680)
        self.setStyleSheet(QSS)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._build_sidebar())

        right_side = QVBoxLayout()
        right_side.setContentsMargins(0, 0, 0, 0)
        right_side.setSpacing(0)
        right_side.addWidget(self._build_topbar())
        right_side.addWidget(self._build_main())

        container = QWidget()
        container.setLayout(right_side)
        main_layout.addWidget(container)

    # ── Sidebar ────────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = QWidget()
        sb.setObjectName("sidebar")
        sb.setFixedWidth(56)

        lay = QVBoxLayout(sb)
        lay.setContentsMargins(8, 12, 8, 12)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        logo = QLabel("N")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(10)

        nav_items = [("🔍", True), ("💬", False), ("🌐", False)]
        for icon, active in nav_items:
            btn = QPushButton(icon)
            btn.setObjectName("nav_btn")
            btn.setProperty("active", str(active).lower())
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        lay.addStretch()

        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("nav_btn")
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        lay.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        avatar = QLabel("יו")
        avatar.setObjectName("avatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignHCenter)

        return sb

    # ── Topbar ─────────────────────────────────────────────────────────────────
    def _build_topbar(self):
        topbar = QWidget()
        topbar.setObjectName("topbar")

        lay = QHBoxLayout(topbar)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(12)

        # Mode tabs
        tab_container = QWidget()
        tab_container.setObjectName("tab_container")
        tab_lay = QHBoxLayout(tab_container)
        tab_lay.setContentsMargins(3, 3, 3, 3)
        tab_lay.setSpacing(2)

        for name, active in [("OSINT", True), ("חדרים", False), ("תקשורת", False)]:
            btn = QPushButton(name)
            btn.setObjectName("mode_tab")
            btn.setProperty("active", str(active).lower())
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            tab_lay.addWidget(btn)

        lay.addWidget(tab_container)
        lay.addStretch()

        greeting = QLabel("שלום, <span style='color:rgba(255,255,255,0.75);font-weight:500'>יובל</span> 👋")
        greeting.setObjectName("greeting")
        greeting.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(greeting)

        avatar = QLabel("יו")
        avatar.setObjectName("avatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(avatar)

        return topbar

    # ── Main content ────────────────────────────────────────────────────────────
    def _build_main(self):
        main = QWidget()
        main.setObjectName("main_area")

        lay = QHBoxLayout(main)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._build_search_panel())
        lay.addWidget(self._build_right_panel())

        return main

    # ── Search panel ────────────────────────────────────────────────────────────
    def _build_search_panel(self):
        panel = QWidget()
        panel.setObjectName("search_panel")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(panel)
        scroll.setStyleSheet("background: #0f1117; border: none;")

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Title
        lay.addWidget(make_label("חיפוש מטרה", "panel_title"))

        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_input")
        self.search_input.setPlaceholderText("שם, אימייל, מספר טלפון, שם משתמש...")
        self.search_input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        scan_btn = QPushButton("הפעל סריקה")
        scan_btn.setObjectName("scan_btn")
        scan_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        scan_btn.setFixedWidth(120)

        search_row.addWidget(self.search_input)
        search_row.addWidget(scan_btn)
        lay.addLayout(search_row)

        # Tags
        tags_row = QHBoxLayout()
        tags_row.setSpacing(6)
        for tag in ["+ שם מלא", "+ אימייל", "+ טלפון", "+ שם משתמש", "+ כתובת IP"]:
            btn = QPushButton(tag)
            btn.setObjectName("tag_btn")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            tags_row.addWidget(btn)
        tags_row.addStretch()
        lay.addLayout(tags_row)

        # Results area
        results_frame = QFrame()
        results_frame.setObjectName("result_card")
        results_lay = QVBoxLayout(results_frame)
        results_lay.setContentsMargins(16, 14, 16, 14)
        results_lay.setSpacing(12)

        # Results header
        header_row = QHBoxLayout()
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color: #22c55e; font-size: 8px; background: transparent; border: none;")
        status_lbl = QLabel("תוצאות ל: ")
        status_lbl.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 12px; background: transparent; border: none;")
        target_lbl = QLabel("Ahmed Al-Rashid")
        target_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px; background: transparent; border: none;")
        export_btn = QPushButton("ייצוא PDF")
        export_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #4a6cf7; font-size: 11px; padding: 0; }
            QPushButton:hover { color: #7a9cf9; }
        """)
        export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        header_row.addWidget(status_dot)
        header_row.addWidget(status_lbl)
        header_row.addWidget(target_lbl)
        header_row.addStretch()
        header_row.addWidget(export_btn)
        results_lay.addLayout(header_row)

        # Social networks card
        social_w = QWidget()
        social_w.setStyleSheet("background: transparent;")
        chips_lay = QHBoxLayout(social_w)
        chips_lay.setContentsMargins(0, 0, 0, 0)
        chips_lay.setSpacing(6)
        for network in ["Facebook ✓", "Instagram ✓", "TikTok ✓", "Telegram ✓"]:
            chips_lay.addWidget(make_chip(network))
        chips_lay.addStretch()
        results_lay.addWidget(make_result_card("📱", "רשתות חברתיות", social_w))

        # Contact card
        contact_w = QWidget()
        contact_w.setStyleSheet("background: transparent;")
        contact_lay = QVBoxLayout(contact_w)
        contact_lay.setContentsMargins(0, 0, 0, 0)
        contact_lay.setSpacing(4)
        for label, val in [("טלפון", "+972-5X-XXX-XXXX"), ("אימייל", "a.rashid@gmail.com")]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 11px; background: transparent; border: none;")
            vl = QLabel(val)
            vl.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 12px; background: transparent; border: none;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(vl)
            contact_lay.addLayout(row)
        results_lay.addWidget(make_result_card("📋", "פרטי קשר", contact_w))

        # Location card
        loc_w = QWidget()
        loc_w.setStyleSheet("background: transparent;")
        loc_lay = QVBoxLayout(loc_w)
        loc_lay.setContentsMargins(0, 0, 0, 0)
        loc_lay.setSpacing(4)
        for label, val in [("אזור", "באר-שבע, הנגב"), ("גיל משוער", "26–30")]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 11px; background: transparent; border: none;")
            vl = QLabel(val)
            vl.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 12px; background: transparent; border: none;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(vl)
            loc_lay.addLayout(row)
        results_lay.addWidget(make_result_card("📍", "מיקום וגיל", loc_w))

        # Bottom hint
        hint = QLabel("סיכום AI · תחביבים · הסקת מסקנות ↓")
        hint.setStyleSheet("color: rgba(255,255,255,0.2); font-size: 11px; background: transparent; border: none;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_lay.addWidget(hint)

        lay.addWidget(results_frame)
        lay.addStretch()

        return scroll

    # ── Right panel ─────────────────────────────────────────────────────────────
    def _build_right_panel(self):
        panel = QWidget()
        panel.setObjectName("right_panel")

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Stats
        lay.addWidget(make_label("סטטיסטיקות", "panel_title"))

        stats_grid = QGridLayout()
        stats_grid.setSpacing(8)
        stats_data = [("47", "סריקות היום", "#4a6cf7"), ("12", "דוחות שמורים", "#22c55e"),
                      ("3",  "חדרים פעילים", "#f59e0b"), ("98%", "אחוז הצלחה", "#e879f9")]
        for i, (num, lbl, color) in enumerate(stats_data):
            stats_grid.addWidget(make_stat_card(num, lbl, color), i // 2, i % 2)
        lay.addLayout(stats_grid)

        # Recent searches
        lay.addWidget(make_label("חיפושים אחרונים", "panel_title"))

        recent_data = [
            ("Ahmed Al-Rashid", "עכשיו", "#4a6cf7"),
            ("user_xyz_123", "14 דק׳", "#22c55e"),
            ("test@example.com", "1 שעה", "#f97316"),
            ("+972-54-000-0000", "אתמול", "#888780"),
        ]
        for name, time, color in recent_data:
            item = QWidget()
            item.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            item_lay = QHBoxLayout(item)
            item_lay.setContentsMargins(8, 6, 8, 6)
            item_lay.setSpacing(10)

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 8px; background: transparent; border: none;")
            dot.setFixedWidth(10)

            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px; background: transparent; border: none;")

            time_lbl = QLabel(time)
            time_lbl.setStyleSheet("color: rgba(255,255,255,0.2); font-size: 11px; background: transparent; border: none;")

            item_lay.addWidget(dot)
            item_lay.addWidget(name_lbl)
            item_lay.addStretch()
            item_lay.addWidget(time_lbl)

            item.setStyleSheet("QWidget { border-radius: 8px; } QWidget:hover { background: rgba(255,255,255,0.04); }")
            lay.addWidget(item)

        lay.addStretch()

        # AI Summary box
        ai_box = QFrame()
        ai_box.setObjectName("ai_box")
        ai_lay = QVBoxLayout(ai_box)
        ai_lay.setContentsMargins(12, 12, 12, 12)
        ai_lay.setSpacing(4)

        ai_title = QLabel("סיכום AI")
        ai_title.setStyleSheet("color: #4a6cf7; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        ai_text = QLabel("המטרה פעילה ברשתות חברתיות מרובות. פוסט אחרון לפני 3 שעות. ניכרת פעילות לילית חריגה.")
        ai_text.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 11px; background: transparent; border: none;")
        ai_text.setWordWrap(True)
        ai_text.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        ai_lay.addWidget(ai_title)
        ai_lay.addWidget(ai_text)
        lay.addWidget(ai_box)

        return panel


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Neuron")

    window = NeuronDashboard()
    window.show()
    sys.exit(app.exec())