__author__ = "Yuval Malkan"

import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from CoreTools.AccountByEmail import scan_email

"""
Complete OSINT scan for an email across all available sources.
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


def search_email_complete(email: str) -> dict:
    email = email.strip().lower()
    report = {
        "query": email,
        "timestamp": None,
        "sources": {},
        "summary": {}
    }

    import time
    start_time = time.time()

    functions_to_run = [
        (scan_email, "email_accounts", 60, email),
    ]

    with ThreadPoolExecutor(max_workers=1) as executor:
        future_to_key = {}
        for func, key, timeout, *args in functions_to_run:
            future = executor.submit(run_function_with_timeout, func, timeout, *args)
            future_to_key[future] = key

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                report["sources"][key] = future.result()
            except Exception as e:
                report["sources"][key] = {"error": str(e)}

    report["summary"] = _build_email_summary(report["sources"], email)
    report["elapsed_seconds"] = round(time.time() - start_time, 2)

    return report


def _build_email_summary(sources: dict, email: str) -> dict:
    """Extract and combine key findings from all sources"""
    summary = {
        "total_accounts_found": 0,
        "platforms": [],
    }

    # Email accounts results
    email_data = sources.get("email_accounts", {})
    if isinstance(email_data, dict):
        found_accounts = email_data.get("found_accounts", [])
        summary["total_accounts_found"] = email_data.get("total_found", 0)
        summary["total_scanned"] = email_data.get("total_scanned", 0)

        for account in found_accounts:
            summary["platforms"].append({
                "site": account.get("site"),
                "url": account.get("url"),
                "category": account.get("category", "unknown")
            })

    return summary


def print_email_report(report: dict):
    """Pretty print the email search report"""
    email = report.get("query", "?")
    elapsed = report.get("elapsed_seconds", "?")

    print("\n" + "=" * 70)
    print(f"  NEURON EMAIL OSINT — {email}  ({elapsed}s)")
    print("=" * 70)

    summary = report.get("summary", {})

    total_found = summary.get("total_accounts_found", 0)
    total_scanned = summary.get("total_scanned", 0)

    print(f"\n[EMAIL SCAN SUMMARY]")
    print(f"  Total Scanned: {total_scanned}")
    print(f"  Total Found: {total_found}")

    platforms = summary.get("platforms", [])
    if platforms:
        print(f"\n[PLATFORMS WHERE EMAIL IS REGISTERED] ({len(platforms)} accounts)")
        for i, platform in enumerate(platforms, 1):
            print(f"  {i}. {platform.get('site')}")
            print(f"     Category: {platform.get('category')}")
            print(f"     {platform.get('url')}")

    print("\n" + "=" * 70)


def save_email_report(report: dict):
    """Save the complete report to JSON in temp folder"""
    import os

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    TEMP_FOLDER = os.path.join(BASE_DIR, "temp")
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    email = report.get("query", "unknown")
    filename = f"osint_email_{email}.json"
    filepath = os.path.join(TEMP_FOLDER, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return filepath


if __name__ == "__main__":
    email = input("Enter email to search: ").strip()

    if not email:
        print("No email provided!")
        exit(1)

    print(f"\nSearching for {email}...")
    report = search_email_complete(email)

    print_email_report(report)

    filepath = save_email_report(report)
    print(f"Report saved to: {filepath}\n")