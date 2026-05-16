__author__ = 'Yuval Malkan'

import json
import urllib.request
from Helpers import resolve_target

def get_ip_intel(target: str) -> dict:
    """Uses socket + ipinfo.io to gather information about an IP or domain."""
    try:
        ip = resolve_target(target)
        if not ip:
            return {"error": f"Could not resolve: {target}"}

        url = f"https://ipinfo.io/{ip}/json"
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode())

        return {
            "ip":       data.get("ip", ip),
            "hostname": data.get("hostname", "N/A"),
            "city":     data.get("city", "N/A"),
            "country":  data.get("country", "N/A"),
            "org":      data.get("org", "N/A"),
            "timezone": data.get("timezone", "N/A"),
        }
    except Exception as e:
        return {"error": str(e)}