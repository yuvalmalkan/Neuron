__author__ = "Yuval Malkan"


from Pages.ui.uiConstants import *
from Pages.ui.uiElements import GlowInput, GlowingButton, Card
from Pages.logic.NetworkMain import ScanThread

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QSizePolicy, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCursor, QTextCharFormat





# ──────────────────────────────────────────
#  SMALL HELPER WIDGETS
# ──────────────────────────────────────────

class _Divider(QFrame):
    """Thin horizontal rule that matches the card border color."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet(f"color: {CARD_BORDER}; background: {CARD_BORDER}; max-height: 1px;")


class _SectionLabel(QLabel):
    """Small all-caps section header inside a result block."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont(FONT_MONO, 8))
        self.setStyleSheet(f"color: {TEXT_PLACEHOLDER}; letter-spacing: 2px; background: transparent; border: none;")


class _KVLabel(QLabel):
    """Key/value text inside a result block."""
    def __init__(self, text, is_key=False, parent=None):
        super().__init__(text, parent)
        color = TEXT_PLACEHOLDER if is_key else TEXT_TITLE
        self.setFont(QFont(FONT_MONO, 10))
        self.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        self.setWordWrap(True)


class _Badge(QLabel):
    """Colored pill badge for port states / severity."""
    COLORS = {
        "OPEN":   ("#BB0000", "#FF4444"),
        "CLOSED": ("#1a1a1a", "#333333"),
        "FOUND":  ("#003300", "#22AA22"),
        "INFO":   ("#001830", "#1F6FEB"),
    }

    def __init__(self, text, kind="INFO", parent=None):
        super().__init__(text, parent)
        bg, fg = self.COLORS.get(kind, self.COLORS["INFO"])
        self.setFont(QFont(FONT_MONO, 8))
        self.setStyleSheet(
            f"background: {bg}; color: {fg}; border: 1px solid {fg}44;"
            f"border-radius: 3px; padding: 1px 6px; letter-spacing: 1px;"
        )
        self.setFixedHeight(18)


# ──────────────────────────────────────────
#  RESULT BLOCK WIDGETS
# ──────────────────────────────────────────

class _ResultBlock(QFrame):
    """
    Base card for a single module's result.
    Left accent border color signals status.
    """
    def __init__(self, accent=BTN_PRIMARY_BORDER, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"background: {CARD_BG};"
            f"border: 1px solid {CARD_BORDER};"
            f"border-left: 3px solid {accent};"
            f"border-radius: 0 8px 8px 0;"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 10, 14, 10)
        self._layout.setSpacing(6)

    def add_header(self, text: str):
        lbl = _SectionLabel(text)
        self._layout.addWidget(lbl)
        self._layout.addWidget(_Divider())

    def inner_layout(self) -> QVBoxLayout:
        return self._layout


class IpIntelBlock(_ResultBlock):
    def __init__(self, data: dict, parent=None):
        super().__init__(accent=TEXT_TERMINAL, parent=parent)
        self.add_header("IP  INTEL")
        grid = QHBoxLayout()
        grid.setSpacing(20)

        keys_col = QVBoxLayout()
        vals_col = QVBoxLayout()

        fields = [
            ("IP",       data.get("ip", "—")),
            ("HOSTNAME", data.get("hostname", "—")),
            ("COUNTRY",  data.get("country", "—")),
            ("CITY",     data.get("city", "—")),
            ("ORG",      data.get("org", "—")),
            ("TIMEZONE", data.get("timezone", "—")),
        ]
        for key, val in fields:
            keys_col.addWidget(_KVLabel(key, is_key=True))
            vals_col.addWidget(_KVLabel(val))

        grid.addLayout(keys_col)
        grid.addLayout(vals_col)
        grid.addStretch()
        self.inner_layout().addLayout(grid)


class PortsBlock(_ResultBlock):
    def __init__(self, ports: list, parent=None):
        open_ports = [p for p in ports if p["state"] == "OPEN"]
        accent = BTN_PRIMARY_BORDER if open_ports else CARD_BORDER
        super().__init__(accent=accent, parent=parent)
        self.add_header(f"PORT  SCAN  —  {len(open_ports)} OPEN")

        # Header row
        hdr = QHBoxLayout()
        for txt, w in [("PORT", 60), ("STATE", 80), ("SERVICE", 120)]:
            l = _KVLabel(txt, is_key=True)
            l.setFixedWidth(w)
            hdr.addWidget(l)
        hdr.addStretch()
        self.inner_layout().addLayout(hdr)
        self.inner_layout().addWidget(_Divider())

        for p in ports:
            if p["state"] == "CLOSED":
                continue   # skip closed ports to keep it clean
            row = QHBoxLayout()
            row.setSpacing(0)

            kind = "OPEN" if p["state"] == "OPEN" else "CLOSED"
            port_lbl = _KVLabel(str(p["port"]))
            port_lbl.setFixedWidth(60)
            state_badge = _Badge(p["state"], kind)

            svc_lbl = _KVLabel(p["service"])
            svc_lbl.setFixedWidth(120)

            row.addWidget(port_lbl)
            row.addWidget(state_badge)
            row.addSpacing(14)
            row.addWidget(svc_lbl)
            row.addStretch()
            self.inner_layout().addLayout(row)


