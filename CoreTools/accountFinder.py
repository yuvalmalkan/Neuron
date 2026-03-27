__author__ = "Yuval Malkan"

import json
import threading
import requests
from pathlib import Path


# ── Load sites from JSON ──────────────────────────────────────────────────────

def load_sites(json_path: str = "sites.json") -> dict:
    """
    Flatten all categories from sites.json into a single {name: info} dict.
    The JSON structure is: { "categories": { "Category Name": { "Site": {...} } } }
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"sites.json not found at: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    flat: dict = {}
    for category_sites in data["categories"].values():
        for site_name, site_info in category_sites.items():
            if site_name in flat:
                print(f"[!] Duplicate site name skipped: {site_name}")
                continue
            flat[site_name] = site_info
    return flat


sites = load_sites()


# ── Core logic ────────────────────────────────────────────────────────────────

def check_not_found_strings(response_text: str, not_found_strings: list) -> bool:
    """Returns True if any not-found indicator is found in the page text."""
    text_lower = response_text.lower()
    return any(s.lower() in text_lower for s in not_found_strings)


def findByUsername(username): #todo add website/account search by intrests or categorys
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    for site, info in sites.items():
        target_url = info["url"].format(username)
        try:
            r = requests.get(target_url, timeout=8, headers=headers, allow_redirects=True)

            # 1. Non-200 status -> not found
            if r.status_code != 200:
                continue

            # 2. Redirect away from expected URL -> not found (for check_url sites)
            if info.get("check_url") and r.url != target_url:
                continue

            # 3. Page contains a known "not found" phrase -> false positive
            if info.get("not_found") and check_not_found_strings(r.text, info["not_found"]):
                continue

            print(f"[+] Found {username} on {site}: {target_url}")

        except requests.RequestException:
            pass  # timeout, connection error, etc.


def makeUserNames(fullname: str) -> list:
    parts = fullname.lower().split()
    if len(parts) < 2:
        return [parts[0]]

    first, last = parts[0], parts[1]
    usernames = [
        first + last,
        first + "." + last,
        first + "_" + last,
        first + last + "_",
        last + first,
        last + "." + first,
        last + "_" + first,

    ]
    return list(dict.fromkeys(usernames))


def findAccounts(fullname: str):
    usernames = makeUserNames(fullname)
    print(f"Searching {len(usernames)} username variations across {len(sites)} sites...\n")

    threads = []
    for username in usernames:
        thread = threading.Thread(target=findByUsername, args=(username,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    print("\nDone.")


if __name__ == "__main__":
    findAccounts("Yuval Malkan")
