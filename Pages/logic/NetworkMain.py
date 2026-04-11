__author__ = "Yuval Malkan"

"""
NetworkMain.py
Backend logic for the Network Mode page.
All scanning operations run in a QThread so the UI never freezes.
Each module emits a signal with its result dict when done.
"""

import socket
import subprocess
import json
import re
from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal, QObject


# ──────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────

def resolve_target(target: str) -> str | None:
    """Resolve a domain to IP. Returns the IP string or None on failure."""
    try:
        return socket.gethostbyname(target.strip())
    except socket.gaierror:
        return None


def is_ip(target: str) -> bool:
    parts = target.strip().split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


# ──────────────────────────────────────────
#  INDIVIDUAL MODULE WORKERS
# ──────────────────────────────────────────

class IpIntelWorker(QObject):
    """Uses socket + ipinfo.io (no API key needed for basic info)."""
    finished = pyqtSignal(dict)   # emits result dict
    error    = pyqtSignal(str)

    def __init__(self, target: str):
        super().__init__()
        self.target = target

    def run(self):
        try:
            import urllib.request
            ip = resolve_target(self.target)
            if not ip:
                self.error.emit(f"Could not resolve: {self.target}")
                return

            url = f"https://ipinfo.io/{ip}/json"
            with urllib.request.urlopen(url, timeout=6) as resp:
                data = json.loads(resp.read().decode())

            result = {
                "ip":       data.get("ip", ip),
                "hostname": data.get("hostname", "N/A"),
                "city":     data.get("city", "N/A"),
                "country":  data.get("country", "N/A"),
                "org":      data.get("org", "N/A"),
                "timezone": data.get("timezone", "N/A"),
            }
            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))


class PortScanWorker(QObject):
    """Fast TCP connect scan on common ports."""
    finished = pyqtSignal(list)   # list of dicts: {port, state, service}
    error    = pyqtSignal(str)

    COMMON_PORTS = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
        443: "HTTPS", 445: "SMB", 3306: "MySQL", 3389: "RDP",
        5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP-ALT",
        8443: "HTTPS-ALT", 27017: "MongoDB",
    }

    def __init__(self, target: str):
        super().__init__()
        self.target = target

    def run(self):
        try:
            ip = resolve_target(self.target) or self.target
            results = []

            for port, service in self.COMMON_PORTS.items():
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                state = "OPEN" if sock.connect_ex((ip, port)) == 0 else "CLOSED"
                sock.close()
                results.append({"port": port, "state": state, "service": service})

            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class WhoisWorker(QObject):
    """Runs system whois and returns raw cleaned text."""
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, target: str):
        super().__init__()
        self.target = target

    def run(self):
        try:
            proc = subprocess.run(
                ["whois", self.target.strip()],
                capture_output=True, text=True, timeout=10
            )
            # Strip comment lines and blank lines for cleaner output
            lines = [
                l for l in proc.stdout.splitlines()
                if l.strip() and not l.strip().startswith("%")
                and not l.strip().startswith("#")
            ]
            self.finished.emit("\n".join(lines[:40]))  # cap at 40 lines
        except Exception as e:
            self.error.emit(str(e))


class SubdomainWorker(QObject):
    """
    Tries a wordlist of common subdomains via DNS resolution.
    Lightweight — no external tools needed.
    """
    finished = pyqtSignal(list)   # list of dicts: {subdomain, ip}
    error    = pyqtSignal(str)

    WORDLIST = [
        "www", "mail", "smtp", "pop", "imap", "ftp", "admin", "api",
        "dev", "staging", "test", "beta", "app", "cdn", "static",
        "media", "img", "images", "vpn", "remote", "portal", "dashboard",
        "auth", "login", "secure", "shop", "store", "blog", "docs",
        "support", "help", "status", "monitor", "ns1", "ns2",
    ]

    def __init__(self, domain: str):
        super().__init__()
        # Use raw domain (strip leading http/https)
        self.domain = re.sub(r"^https?://", "", domain.strip()).rstrip("/")

    def run(self):
        found = []
        for sub in self.WORDLIST:
            fqdn = f"{sub}.{self.domain}"
            try:
                ip = socket.gethostbyname(fqdn)
                found.append({"subdomain": fqdn, "ip": ip})
            except socket.gaierror:
                pass
        self.finished.emit(found)


# ──────────────────────────────────────────
#  MASTER SCAN THREAD
# ──────────────────────────────────────────

class ScanThread(QThread):
    """
    Orchestrates all enabled modules sequentially in a single thread.
    Emits per-module signals as each one completes so the UI can
    stream results in real time.
    """

    # One signal per module — UI connects to whichever it needs
    log_line      = pyqtSignal(str)          # raw status line → terminal feed
    ip_done       = pyqtSignal(dict)
    ports_done    = pyqtSignal(list)
    whois_done    = pyqtSignal(str)
    subdomains_done = pyqtSignal(list)
    scan_complete = pyqtSignal(float)        # total elapsed seconds

    def __init__(self, target: str, modules: list[str]):
        """
        target  : IP or domain string
        modules : list of module names to run, e.g. ["ip", "ports", "whois", "subdomains"]
        """
        super().__init__()
        self.target  = target.strip()
        self.modules = modules

    def run(self):
        start = datetime.now()
        self.log_line.emit(f">> scan {self.target}  [{', '.join(self.modules)}]")
        self.log_line.emit(f"   resolving target...")

        ip = resolve_target(self.target)
        if ip:
            self.log_line.emit(f"   resolved → {ip}")
        else:
            self.log_line.emit(f"   [!] could not resolve {self.target!r}")

        # ── IP INTEL ──
        if "ip" in self.modules:
            self.log_line.emit("   [ IP INTEL ]  querying ipinfo.io...")
            worker = IpIntelWorker(self.target)
            worker.finished.connect(self.ip_done)
            worker.error.connect(lambda e: self.log_line.emit(f"   [!] ip intel: {e}"))
            # run synchronously inside the thread
            worker.run()
            self.log_line.emit("   [ IP INTEL ]  done")

        # ── PORT SCAN ──
        if "ports" in self.modules:
            self.log_line.emit("   [ PORT SCAN ]  scanning common ports...")
            worker = PortScanWorker(self.target)
            worker.finished.connect(self.ports_done)
            worker.error.connect(lambda e: self.log_line.emit(f"   [!] port scan: {e}"))
            worker.run()
            self.log_line.emit("   [ PORT SCAN ]  done")

        # ── WHOIS ──
        if "whois" in self.modules:
            self.log_line.emit("   [ WHOIS ]      running whois...")
            worker = WhoisWorker(self.target)
            worker.finished.connect(self.whois_done)
            worker.error.connect(lambda e: self.log_line.emit(f"   [!] whois: {e}"))
            worker.run()
            self.log_line.emit("   [ WHOIS ]      done")

        # ── SUBDOMAINS ──
        if "subdomains" in self.modules:
            self.log_line.emit("   [ SUBDOMAINS ] enumerating...")
            worker = SubdomainWorker(self.target)
            worker.finished.connect(self.subdomains_done)
            worker.error.connect(lambda e: self.log_line.emit(f"   [!] subdomains: {e}"))
            worker.run()
            self.log_line.emit("   [ SUBDOMAINS ] done")

        elapsed = (datetime.now() - start).total_seconds()
        self.log_line.emit(f"\n   [ DONE ]  completed in {elapsed:.1f}s\n")
        self.scan_complete.emit(elapsed)