class SubdomainsBlock(_ResultBlock):
    def __init__(self, subs: list, parent=None):
        accent = "#22AA22" if subs else CARD_BORDER
        super().__init__(accent=accent, parent=parent)
        self.add_header(f"SUBDOMAINS  —  {len(subs)} FOUND")

        if not subs:
            self.inner_layout().addWidget(_KVLabel("no subdomains resolved"))
            return

        for s in subs:
            row = QHBoxLayout()
            name = _KVLabel(s["subdomain"])
            ip   = _KVLabel(s["ip"], is_key=True)
            row.addWidget(name)
            row.addStretch()
            row.addWidget(ip)
            self.inner_layout().addLayout(row)
            self.inner_layout().addWidget(_Divider())


class WhoisBlock(_ResultBlock):
    def __init__(self, text: str, parent=None):
        super().__init__(accent=CARD_BORDER, parent=parent)
        self.add_header("WHOIS")
        box = QTextEdit()
        box.setReadOnly(True)
        box.setPlainText(text)
        box.setFont(QFont(FONT_MONO, 9))
        box.setFixedHeight(160)
        box.setStyleSheet(
            f"background: {WINDOW_BG}; color: {TEXT_PLACEHOLDER}; border: none;"
        )
        self.inner_layout().addWidget(box)


# ──────────────────────────────────────────
#  TERMINAL FEED  (streaming log lines)
# ──────────────────────────────────────────

