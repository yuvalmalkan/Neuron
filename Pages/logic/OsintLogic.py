__author__ = 'Yuval Malkan'

import re
import logging
from Gemini import ask_gemini
import json


def format_ai_response(raw_text: str) -> str:
    """Cleans markdown tags from Gemini's response and formats the JSON into a terminal report."""
    # 1. Clean markdown code blocks
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        data = json.loads(cleaned.strip())
        profile = data.get("target_profile", {})
        if not profile:
            return raw_text  # Fallback if schema doesn't match

        lines = []

        # --- CORE IDENTITY ---
        core = profile.get("core_identity", {})
        if core:
            lines.append("[CORE IDENTITY]")
            lines.append("─" * 60)

            alias = core.get("primary_name_or_alias", {})
            if alias.get("deduction"):
                lines.append(
                    f"  Primary Alias : {alias.get('deduction')} ({alias.get('confidence_score', 0)}% confidence)")
                lines.append(f"  ↳ Reasoning   : {alias.get('justification', '')}")

            contacts = core.get("contact_info", [])
            for c in contacts:
                lines.append(
                    f"  Contact       : {c.get('value')} [{c.get('type')}] ({c.get('confidence_score', 0)}% confidence)")

        # --- BEHAVIORAL ANALYSIS ---
        behav = profile.get("behavioral_analysis", {})
        if behav:
            lines.append("\n[BEHAVIORAL ANALYSIS]")
            lines.append("─" * 60)

            prof = behav.get("inferred_profession", {})
            if prof.get('deduction') and prof.get('deduction') != "Unknown":
                lines.append(f"  Profession : {prof.get('deduction')} ({prof.get('confidence_score', 0)}% confidence)")

            hobbies = behav.get("hobbies_and_interests", [])
            if hobbies:
                lines.append("  Interests  :")
                for h in hobbies:
                    lines.append(f"    • {h.get('deduction')} ({h.get('confidence_score', 0)}%)")
                    lines.append(f"      ↳ {h.get('justification')}")

            lifestyle = behav.get("lifestyle_indicators", [])
            if lifestyle:
                lines.append("  Lifestyle  :")
                for l in lifestyle:
                    lines.append(f"    • {l.get('deduction')} ({l.get('confidence_score', 0)}%)")

        # --- INVESTIGATIVE PIVOTS ---
        pivots = profile.get("investigative_pivots", {})
        if pivots:
            lines.append("\n[INVESTIGATIVE PIVOTS]")
            lines.append("─" * 60)

            vulns = pivots.get("opsec_vulnerabilities", [])
            if vulns:
                lines.append("  ⚠️ OPSEC Vulnerabilities:")
                for v in vulns:
                    lines.append(f"    • {v}")

            steps = pivots.get("recommended_next_steps", [])
            if steps:
                lines.append("\n  🎯 Recommended Next Steps:")
                for s in steps:
                    lines.append(f"    • {s}")

        return "\n".join(lines).strip()

    except json.JSONDecodeError:
        # If Gemini didn't return valid JSON, just return exactly what it said
        return raw_text


def generate_ai_summary(raw_results: str) -> str:
    """Pass raw OSINT results string to Gemini and return the AI summary."""
    try:
        raw_ai_response = ask_gemini(raw_results)
        return format_ai_response(raw_ai_response)
    except Exception as e:
        logging.error(f"Gemini summary error: {e}", exc_info=True)
        return f"[AI summary unavailable: {e}]"

def parse_target_input(raw: str) -> dict:
    """Parse a free-form input string into typed OSINT fields."""
    fields = {"phone": None, "email": None, "username": None, "name": None}
    tokens = raw.split()
    remaining = []
    for token in tokens:
        # Phone: starts with + followed by digits, or 7+ consecutive digits (with optional separators)
        if re.match(r'^\+\d{6,15}$', token) or re.match(r'^\d[\d\-\s().]{6,}$', token):
            fields["phone"] = token
        # Email
        elif re.match(r'[^@]+@[^@]+\.[^@]+', token):
            fields["email"] = token.lstrip("@")
        # Username: starts with @
        elif token.startswith("@") and len(token) > 1:
            fields["username"] = token.lstrip("@")
        else:
            remaining.append(token)
    if remaining and not any(fields[k] for k in ("phone", "email", "username")):
        fields["name"] = " ".join(remaining)
    return fields


