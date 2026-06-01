__author__ = "Yuval Malkan"

import json
import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from PhoneOsint import full_phone_osint
from CoreTools.SocialMedia.Telegram import lookup_phone_sync

load_dotenv()

CONFIG = {
    "abstract_key": os.getenv("ABSTRACT_KEY"),
}


async def _run_all(phone: str, config: dict) -> dict:
    report = {"query": phone, "sources": {}}
    start = time.time()

    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=3) as pool:
        future_basic = loop.run_in_executor(
            pool, lambda: full_phone_osint(phone, abstract_key=config.get("abstract_key"))
        )

        #no auth prompt if session exists
        future_tg = loop.run_in_executor(
            pool, lambda: lookup_phone_sync(phone)
        )


        basic_result, tg_result = await asyncio.gather(
            future_basic,
            future_tg,
            return_exceptions=True
        )

    report["sources"]["basic"] = basic_result if not isinstance(basic_result, Exception) else {
        "error": str(basic_result)}
    report["sources"]["telegram"] = tg_result if not isinstance(tg_result, Exception) else {"error": str(tg_result)}

    report["elapsed_seconds"] = round(time.time() - start, 2)
    report["summary"] = _build_summary(report["sources"])
    return report


def _build_summary(sources: dict) -> dict:
    tg = sources.get("telegram", {})
    basic = sources.get("basic", {})
    ab = basic.get("abstract", {})
    co = basic.get("country_offline", {})
    parsed = basic.get("parsed", {})


    name = tg.get("full_name")
    if name and all(c in ". " for c in name):
        name = None

    return {
        # Identity
        "name": name,
        "telegram_id": tg.get("telegram_id"),
        "telegram_username": tg.get("username"),
        "telegram_registered": tg.get("registered", False),
        "telegram_premium": tg.get("is_premium", False),
        "telegram_scam": tg.get("is_scam", False),
        "telegram_fake": tg.get("is_fake", False),
        "telegram_verified": tg.get("is_verified", False),
        "telegram_has_photo": tg.get("has_profile_photo", False),
        "telegram_photo_saved": tg.get("profile_photo_saved"),
        "telegram_photo_size_kb": tg.get("profile_photo_size_kb"),
        "telegram_photo_base64": tg.get("profile_photo_base64"),
        "telegram_profile_url": tg.get("profile_url"),

        # Line info
        "phone_e164": parsed.get("e164"),
        "country": ab.get("country") or co.get("country"),
        "country_flag": co.get("flag"),
        "line_type": ab.get("type"),
        "location": ab.get("location"),

        # Google dorks
        "google_dork_urls": basic.get("google_dorks", []),
    }


def run_full_osint(phone: str, config: dict = None) -> dict:
    return asyncio.run(_run_all(phone, config or CONFIG))


def print_report(report: dict):
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
    tg_id = s.get('telegram_username') or str(s.get('telegram_id')) if s.get('telegram_registered') else None

    print(
        f"  Telegram     : {' ' + tg_id if tg_id else (' (no username)' if s.get('telegram_registered') else '  Not found')}")
    if s.get('telegram_registered'):
        print(f"  TG Name      : {s.get('name') or '—'}")
        print(f"  TG Premium   : {'Yes' if s.get('telegram_premium') else 'No'}")
        print(f"  TG Scam flag : {'YES' if s.get('telegram_scam') else 'No'}")
        if s.get('telegram_photo_saved'):
            print(f"  TG Photo     :  {s['telegram_photo_saved']} ({s.get('telegram_photo_size_kb', '?')} KB)")
        elif s.get('telegram_has_photo'):
            print(f"  TG Photo     : exists (download failed)")
        else:
            print(f"  TG Photo     : No")
        if s.get('telegram_profile_url'):
            print(f"  TG Profile   : {s['telegram_profile_url']}")
    print("─" * 55)
    print(f"  Google dorks : {len(s.get('google_dork_urls', []))} queries ready")
    print("═" * 55 + "\n")






def build_gemini_prompt(report: dict) -> str:
    s = report.get("summary", {})
    lines = [
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


if __name__ == "__main__":
    PHONE = input("Enter phone number: ")

    report = run_full_osint(PHONE)
    print_report(report)


    report_clean = json.loads(json.dumps(report))
    report_clean.get("summary", {}).pop("telegram_photo_base64", None)
    report_clean.get("sources", {}).get("telegram", {}).pop("profile_photo_base64", None)

    filename = f"report_{PHONE.replace('+', '')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report_clean, f, indent=2, ensure_ascii=False)
    print(f"Report saved to {filename}")

    print(build_gemini_prompt(report))