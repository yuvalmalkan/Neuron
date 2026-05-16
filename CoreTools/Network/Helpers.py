__author__ = "Yuval Malkan"

import socket

def resolve_target(target: str) -> str | None:
    """Resolve a domain to IP. Returns the IP string or None on failure."""
    try:
        return socket.gethostbyname(target.strip())
    except socket.gaierror:
        return None

def is_ip(target: str) -> bool:
    """Checks if a given string is a valid IPv4 address."""
    parts = target.strip().split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False