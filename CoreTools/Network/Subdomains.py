__author__ = "Yuval Malkan"

import socket
import re


def enumerate_subdomains(domain: str) -> list[dict]:
    """
    Tries a wordlist of common subdomains via DNS resolution.
    Lightweight — no external tools needed.
    """
    WORDLIST = [
        "www", "mail", "smtp", "pop", "imap", "ftp", "admin", "api",
        "dev", "staging", "test", "beta", "app", "cdn", "static",
        "media", "img", "images", "vpn", "remote", "portal", "dashboard",
        "auth", "login", "secure", "shop", "store", "blog", "docs",
        "support", "help", "status", "monitor", "ns1", "ns2",
    ]

    #use raw domain (strip leading http/https)
    clean_domain = re.sub(r"^https?://", "", domain.strip()).rstrip("/")
    found = []

    for sub in WORDLIST:
        fqdn = f"{sub}.{clean_domain}"
        try:
            ip = socket.gethostbyname(fqdn)
            found.append({"subdomain": fqdn, "ip": ip})
        except socket.gaierror:
            pass

    return found