__author__ = 'Yuval Malkan'

import re
import os
import logging
from Gemini import ask_gemini
import json




def format_ai_response(raw_text: str) -> str:
    """Formats the JSON into a terminal report from the Gemini response."""
    if not raw_text:
        return "AI Summary Error: Empty response from model."

    start_idx = raw_text.find('{')
    end_idx = raw_text.rfind('}')

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = raw_text[start_idx:end_idx + 1]
    else:
        cleaned = raw_text

    try:

        data = json.loads(cleaned, strict=False)

        #fallback handling
        dossier = data.get("dossier", data)

        if not dossier:
            return raw_text

        lines = []

        #identity and demographics
        ident = dossier.get("identity_demographics", {})
        if ident:
            lines.append("IDENTITY & DEMOGRAPHICS")
            lines.append("─" * 60)

            alias = ident.get("primary_alias", {})
            if alias.get("value"):
                lines.append(f"  Primary Alias : {alias.get('value')} ({alias.get('score', 0)}% confidence)")
                lines.append(f"  ↳ Reasoning   : {alias.get('reason', '')}")

            age = ident.get("approximate_age", {})
            if age.get("value"):
                lines.append(f"  Est. Age      : {age.get('value')} ({age.get('score', 0)}%) - {age.get('reason', '')}")

            cult = ident.get("cultural_linguistic_affiliations", [])
            if cult:
                lines.append("  Cultural/Linguistic Markers:")
                for c in cult:
                    inds = ", ".join(c.get("indicators", []))
                    lines.append(f"    • {c.get('language_or_region', 'Unknown')} [{inds}]")



        #geographic profiling
        geo = dossier.get("geographic_profiling", {})
        if geo:
            lines.append("\nGEOGRAPHIC PROFILING")
            lines.append("─" * 60)

            res = geo.get("suspected_current_residence", {})
            if res.get("value"):
                lines.append(f"  Residence     : {res.get('value')} ({res.get('score', 0)}%)")
                lines.append(f"  ↳ Reasoning   : {res.get('reason', '')}")

            tz = geo.get("inferred_timezone", "")
            if tz:
                lines.append(f"  Timezone      : {tz}")

            dist = geo.get("footprint_distribution", {})
            if dist:
                lines.append(
                    f"  Distribution  : {dist.get('domestic_percent', 0)}% Domestic / {dist.get('foreign_percent', 0)}% Foreign")



        #professional and technical profile
        prof = dossier.get("professional_technical_profile", {})
        if prof:
            lines.append("\nPROFESSIONAL & TECHNICAL PROFILE")
            lines.append("─" * 60)

            job = prof.get("inferred_profession", {})
            if job.get("value"):
                lines.append(f"  Profession    : {job.get('value')} ({job.get('score', 0)}%)")
                lines.append(f"  ↳ Reasoning   : {job.get('reason', '')}")

            skill = prof.get("technical_skill_level", {})
            if skill.get("tier"):
                lines.append(
                    f"  Skill Level   : {skill.get('tier')} ({skill.get('score', 0)}%) - {skill.get('justification', '')}")

        #behavioral vectors
        behav = dossier.get("behavioral_vectors", {})
        if behav:
            lines.append("\nBEHAVIORAL VECTORS")
            lines.append("─" * 60)

            gaming = behav.get("gaming_entertainment", {})
            if gaming.get("platforms_identified"):
                lines.append(f"  Gaming Profile: {gaming.get('engagement_type', 'Unknown')}")
                lines.append(f"    • Platforms : {', '.join(gaming.get('platforms_identified', []))}")

            habits = behav.get("lifestyle_habits", [])
            if habits:
                lines.append("  Lifestyle Habits:")
                for h in habits:
                    lines.append(f"    • {h.get('hobby', 'Unknown')} (Intensity: {h.get('intensity_marker', 'N/A')})")

        #operational footprint
        opsec = dossier.get("operational_footprint", {})
        if opsec:
            lines.append("\nOPERATIONAL FOOTPRINT")
            lines.append("─" * 60)

            timeline = opsec.get("timeline", {})
            if timeline.get("earliest_known_footprint"):
                lines.append(f"  Earliest Trace: {timeline.get('earliest_known_footprint')}")

            behavior = opsec.get("handle_behavior", {})
            if behavior.get("uniqueness_rating"):
                lines.append(
                    f"  Handle Rating : {behavior.get('uniqueness_rating')} (Risk: {behavior.get('recycling_risk', 'Unknown')})")

            if opsec.get("footprint_orientation"):
                lines.append(f"  Orientation   : {opsec.get('footprint_orientation')}")

        return "\n".join(lines).strip()

    except json.JSONDecodeError:
        return f"\n[AI SUMMARY PARSING ERROR]\nRaw AI Output:\n{raw_text}"