def build_target_summary(fields: dict) -> str:
    """Format a short 'TARGET QUEUED' confirmation string from parsed fields."""
    lines = ["TARGET QUEUED", "─" * 28]
    if fields.get("name"):
        lines.append(f"  name      {fields['name']}")
    if fields.get("phone"):
        lines.append(f"  phone     {fields['phone']}")
    if fields.get("email"):
        lines.append(f"  email     {fields['email']}")
    if fields.get("username"):
        lines.append(f"  username  @{fields['username']}")
    return "\n".join(lines)


def format_osint_results(report: dict) -> str:
    """Convert a raw OSINT report dict into a human-readable terminal string."""
    query = report.get('query', '?')
    elapsed = report.get('elapsed_seconds', '?')
    summary = report.get('summary') or report.get('sources') or {}

    # Determine input type
    is_phone = bool(re.match(r'^\+?\d[\d\s\-.()]{5,}$', query.strip()))
    is_email = not is_phone and ('@' in query and '.' in query)

    # ── Phone ────────────────────────────────────────────────────────────────
    if is_phone:
        lines = [
            f"OSINT SCAN COMPLETE — {query}  ({elapsed}s)",
            "─" * 60,
            "\n[PHONE INFO]",
            "─" * 60,
        ]
        lines.append(f"  Phone     : {summary.get('phone_e164') or query}")
        lines.append(f"  Country   : {summary.get('country_flag', '')} {summary.get('country') or '—'}")
        lines.append(f"  Line type : {summary.get('line_type') or '—'}")
        lines.append(f"  Location  : {summary.get('location') or '—'}")

        lines.append("\n[TELEGRAM]")
        lines.append("─" * 60)
        if summary.get('telegram_registered'):
            tg_id = summary.get('telegram_username') or str(summary.get('telegram_id', ''))
            lines.append(f"  ✓ Found  (@{tg_id})" if tg_id else "  ✓ Found (no username)")
            lines.append(f"  ID       : {summary.get('telegram_id', 'N/A')}")
            lines.append(f"  Name     : {summary.get('name') or '—'}")
            lines.append(f"  Premium  : {'Yes' if summary.get('telegram_premium') else 'No'}")
            if summary.get('telegram_scam'):
                lines.append("  ⚠️  SCAM FLAG: YES")
            if summary.get('telegram_fake'):
                lines.append("  ⚠️  FAKE FLAG: YES")
            if summary.get('telegram_photo_saved'):
                lines.append(f"  Photo    : {summary['telegram_photo_saved']} ({summary.get('telegram_photo_size_kb', '?')} KB)")
            elif summary.get('telegram_has_photo'):
                lines.append("  Photo    : exists (download failed)")
            else:
                lines.append("  Photo    : No")
            if summary.get('telegram_profile_url'):
                lines.append(f"  Profile  : {summary['telegram_profile_url']}")
        else:
            err = summary.get('telegram_error')
            lines.append(f"  ✗ Not found{(' — ' + err) if err else ''}")

        dorks = summary.get('google_dork_urls', [])
        if dorks:
            lines.append(f"\n[GOOGLE DORK URLS] ({len(dorks)} queries)")
            lines.append("─" * 60)
            for url in dorks:
                lines.append(f"  LINK: {url}")

        lines.append("\n" + "─" * 60)
        return "\n".join(lines)

    #Email
    elif is_email:
        lines = [
            f"OSINT SCAN COMPLETE — {query}  ({elapsed}s)",
            "─" * 60,
            "\n[EMAIL SCAN SUMMARY]",
            "─" * 60,
        ]

        total_scanned = summary.get('total_scanned', 0)
        total_found = summary.get('total_accounts_found', 0)
        lines.append(f"  Total Scanned: {total_scanned}")
        lines.append(f"  Total Found: {total_found}")

        platforms = summary.get('platforms', [])
        if platforms:
            lines.append(f"\n[PLATFORMS WHERE EMAIL IS REGISTERED] ({len(platforms)} accounts)")
            lines.append("─" * 60)
            for i, platform in enumerate(platforms, 1):
                lines.append(f"\n  {i}. {platform.get('site', 'Unknown')}")
                lines.append(f"     Category: {platform.get('category', 'unknown')}")
                lines.append(f"     LINK: {platform.get('url', 'No URL')}")
        else:
            lines.append("\n[PLATFORMS WHERE EMAIL IS REGISTERED]")
            lines.append("  ✗ No accounts found")

        lines.append("\n" + "─" * 60)
        return "\n".join(lines)

    # ── Username ──────────────────────────────────────────────────────────────
    else:
        lines = [
            f"OSINT SCAN COMPLETE — @{query}  ({elapsed}s)",
            "─" * 60,
        ]

        if summary.get('telegram'):
            tg = summary['telegram']
            lines.append("\n[TELEGRAM]")
            lines.append("─" * 60)
            if tg.get('found'):
                lines.append(f"  ✓ Found")
                lines.append(f"  ID: {tg.get('user_id', 'N/A')}")
                lines.append(f"  Username: @{tg.get('username', 'N/A')}")
                lines.append(f"  Name: {tg.get('name', 'N/A')}")
                lines.append(f"  Bio: {tg.get('bio', 'N/A')}")
                lines.append(f"  Verified: {'Yes' if tg.get('is_verified') else 'No'}")
                lines.append(f"  Premium: {'Yes' if tg.get('is_premium') else 'No'}")
                if tg.get('is_scam'):
                    lines.append(f"  ⚠️  SCAM FLAG: YES")
                if tg.get('is_fake'):
                    lines.append(f"  ⚠️  FAKE FLAG: YES")
                if tg.get('profile_photo'):
                    lines.append(f"  Profile Photo: {tg['profile_photo']}")
                if tg.get('profile_url'):
                    lines.append(f"  Profile URL: {tg['profile_url']}")
            else:
                lines.append("  ✗ Not found")

        if summary.get('facebook'):
            fb = summary['facebook']
            lines.append("\n[FACEBOOK]")
            lines.append("─" * 60)
            if not fb.get('error'):
                lines.append(f"  ✓ Found")
                for key, value in fb.items():
                    if value and key != 'error':
                        lines.append(f"  {key}: {value}")
            else:
                lines.append(f"  ✗ Error: {fb.get('error')}")

        if summary.get('instagram'):
            ig = summary['instagram']
            lines.append("\n[INSTAGRAM]")
            lines.append("─" * 60)
            if not ig.get('error'):
                lines.append(f"  ✓ Found")
                lines.append(f"  Username: @{ig.get('username', 'N/A')}")
                lines.append(f"  Display Name: {ig.get('display_name', 'N/A')}")
                lines.append(f"  Bio: {ig.get('bio', 'N/A')}")
                lines.append(f"  Followers: {ig.get('followers', 'N/A')}")
                lines.append(f"  Following: {ig.get('following', 'N/A')}")
                lines.append(f"  Posts: {ig.get('number_of_posts', 'N/A')}")
                if ig.get('profile_picture_url'):
                    lines.append(f"  Profile Picture: {ig['profile_picture_url']}")
                if ig.get('profile_url'):
                    lines.append(f"  Profile URL: {ig['profile_url']}")
            else:
                lines.append(f"  ✗ Error: {ig.get('error')}")

        platforms = summary.get('platforms', [])
        if platforms:
            lines.append(f"\n[SOCIAL MEDIA & PLATFORMS] ({len(platforms)} total accounts found)")
            lines.append("─" * 60)
            for i, platform in enumerate(platforms, 1):
                lines.append(f"\n  {i}. {platform.get('site', 'Unknown')} (from {platform.get('source', '?')})")
                lines.append(f"     LINK: {platform.get('url', 'No URL')}")
                if platform.get('details'):
                    for key, val in platform['details'].items():
                        lines.append(f"     • {key}: {val}")
        else:
            lines.append("\n[SOCIAL MEDIA & PLATFORMS]\n  ✗ No accounts found")

        lines.append("\n" + "─" * 60)
        return "\n".join(lines)