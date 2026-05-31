__author__ = "Yuval Malkan"

import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from CoreTools.ByPhone.PhoneOsint import full_phone_osint
from CoreTools.SocialMedia.Telegram import lookup_phone_sync

load_dotenv()

CONFIG = {
    "abstract_key": os.getenv("ABSTRACT_KEY"),
}


# ──────────────────────────────────────────
#  TIMEOUT HELPER  (mirrors FullUsernameSearch)
# ──────────────────────────────────────────

def run_function_with_timeout(func, timeout, *args, **kwargs):
    """Run a function in a thread; return an error dict if it times out."""
    try:
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            return {"error": f"Timeout after {timeout}s"}
        if exception[0]:
            return {"error": str(exception[0])}
        return result[0]
    except Exception as e:
        return {"error": str(e)}


# ──────────────────────────────────────────
#  MAIN SEARCH FUNCTION
# ──────────────────────────────────────────

def search_phone_complete(phone: str, config: dict = None) -> dict:
    """
    Complete OSINT scan for a phone number across all available sources in parallel.
    Mirrors the structure of search_username_complete() in FullUsernameSearch.py.
    """
    if config is None:
        config = CONFIG

    report = {
        "query": phone,
        "timestamp": None,
        "sources": {},
        "summary": {}
    }

    start_time = time.time()

    # ── Telegram runs in its own thread early (writes JSON to temp) ──
    telegram_thread = threading.Thread(
        target=lookup_phone_sync,
        args=(phone,),
        daemon=True
    )
    telegram_thread.start()

    # ── Other lookups run in the thread pool ──
    functions_to_run = [
        (full_phone_osint, "basic", 30, phone, config.get("abstract_key")),
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_key = {}
        for func, key, timeout, *args in functions_to_run:
            future = executor.submit(run_function_with_timeout, func, timeout, *args)
            future_to_key[future] = key

        for future in future_to_key:
            key = future_to_key[future]
            try:
                report["sources"][key] = future.result()
            except Exception as e:
                report["sources"][key] = {"error": str(e)}

    # ── Wait for Telegram thread, then read its JSON output ──
    telegram_thread.join(timeout=60)

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    phone_safe = phone.replace("+", "").replace(" ", "")
    telegram_json_path = os.path.join(
        BASE_DIR, "CoreTools", "temp", f"telegram_phone_{phone_safe}.json"
    )

    if os.path.exists(telegram_json_path):
        try:
            with open(telegram_json_path, "r", encoding="utf-8") as f:
                report["sources"]["telegram"] = json.load(f)
        except Exception as e:
            report["sources"]["telegram"] = {"error": f"Failed to read telegram JSON: {e}"}
    else:
        report["sources"]["telegram"] = {
            "error": "Telegram JSON not written — check credentials or session"
        }

    report["summary"] = _build_phone_summary(report["sources"], phone)
    report["elapsed_seconds"] = round(time.time() - start_time, 2)

    return report


# ──────────────────────────────────────────
#  SUMMARY BUILDER
# ──────────────────────────────────────────

def _build_phone_summary(sources: dict, phone: str) -> dict:
    """Extract and combine key findings from all sources."""
    tg = sources.get("telegram", {})
    basic = sources.get("basic", {})
    ab = basic.get("abstract", {}) if isinstance(basic, dict) else {}
    co = basic.get("country_offline", {}) if isinstance(basic, dict) else {}
    parsed = basic.get("parsed", {}) if isinstance(basic, dict) else {}

    # Ignore placeholder names like "."
    name = tg.get("full_name") if isinstance(tg, dict) else None
    if name and all(c in ". " for c in name):
        name = None

    return {
        # ── Identity ──
        "name": name,
        "telegram_id": tg.get("telegram_id") if isinstance(tg, dict) else None,
        "telegram_username": tg.get("username") if isinstance(tg, dict) else None,
        "telegram_registered": tg.get("registered", False) if isinstance(tg, dict) else False,
        "telegram_premium": tg.get("is_premium", False) if isinstance(tg, dict) else False,
        "telegram_scam": tg.get("is_scam", False) if isinstance(tg, dict) else False,
        "telegram_fake": tg.get("is_fake", False) if isinstance(tg, dict) else False,
        "telegram_verified": tg.get("is_verified", False) if isinstance(tg, dict) else False,
        "telegram_has_photo": tg.get("has_profile_photo", False) if isinstance(tg, dict) else False,
        "telegram_photo_saved": tg.get("profile_photo_saved") if isinstance(tg, dict) else None,
        "telegram_photo_size_kb": tg.get("profile_photo_size_kb") if isinstance(tg, dict) else None,
        "telegram_photo_base64": tg.get("profile_photo_base64") if isinstance(tg, dict) else None,
        "telegram_profile_url": tg.get("profile_url") if isinstance(tg, dict) else None,
        "telegram_error": tg.get("error") if isinstance(tg, dict) else str(tg),

        # ── Line info ──
        "phone_e164": parsed.get("e164"),
        "country": ab.get("country") or co.get("country"),
        "country_flag": co.get("flag"),
        "line_type": ab.get("type"),
        "location": ab.get("location"),

        # ── Google dorks ──
        "google_dork_urls": basic.get("google_dorks", []) if isinstance(basic, dict) else [],
    }


# ──────────────────────────────────────────
#  PRINT REPORT  (CLI output)
# ──────────────────────────────────────────

def print_phone_report(report: dict):
    s = report.get("summary", {})
    elapsed = report.get("elapsed_seconds", "?")

    print("\n" + "═" * 55)
    print(f"  NEURON PHONE OSINT — {report['query']}  ({elapsed}s)")
    print("═" * 55)
    print(f"  Phone        : {s.get('phone_e164') or report['query']}")
    print(f"  Country      : {s.get('country_flag', '')} {s.get('country') or '—'}")
    print(f"  Line type    : {s.get('line_type') or '—'}")
    print(f"  Location     : {s.get('location') or '—'}")
    print("─" * 55)

    tg_registered = s.get("telegram_registered")
    tg_id = s.get("telegram_username") or (str(s.get("telegram_id")) if s.get("telegram_id") else None)

    print(f"  Telegram     : {'✓ ' + tg_id if tg_id else ('✓ (no username)' if tg_registered else '✗ Not found')}")

    if tg_registered:
        print(f"  TG Name      : {s.get('name') or '—'}")
        print(f"  TG Premium   : {'Yes' if s.get('telegram_premium') else 'No'}")
        print(f"  TG Scam flag : {'⚠ YES' if s.get('telegram_scam') else 'No'}")
        if s.get("telegram_photo_saved"):
            print(f"  TG Photo     : ✓ {s['telegram_photo_saved']} ({s.get('telegram_photo_size_kb', '?')} KB)")
        elif s.get("telegram_has_photo"):
            print(f"  TG Photo     : exists (download failed)")
        else:
            print(f"  TG Photo     : No")
        if s.get("telegram_profile_url"):
            print(f"  TG Profile   : {s['telegram_profile_url']}")
    elif s.get("telegram_error"):
        print(f"  TG Error     : {s['telegram_error']}")

    print("─" * 55)
    print(f"  Google dorks : {len(s.get('google_dork_urls', []))} queries ready")
    print("═" * 55 + "\n")


# ──────────────────────────────────────────
#  GEMINI PROMPT BUILDER
# ──────────────────────────────────────────

def build_gemini_prompt(report: dict) -> str:
    s = report.get("summary", {})
    lines = [
        "You are an OSINT analyst. Analyze the following phone number data and provide:",
        "1. A summary of what is known about this number",
        "2. Any patterns or conclusions you can draw",
        "3. Risk assessment (spam/scam/legitimate)",
        "4. Recommended next investigation steps",
        "",
        f"Phone number : {report['query']}",
        f"Country      : {s.get('country') or 'Unknown'}",
        f"Line type    : {s.get('line_type') or 'Unknown'}",
        f"Location     : {s.get('location') or 'Unknown'}",
        "",
        "=== TELEGRAM ===",
        f"Registered   : {s.get('telegram_registered')}",
        f"ID           : {s.get('telegram_id') or 'N/A'}",
        f"Username     : {s.get('telegram_username') or 'None'}",
        f"Name         : {s.get('name') or 'None'}",
        f"Premium      : {s.get('telegram_premium')}",
        f"Has photo    : {s.get('telegram_has_photo')}",
        f"Photo file   : {s.get('telegram_photo_saved') or 'N/A'}",
        f"Scam flag    : {s.get('telegram_scam')}",
        f"Fake flag    : {s.get('telegram_fake')}",
        f"Profile URL  : {s.get('telegram_profile_url') or 'N/A'}",
        "",
        "=== GOOGLE DORK URLS ===",
    ]
    for url in s.get("google_dork_urls", []):
        lines.append(f"  {url}")
    return "\n".join(lines)


# ──────────────────────────────────────────
#  SAVE REPORT
# ──────────────────────────────────────────

def save_phone_report(report: dict) -> str:
    """Save the complete report (without base64 blob) to JSON in temp folder."""
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    TEMP_FOLDER = os.path.join(BASE_DIR, "temp")
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    phone_safe = report.get("query", "unknown").replace("+", "").replace(" ", "")
    filename = f"osint_phone_{phone_safe}.json"
    filepath = os.path.join(TEMP_FOLDER, filename)

    # Strip base64 blobs before saving
    report_clean = json.loads(json.dumps(report))
    report_clean.get("summary", {}).pop("telegram_photo_base64", None)
    report_clean.get("sources", {}).get("telegram", {}).pop("profile_photo_base64", None)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report_clean, f, indent=2, ensure_ascii=False)

    return filepath


# ──────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────

if __name__ == "__main__":
    phone = input("Enter phone number: ").strip()
    if not phone:
        print("No phone number provided!")
        exit(1)

    print(f"\nSearching for {phone}...")
    report = search_phone_complete(phone)

    print_phone_report(report)

    filepath = save_phone_report(report)
    print(f"Report saved to: {filepath}\n")

    print("\n=== GEMINI PROMPT ===\n")
    print(build_gemini_prompt(report))