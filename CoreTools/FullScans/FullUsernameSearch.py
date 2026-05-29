__author__ = "Yuval Malkan"

import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from CoreTools.Maigret import Maigret_search_username
from CoreTools.Sherlock import sherlock_search_username
#from CoreTools.accountFinder import findByUsername
from CoreTools.SocialMedia.Telegram import lookup_username_sync
from CoreTools.SocialMedia.Facebook import FacebookFullScan
from CoreTools.SocialMedia.Instagram import InstagramFullScan

"""
Complete OSINT scan for a username across all available sources in parallel.
"""


def run_function_with_timeout(func, timeout, *args, **kwargs):
    """Run function with timeout protection"""
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


def search_username_complete(username: str) -> dict:
    """
    Complete username search across ALL available OSINT sources.
    Runs all tools in parallel for maximum speed.

    Args:
        username: Target username to search (with or without @)

    Returns:
        Comprehensive report with all findings from:
        - Sherlock (social media platforms)
        - Maigret (site enumeration)
        - Account Finder (custom sites database)
        - Telegram (Telegram-specific lookup)
    """

    username = username.lstrip("@")
    report = {
        "query": username,
        "timestamp": None,
        "sources": {},
        "summary": {}
    }

    import time
    start_time = time.time()

    # Define all username search functions with their timeouts
    functions_to_run = [
        (sherlock_search_username, "sherlock", 90, username),
        (Maigret_search_username, "maigret", 90, username),
        (lookup_username_sync, "telegram", 30, username),
        (FacebookFullScan, "facebook", 30, username),
        (InstagramFullScan, "instagram", 30, username),
    ]

    # Execute all functions in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_key = {}

        for func, key, timeout, *args in functions_to_run:
            future = executor.submit(run_function_with_timeout, func, timeout, *args)
            future_to_key[future] = key

        # Collect results as they complete
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                result = future.result()
                report["sources"][key] = result
            except Exception as e:
                report["sources"][key] = {"error": str(e)}

    # Build summary from all sources
    report["summary"] = _build_username_summary(report["sources"], username)
    report["elapsed_seconds"] = round(time.time() - start_time, 2)

    return report


def _build_username_summary(sources: dict, username: str) -> dict:
    """Extract and combine key findings from all sources"""
    summary = {
        "total_accounts_found": 0,
        "platforms": [],
        "telegram": {},
        "instagram": {},
        "facebook": {},
    }

    # Sherlock results
    sherlock_data = sources.get("sherlock", {})
    if isinstance(sherlock_data, list):
        for account in sherlock_data:
            summary["platforms"].append({
                "source": "sherlock",
                "site": account.get("site"),
                "url": account.get("url")
            })
            summary["total_accounts_found"] += 1

    # Maigret results
    maigret_data = sources.get("maigret", {})
    if maigret_data and isinstance(maigret_data, dict) and "accounts" in maigret_data:
        for account in maigret_data.get("accounts", []):
            summary["platforms"].append({
                "source": "maigret",
                "site": account.get("site"),
                "url": account.get("url"),
                "details": account.get("details", {})
            })
            summary["total_accounts_found"] += 1

    # Telegram results
    telegram_data = sources.get("telegram", {})
    if isinstance(telegram_data, dict):  # Remove the "not error" check
        summary["telegram"] = {
            "found": telegram_data.get("found", False),
            "user_id": telegram_data.get("telegram_id"),
            "username": telegram_data.get("username"),
            "name": telegram_data.get("full_name"),
            "bio": telegram_data.get("bio"),
            "is_verified": telegram_data.get("is_verified"),
            "is_premium": telegram_data.get("is_premium"),
            "is_scam": telegram_data.get("is_scam"),
            "is_fake": telegram_data.get("is_fake"),
            "has_photo": telegram_data.get("has_profile_photo"),
            "profile_photo": telegram_data.get("profile_photo_saved"),
            "profile_url": telegram_data.get("profile_url"),
            "error": telegram_data.get("error"),  # Add error field
        }

    # Instagram results
    instagram_data = sources.get("instagram", {})
    if instagram_data and isinstance(instagram_data, dict) and not instagram_data.get("error"):
        summary["instagram"] = {
            "username": instagram_data.get("username"),
            "display_name": instagram_data.get("display_name"),
            "bio": instagram_data.get("bio"),
            "followers": instagram_data.get("followers"),
            "following": instagram_data.get("following"),
            "number_of_posts": instagram_data.get("number_of_posts"),
            "profile_picture_url": instagram_data.get("profile_picture_url"),
            "profile_url": instagram_data.get("profile_url"),
        }
    else:
        summary["instagram"] = instagram_data  # Include error if present

    # Facebook results
    facebook_data = sources.get("facebook", {})
    if facebook_data and isinstance(facebook_data, dict) and not facebook_data.get("error"):
        summary["facebook"] = facebook_data
    else:
        summary["facebook"] = facebook_data  # Include error if present

    return summary


