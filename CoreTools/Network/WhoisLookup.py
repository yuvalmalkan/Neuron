__author__ = "Yuval Malkan"

import subprocess

def whois_lookup(target: str) -> str:
    """Runs system whois and returns raw cleaned text"""
    try:
        proc = subprocess.run(
            ["whois", target.strip()],
            capture_output=True, text=True, timeout=10
        )


        #strip comment lines and blank lines for cleaner output
        lines = [
            l for l in proc.stdout.splitlines()
            if l.strip() and not l.strip().startswith("%")
            and not l.strip().startswith("#")
        ]
        return "\n".join(lines[:40])  # cap at 40 lines


    except Exception as e:
        return f"Error: {str(e)}"