__author__ = "Yuval Malkan"

import subprocess
import threading
import time
import platform
import shutil
import sys

def _subprocess_flags() -> dict:
    #suppress console popup windows on Windows no-op on Mac/Linux
    if platform.system() == "Windows":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}

def _find_sherlock() -> list:
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'sherlock', '--version'],
            capture_output=True, text=True, timeout=5,
            **_subprocess_flags()
        )
        if result.returncode == 0:
            return [sys.executable, '-m', 'sherlock']
    except Exception:
        pass
    #fall back to the script on path
    found = shutil.which('sherlock')
    if found:
        return [found]

    return ['sherlock']

_SHERLOCK_CMD = _find_sherlock()

def sherlock_search_username(username: str) -> list:

    #timer print
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
            _SHERLOCK_CMD + [username, "--print-found", "--no-color"],
            capture_output=True,
            text=True,
            timeout=300,
            **_subprocess_flags()
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