def print_username_report(report: dict):
    """Pretty print the username search report"""
    username = report.get("query", "?")
    elapsed = report.get("elapsed_seconds", "?")

    print("\n" + "=" * 70)
    print(f"  NEURON USERNAME OSINT — @{username}  ({elapsed}s)")
    print("=" * 70)

    summary = report.get("summary", {})

    # Telegram section
    if summary.get("telegram"):
        tg = summary["telegram"]
        print("\n[TELEGRAM]")
        if tg.get("found"):
            print(f"    Found")
            print(f"    ID: {tg.get('user_id')}")
            print(f"    Name: {tg.get('name') or 'N/A'}")
            print(f"    Bio: {tg.get('bio') or 'N/A'}")
            print(f"    Verified: {'Yes' if tg.get('is_verified') else 'No'}")
            print(f"    Premium: {'Yes' if tg.get('is_premium') else 'No'}")
            print(f"    Scam flag: {'YES' if tg.get('is_scam') else 'No'}")
            print(f"    Fake flag: {'YES' if tg.get('is_fake') else 'No'}")
            if tg.get("profile_photo"):
                print(f"    Photo: {tg['profile_photo']}")
            if tg.get("profile_url"):
                print(f"    Profile: {tg['profile_url']}")
        else:
            print("  ✗ Not found")


    # Facebook section
    if summary.get("facebook"):
        fb = summary["facebook"]
        print("\n[FACEBOOK]")
        if not fb.get("error"):
            print(f"  ✓ Found")
            # Print ALL available raw data from Facebook
            for key, value in fb.items():
                if value and key != 'error':
                    # Format key nicely (convert snake_case to Title Case)
                    formatted_key = key.replace('_', ' ').title()
                    print(f"  {formatted_key}: {value}")
        else:
            print(f"  ✗ Error: {fb.get('error')}")


    # Instagram section
    if summary.get("instagram"):
        ig = summary["instagram"]
        print("\n[INSTAGRAM]")
        if not ig.get("error"):
            print(f"  ✓ Found")
            print(f"  Username: {ig.get('username') or 'N/A'}")
            print(f"  Display Name: {ig.get('display_name') or 'N/A'}")
            print(f"  Bio: {ig.get('bio') or 'N/A'}")
            print(f"  Followers: {ig.get('followers') or 'N/A'}")
            print(f"  Following: {ig.get('following') or 'N/A'}")
            print(f"  Posts: {ig.get('number_of_posts') or 'N/A'}")
            if ig.get("profile_picture_url"):
                print(f"  Profile Picture: {ig['profile_picture_url']}")
            if ig.get("profile_url"):
                print(f"  Profile: {ig['profile_url']}")
        else:
            print(f"  ✗ Error: {ig.get('error')}")

    # Other platforms (remove the limit of 15)
    platforms = summary.get("platforms", [])
    if platforms:
        print(f"\n[SOCIAL MEDIA & PLATFORMS] ({len(platforms)} accounts found)")
        for i, platform in enumerate(platforms, 1):  # Removed the [:15] slice
            print(f"  {i}. {platform.get('site')}")
            print(f"     {platform.get('url')}")
            if platform.get('details'):
                for key, val in list(platform['details'].items())[:2]:
                    print(f"     {key}: {val}")
        # Remove the "more accounts" print statement entirely



    print("\n" + "=" * 70)


def save_username_report(report: dict):
    """Save the complete report to JSON in temp folder"""
    import os

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    TEMP_FOLDER = os.path.join(BASE_DIR, "temp")
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    username = report.get("query", "unknown")
    filename = f"osint_username_{username}.json"
    filepath = os.path.join(TEMP_FOLDER, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return filepath


if __name__ == "__main__":
    username = input("Enter username to search: ").strip()

    if not username:
        print("No username provided!")
        exit(1)

    print(f"\nSearching for @{username}...")
    report = search_username_complete(username)

    print_username_report(report)

    filepath = save_username_report(report)
    print(f"Report saved to: {filepath}\n")
