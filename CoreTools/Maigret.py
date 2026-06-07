__author__ = "Yuval Malkan"

import subprocess
import threading
import time
import re
import platform
import shutil
import sys


#false positives
FALSE_POSITIVE_SITES = [
    "OP.GG", "Tom's guide", "mercadolivre", "opensea.io",
    "iXBT", "Livemaster", "3ddd", "Kaskus", "AdultFriendFinder",
    "hi5", "Weedmaps", "Bibsonomy", "authorSTREAM", "getmyuni",
    "Blu-ray", "TechPowerUp", "forums.bulbagarden.net", "Behance", "Scribd",
    "SlideShare", "AppleDeveloper", "AppleDiscussions", "Kaggle", "Warface", "HackerNews",
    "WikimapiaSearch", "interpals", "igromania", "Kinja", "hashnode", "MoscowFlamp"
]

def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes like \x1b[0m"""
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def _subprocess_flags() -> dict:
    #suppress console popup windows on Windows; no-op on Mac/Linux
    if platform.system() == "Windows":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}

def _find_maigret() -> list:
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'maigret', '--version'],
            capture_output=True, text=True, timeout=5,
            **_subprocess_flags()
        )
        if result.returncode == 0:
            return [sys.executable, '-m', 'maigret']
    except Exception:
        pass

    #fall back to the script on path
    found = shutil.which('maigret')
    if found:
        return [found]
    return ['maigret']

_MAIGRET_CMD = _find_maigret()




def Maigret_search_username(username: str) -> dict:
    start_time = time.time()
    stop_timer = threading.Event()

    def timer():
        while not stop_timer.is_set():
            elapsed = int(time.time() - start_time)
            print(f"\rsearching... {elapsed}s elapsed", end="", flush=True)
            time.sleep(1)

    timer_thread = threading.Thread(target=timer)
    timer_thread.start()

    try:
        result = subprocess.run(
            _MAIGRET_CMD + [username, "--no-color", "--no-progressbar"],
            capture_output=True,
            text=True,
            timeout=300,
            **_subprocess_flags()
        )
    finally:
        stop_timer.set()
        timer_thread.join()
        print()

    found = []
    current_site = None
    current_url  = None
    current_details = {}




    for raw_line in result.stdout.split("\n"):
        line = strip_ansi(raw_line).strip()

        if not line or line.startswith("\x1b") or line.startswith("[!]") \
                    or line.startswith("[-]") or line.startswith("[*]"):
            continue


        if line.startswith("[+]"):
            #save previous entry
            if current_site and current_url:
                if not any(fp in current_site for fp in FALSE_POSITIVE_SITES):
                    found.append({
                        "site":    current_site,
                        "url":     current_url,
                        "details": current_details
                    })

            #parse new entry
            content = line.replace("[+]", "").strip()
            parts = content.split(": ", 1)
            current_site    = parts[0].strip() if len(parts) == 2 else content
            current_url     = parts[1].strip() if len(parts) == 2 else ""
            current_details = {}

        elif "─" in line:
            detail = re.sub(r'^[│├└─\s]+', '', line).strip()
            if ": " in detail:
                key, value = detail.split(": ", 1)
                current_details[key.strip()] = value.strip()

    #save last entry
    if current_site and current_url:
        if not any(fp in current_site for fp in FALSE_POSITIVE_SITES):
            found.append({
                "site":    current_site,
                "url":     current_url,
                "details": current_details
            })

    total_time = round(time.time() - start_time, 1)

    return {
        "username": username,
        "accounts": found,
        "total":    len(found),
        "duration": total_time
    }






if __name__ == "__main__":
    user = input("Username: ")
    report = Maigret_search_username(user)
    print(f"\n Done in {report['duration']}s — found {report['total']} accounts\n")
    for r in report["accounts"]:
        print(f"  → {r['site']}: {r['url']}")
        for key, val in r["details"].items():
            print(f"      {key}: {val}")