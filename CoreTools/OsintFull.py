__author__ = "Yuval Malkan"

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from Maigret import Maigret_search_username
from Sherlock import sherlock_search_username
from accountFinder import findByUsername
from CoreTools.SocialMedia.Telegram import lookup_username_sync

"""
Full OSINT scan with multi-threaded execution for speed.
Each tool runs in parallel to minimize total scanning time.
"""


def run_function_with_timeout(func, timeout, *args, **kwargs):
    """Run function with timeout protection"""
    try:
        # Wrap in a thread with timeout
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


def OsintByUsername(username: str, timeout_per_func: int = 60, skip_slow: bool = False) -> dict:
    """
    Scan username across multiple OSINT sources in parallel.

    Args:
        username: Target username to scan
        timeout_per_func: Max seconds per function (default 60)
        skip_slow: If True, skip Sherlock & Maigret (very slow). Default False

    Returns:
        Dictionary with results from all sources
    """
    results = {}

    # Define all functions with their timeout preferences
    functions_to_run = []

    if not skip_slow:
        functions_to_run.extend([
            (sherlock_search_username, "sherlock", 90, username),  # ~60-90s
            (Maigret_search_username, "maigret", 90, username),  # ~60-90s
        ])

    # Fast functions
    functions_to_run.extend([
        (findByUsername, "accountFinder", timeout_per_func, username),  # ~20-30s
        (lookup_username_sync, "telegram", timeout_per_func, username),  # ~10-20s
    ])

    # Use ThreadPoolExecutor for cleaner parallel execution
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_key = {}

        for func, key, timeout, *args in functions_to_run:
            future = executor.submit(run_function_with_timeout, func, timeout, *args)
            future_to_key[future] = key

        # Collect results as they complete (not waiting for slowest)
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"error": str(e)}

    return results


def OsintByUsernameQuick(username: str) -> dict:
    """Quick scan - skip slow functions like Sherlock/Maigret"""
    return OsintByUsername(username, timeout_per_func=30, skip_slow=True)


if __name__ == "__main__":
    username = input("Enter username to scan: ")

    print("\n[1] Full scan (includes Sherlock & Maigret) - ~2-3 minutes")
    print("[2] Quick scan (skip slow tools) - ~30 seconds")
    choice = input("Choose [1] or [2] (default 2): ").strip() or "2"

    if choice == "1":
        report = OsintByUsername(username)
    else:
        report = OsintByUsernameQuick(username)

    print("\n" + "=" * 50)
    for tool, data in report.items():
        print(f"\n[{tool.upper()}]")
        if isinstance(data, dict) and "error" in data:
            print(f"  ❌ {data['error']}")
        else:
            print(f"  ✓ {str(data)[:100]}...")