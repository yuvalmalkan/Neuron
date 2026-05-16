__author__ = "Yuval Malkan"

import socket
from Helpers import resolve_target


def port_scanner(target: str) -> list[dict]:
    """Fast TCP connect scan on common ports."""
    COMMON_PORTS = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
        443: "HTTPS", 445: "SMB", 3306: "MySQL", 3389: "RDP",
        5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP-ALT",
        8443: "HTTPS-ALT", 27017: "MongoDB",
    }

    try:
        ip = resolve_target(target) or target
        results = []

        for port, service in COMMON_PORTS.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            state = "OPEN" if sock.connect_ex((ip, port)) == 0 else "CLOSED"
            sock.close()
            results.append({"port": port, "state": state, "service": service})

        return results
    except Exception as e:
        return [{"error": str(e)}]