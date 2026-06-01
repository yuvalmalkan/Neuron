__author__ = "Yuval Malkan"

import subprocess
import threading
import time

def sherlock_search_username(username: str) -> list:
    # Timer that prints elapsed time every second
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
            ["sherlock", username, "--print-found", "--no-color"],
            capture_output=True,
            text=True,
        )
    finally:
        stop_timer.set()
        timer_thread.join()
        print()  # newline after timer

    found = []
    for line in result.stdout.split("\n"):
        if "[+]" in line:
            parts = line.replace("[+]", "").strip().split(": ", 1)
            if len(parts) == 2:
                found.append({
                    "site": parts[0].strip(),
                    "url":  parts[1].strip()
                })

    total_time = round(time.time() - start_time, 1)
    print(f"done in {total_time}s — found {len(found)} accounts")
    return found


if __name__ == "__main__":
    user =input("username: ")
    results = sherlock_search_username(user)
    print()
    for r in results:
        print(f"{r['site']}: {r['url']}")