class TerminalFeed(QTextEdit):
    """
    Read-only terminal-style text area.
    Appends colored lines using QTextCharFormat.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont(FONT_MONO, 10))
        self.setMinimumHeight(80)
        self.setMaximumHeight(140)
        self.setStyleSheet(
            f"background: {WINDOW_BG}; color: {TEXT_TERMINAL};"
            f"border: none; border-top: 1px solid {CARD_BORDER};"
            f"padding: 8px 14px;"
        )
        self.setPlaceholderText("// NEURON NETWORK MODULE — READY\n// type a target and press INITIATE SCAN\n")

    def append_line(self, text: str, color: str = TEXT_TERMINAL):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self.toPlainText() == "":
            cursor.insertText("\n")
        cursor.insertText(text, fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()


# ──────────────────────────────────────────
#  MODULE TOGGLE BUTTON
# ──────────────────────────────────────────

class ModuleToggle(GlowingButton):
    """
    Checkable toggle that switches between 'primary' (on) and 'danger' (off)
    variants so it re-uses the QSS you already have.
    """
    def __init__(self, label: str, module_id: str, on: bool = True, parent=None):
        super().__init__(label, variant="primary" if on else "danger", parent=parent)
        self.module_id = module_id
        self.setCheckable(True)
        self.setChecked(on)
        self.setMinimumHeight(32)
        self.setFont(QFont(FONT_MONO, 8))
        self.toggled.connect(self._on_toggle)

    def _on_toggle(self, checked: bool):
        self.setProperty("variant", "primary" if checked else "danger")
        # Force QSS re-evaluation
        self.style().unpolish(self)
        self.style().polish(self)


# ──────────────────────────────────────────
#  SCROLLABLE RESULTS CONTAINER
# ──────────────────────────────────────────

class ResultsContainer(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            f"QScrollArea {{ background: {WINDOW_BG}; border: none; }}"
            f"QScrollBar:vertical {{ background: {SCROLLBAR_BG}; width: 6px; border-radius: 3px; }}"
            f"QScrollBar::handle:vertical {{ background: {SCROLLBAR_HANDLE}; border-radius: 3px; }}"
        )

        self._inner = QWidget()
        self._inner.setStyleSheet(f"background: {WINDOW_BG};")
        self._vbox = QVBoxLayout(self._inner)
        self._vbox.setContentsMargins(0, 0, 8, 0)
        self._vbox.setSpacing(10)
        self._vbox.addStretch()

        self.setWidget(self._inner)

    def add_block(self, widget: QWidget):
        # Insert before the trailing stretch
        idx = self._vbox.count() - 1
        self._vbox.insertWidget(idx, widget)
        # Scroll to bottom after a tick
        QTimer.singleShot(50, lambda: self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        ))

    def clear_blocks(self):
        while self._vbox.count() > 1:   # keep the trailing stretch
            item = self._vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ──────────────────────────────────────────
#  MAIN NETWORK PAGE
# ──────────────────────────────────────────

class NetworkPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("networkPage")
        self._scan_thread: ScanThread | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 16)
        root.setSpacing(16)

        # ── HEADER ──────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("NETWORK")
        title.setFont(QFont(FONT_TITLE, 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_TITLE};")

        self._status_lbl = QLabel("STANDBY")
        self._status_lbl.setFont(QFont(FONT_MONO, 9))
        self._status_lbl.setStyleSheet(f"color: {TEXT_PLACEHOLDER}; letter-spacing: 2px;")

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self._status_lbl)
        root.addLayout(hdr)

        # ── TARGET + SCAN BTN ────────────────────
        target_card = Card()
        tc_layout = QVBoxLayout(target_card)
        tc_layout.setContentsMargins(20, 14, 20, 14)
        tc_layout.setSpacing(12)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        target_prefix = QLabel("TARGET //")
        target_prefix.setFont(QFont(FONT_MONO, 10))
        target_prefix.setStyleSheet(f"color: {TEXT_TERMINAL}; background: transparent; border: none;")

        self._target_input = GlowInput("IP address, domain, or CIDR range...")
        self._target_input.returnPressed.connect(self._on_scan)

        self._scan_btn  = GlowingButton("▶  INITIATE SCAN", "primary")
        self._clear_btn = GlowingButton("✕  CLEAR", "danger")
        self._scan_btn.clicked.connect(self._on_scan)
        self._clear_btn.clicked.connect(self._on_clear)

        input_row.addWidget(target_prefix)
        input_row.addWidget(self._target_input, 1)
        input_row.addWidget(self._scan_btn)
        input_row.addWidget(self._clear_btn)
        tc_layout.addLayout(input_row)

        # ── MODULE TOGGLES ───────────────────────
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(8)

        self._modules = {
            "ip":         ModuleToggle("IP INTEL",    "ip",         on=True),
            "ports":      ModuleToggle("PORT SCAN",   "ports",      on=True),
            "subdomains": ModuleToggle("SUBDOMAINS",  "subdomains", on=True),
            "whois":      ModuleToggle("WHOIS",       "whois",      on=False),
        }
        for btn in self._modules.values():
            toggle_row.addWidget(btn)
        toggle_row.addStretch()

        tc_layout.addLayout(toggle_row)
        root.addWidget(target_card)

        # ── RESULTS AREA ─────────────────────────
        results_label = QLabel("SCAN RESULTS")
        results_label.setFont(QFont(FONT_TITLE, 11))
        results_label.setStyleSheet(f"color: {TEXT_PLACEHOLDER};")
        root.addWidget(results_label)

        self._results = ResultsContainer()
        root.addWidget(self._results, 1)

        # ── TERMINAL FEED ────────────────────────
        self._terminal = TerminalFeed()
        root.addWidget(self._terminal)

    # ── ACTIVE MODULE LIST ───────────────────
    def _active_modules(self) -> list[str]:
        return [mid for mid, btn in self._modules.items() if btn.isChecked()]

    # ── SCAN FLOW ────────────────────────────
    def _on_scan(self):
        target = self._target_input.text().strip()
        if not target:
            self._terminal.append_line("  [!] no target entered", color="#BB0000")
            return

        modules = self._active_modules()
        if not modules:
            self._terminal.append_line("  [!] enable at least one module", color="#BB0000")
            return

        # Clear previous results
        self._results.clear_blocks()
        self._terminal.clear()
        self._set_scanning(True)

        self._scan_thread = ScanThread(target, modules)
        self._scan_thread.log_line.connect(self._on_log)
        self._scan_thread.ip_done.connect(self._on_ip_done)
        self._scan_thread.ports_done.connect(self._on_ports_done)
        self._scan_thread.whois_done.connect(self._on_whois_done)
        self._scan_thread.subdomains_done.connect(self._on_subdomains_done)
        self._scan_thread.scan_complete.connect(self._on_scan_complete)
        self._scan_thread.start()

    def _on_clear(self):
        self._target_input.clear()
        self._results.clear_blocks()
        self._terminal.clear()
        self._set_scanning(False)

    def _set_scanning(self, active: bool):
        self._scan_btn.setEnabled(not active)
        self._status_lbl.setText("SCANNING..." if active else "STANDBY")
        color = "#BB0000" if active else TEXT_PLACEHOLDER
        self._status_lbl.setStyleSheet(f"color: {color}; letter-spacing: 2px;")

    # ── SIGNAL HANDLERS ──────────────────────
    def _on_log(self, line: str):
        self._terminal.append_line(line)

    def _on_ip_done(self, data: dict):
        self._results.add_block(IpIntelBlock(data))

    def _on_ports_done(self, ports: list):
        self._results.add_block(PortsBlock(ports))

    def _on_whois_done(self, text: str):
        self._results.add_block(WhoisBlock(text))

    def _on_subdomains_done(self, subs: list):
        self._results.add_block(SubdomainsBlock(subs))

    def _on_scan_complete(self, elapsed: float):
        self._set_scanning(False)
        self._terminal.append_line(
            f"  [ DONE ]  completed in {elapsed:.1f}s", color="#22AA22"
        )