def generate_ai_summary(target_input: str, raw_results: str) -> str:
    """Read the master prompt from file, inject both target input and scan results, then ask Gemini."""
    prompt_file_path = "AIPROMPT.txt"

    if os.path.exists(prompt_file_path):
        with open(prompt_file_path, "r", encoding="utf-8") as f:
            base_prompt = f.read()
    else:
        logging.warning("AIPROMPT.txt not found in root path. Defaulting to fallback baseline prompt.")
        base_prompt = "Act as an OSINT Analyst. Synthesize a behavioral profile from data. Return valid JSON only."

    # Assemble complete operational context block
    full_payload = f"""{base_prompt}

        RAW USER INPUT:
    {target_input}
    
        RAW OSINT SCAN RESULTS:
    {raw_results}
    """

    try:
        raw_ai_response = ask_gemini(full_payload)
        return format_ai_response(raw_ai_response)
    except Exception as e:
        logging.error(f"Gemini summary error: {e}", exc_info=True)
        return f"AI summary unavailable: {e}"


def parse_target_input(raw: str) -> dict:
    """parse a free form input string into typed osint fields."""
    fields = {"phone": None, "email": None, "username": None, "name": None, "extra": raw}
    tokens = raw.split()
    remaining = []

    for token in tokens:
        if re.match(r'^\+\d{6,15}$', token) or re.match(r'^\d[\d\-\s().]{6,}$', token):
            fields["phone"] = token

        elif re.match(r'[^@]+@[^@]+\.[^@]+', token):
            fields["email"] = token.lstrip("@")

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
    """convert a raw OSINT report dict into a human readable terminal string."""
    query = report.get('query', '?')
    elapsed = report.get('elapsed_seconds', '?')
    summary = report.get('summary') or report.get('sources') or {}

    is_phone = bool(re.match(r'^\+?\d[\d\s\-.()]{5,}$', query.strip()))
    is_email = not is_phone and ('@' in query and '.' in query)

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
            lines.append(f"  Found  (@{tg_id})" if tg_id else "    Found (no username)")
            lines.append(f"  ID       : {summary.get('telegram_id', 'N/A')}")
            lines.append(f"  Name     : {summary.get('name') or '—'}")
            lines.append(f"  Premium  : {'Yes' if summary.get('telegram_premium') else 'No'}")
            if summary.get('telegram_scam'):
                lines.append("  SCAM FLAG: YES")
            if summary.get('telegram_fake'):
                lines.append("  FAKE FLAG: YES")
            if summary.get('telegram_photo_saved'):
                lines.append(
                    f"  Photo    : {summary['telegram_photo_saved']} ({summary.get('telegram_photo_size_kb', '?')} KB)")
            elif summary.get('telegram_has_photo'):
                lines.append("  Photo    : exists (download failed)")
            else:
                lines.append("  Photo    : No")
            if summary.get('telegram_profile_url'):
                lines.append(f"  Profile  : {summary['telegram_profile_url']}")
        else:
            err = summary.get('telegram_error')
            lines.append(f"    Not found{(' — ' + err) if err else ''}")

        dorks = summary.get('google_dork_urls', [])
        if dorks:
            lines.append(f"\n[GOOGLE DORK URLS] ({len(dorks)} queries)")
            lines.append("─" * 60)
            for url in dorks:
                lines.append(f"  LINK: {url}")

        lines.append("\n" + "─" * 60)
        return "\n".join(lines)

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
            lines.append("   No accounts found")

        lines.append("\n" + "─" * 60)
        return "\n".join(lines)

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
                lines.append(f"  Found")
                lines.append(f"  ID: {tg.get('user_id', 'N/A')}")
                lines.append(f"  Username: @{tg.get('username', 'N/A')}")
                lines.append(f"  Name: {tg.get('name', 'N/A')}")
                lines.append(f"  Bio: {tg.get('bio', 'N/A')}")
                lines.append(f"  Verified: {'Yes' if tg.get('is_verified') else 'No'}")
                lines.append(f"  Premium: {'Yes' if tg.get('is_premium') else 'No'}")
                if tg.get('is_scam'):
                    lines.append(f"  SCAM FLAG: YES")
                if tg.get('is_fake'):
                    lines.append(f"  FAKE FLAG: YES")
                if tg.get('profile_photo'):
                    lines.append(f"  Profile Photo: {tg['profile_photo']}")
                if tg.get('profile_url'):
                    lines.append(f"  Profile URL: {tg['profile_url']}")
            else:
                lines.append("    Not found")

        if summary.get('facebook'):
            fb = summary['facebook']
            lines.append("\n[FACEBOOK]")
            lines.append("─" * 60)
            if not fb.get('error'):
                lines.append(f"    Found")
                for key, value in fb.items():
                    if value and key != 'error':
                        lines.append(f"  {key}: {value}")
            else:
                lines.append(f"    Error: {fb.get('error')}")

        if summary.get('instagram'):
            ig = summary['instagram']
            lines.append("\n[INSTAGRAM]")
            lines.append("─" * 60)
            if not ig.get('error'):
                lines.append(f"  Found")
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
                lines.append(f"    Error: {ig.get('error')}")

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
            lines.append("\n[SOCIAL MEDIA & PLATFORMS]\n    No accounts found")

        lines.append("\n" + "─" * 60)
        return "\n".join(lines)