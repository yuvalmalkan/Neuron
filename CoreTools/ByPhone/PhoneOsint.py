__author__ = "Yuval Malkan"


import requests
import re
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


# ─── PHONE VALIDATION ─────────────────────────────────────────────────────────

def parse_phone(phone: str) -> dict:
    digits = re.sub(r'\D', '', phone)
    e164 = '+' + digits if not phone.strip().startswith('+') else '+' + digits
    return {
        "raw": phone,
        "digits_only": digits,
        "e164": e164,
        "length": len(digits),
        "valid_length": len(digits) in range(7, 16)
    }


# ─── ABSTRACT API ─────────────────────────────────────────────────────────────

def lookup_abstract(phone: str, api_key: str) -> dict:
    url = "https://phonevalidation.abstractapi.com/v1/"
    params = {"api_key": api_key, "phone": phone}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        return {
            "source": "abstract",
            "valid": data.get("valid"),
            "format_international": data.get("format", {}).get("international"),
            "format_local": data.get("format", {}).get("local"),
            "country": data.get("country", {}).get("name"),
            "country_code": data.get("country", {}).get("code"),
            "location": data.get("location"),
            "type": data.get("type"),
        }
    except Exception as e:
        return {"source": "abstract", "error": str(e)}


# ─── COUNTRY FROM DIAL CODE (offline fallback) ────────────────────────────────

DIAL_CODES = {
    "972": {"country": "Israel",            "flag": "🇮🇱"},
    "1":   {"country": "USA / Canada",      "flag": "🇺🇸"},
    "44":  {"country": "United Kingdom",    "flag": "🇬🇧"},
    "49":  {"country": "Germany",           "flag": "🇩🇪"},
    "33":  {"country": "France",            "flag": "🇫🇷"},
    "39":  {"country": "Italy",             "flag": "🇮🇹"},
    "7":   {"country": "Russia/Kazakhstan", "flag": "🇷🇺"},
    "86":  {"country": "China",             "flag": "🇨🇳"},
    "91":  {"country": "India",             "flag": "🇮🇳"},
    "20":  {"country": "Egypt",             "flag": "🇪🇬"},
    "962": {"country": "Jordan",            "flag": "🇯🇴"},
    "961": {"country": "Lebanon",           "flag": "🇱🇧"},
    "963": {"country": "Syria",             "flag": "🇸🇾"},
    "966": {"country": "Saudi Arabia",      "flag": "🇸🇦"},
    "971": {"country": "UAE",               "flag": "🇦🇪"},
    "90":  {"country": "Turkey",            "flag": "🇹🇷"},
    "98":  {"country": "Iran",              "flag": "🇮🇷"},
}

def get_country_from_dialcode(phone: str) -> dict:
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('0'):
        digits = digits[1:]
    for length in [3, 2, 1]:
        prefix = digits[:length]
        if prefix in DIAL_CODES:
            return {
                "dial_code": "+" + prefix,
                **DIAL_CODES[prefix],
                "local_number": digits[length:]
            }
    return {"error": "Unknown dial code"}


# ─── GOOGLE DORKS (just URLs, no scraping — avoids 429) ──────────────────────

def google_dorks_for_phone(phone: str) -> list:
    digits = re.sub(r'\D', '', phone)
    formatted = phone.strip()
    dorks = [
        f'"{formatted}"',
        f'"{formatted}" site:facebook.com',
        f'"{formatted}" site:instagram.com',
        f'"{formatted}" site:linkedin.com',
        f'"{formatted}" site:twitter.com OR site:x.com',
        f'"{formatted}" site:tiktok.com',
        f'"{digits}" filetype:pdf',
        f'"{formatted}" intext:contact',
        f'"{digits}" site:truecaller.com',
    ]
    base = "https://www.google.com/search?q="
    return [base + requests.utils.quote(d) for d in dorks]


# ─── AGGREGATE ────────────────────────────────────────────────────────────────

def full_phone_osint(phone: str, abstract_key: Optional[str] = None) -> dict:
    results = {
        "parsed": parse_phone(phone),
        "country_offline": get_country_from_dialcode(phone),
        "google_dorks": google_dorks_for_phone(phone),
    }
    if abstract_key:
        results["abstract"] = lookup_abstract(phone, abstract_key)
    return results
