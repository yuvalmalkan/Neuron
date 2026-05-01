__author__ = "Yuval Malkan"

import os
import logging
import requests
from Constants import debug
import re
from playwright.sync_api import sync_playwright
import time

TEMP_FOLDER_PATH = "temp/"


def downloadHtml(url):
    """
    args: url
    returns: void, downloads html into temp folder

    """
    try:

        path_part = url.split("://")[-1]  # "www.instagram.com/john.doe/"

        # For Instagram, extract username from URL if possible
        if "instagram.com/" in path_part:

            username = path_part.split("instagram.com/")[-1].rstrip("/")
            print(f"1 {username}")
            filename = f"instagram_{username}" # fixme remove hardcoded instagram


        else:
            # For other URLs, sanitize but keep dots in the actual content
            filename = path_part.replace("/", "_").replace("?", "_").replace("&", "_")


        # Remove any remaining problematic characters
        filename = filename.replace(":", "_")

        if not filename:
            filename = "webpage"

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}


        logging.info(f"downloading {filename}...")

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        filepath = os.path.join(TEMP_FOLDER_PATH, f'{filename}.html')

        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(response.text)

        logging.debug(f"Saved to {filepath}")

    except Exception as e:
        logging.error(f"Error: {e}")





def downloadRenderedHtml(url):
    """
    args: website url
    returns: void, downloads html into temp folder
    """
    with sync_playwright() as p:

        path_part = url.split("://")[-1]
        filename = path_part.replace("/", "_").replace("?", "_").replace("&", "_")
        filename = filename.replace(":", "_")


        # Launch a headless Chromium browser
        browser = p.chromium.launch(headless=True)

        # Add a normal User-Agent so Facebook doesn't immediately flag you as a bot
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        logging.info(f"Navigating to {url}...")

        # wait_until="networkidle" tells the script to wait until network activity calms down
        try:
            page.goto(url, wait_until="networkidle", timeout=15000)

        except Exception as e:
            logging.error(f"Page loaded, but hit a timeout waiting for network to idle: {e}")

        # Optional: Wait a couple of extra seconds for React to finish rendering DOM elements
        time.sleep(3)

        # Extract the fully rendered HTML
        html_content = page.content()

        filepath = os.path.join(TEMP_FOLDER_PATH, f'{filename}.html')

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Successfully saved to {filename}")
        browser.close()





#todo move to linkedin.py, add proper logging and make it better
from playwright.sync_api import sync_playwright
import re


def scrape_linkedin_osint(profile_url):
    """
    The safest free OSINT scraper. Uses a visible browser, forces US network
    headers to prevent local IP language bleeds, and crushes cookie walls.
    """
    clean_url = re.sub(r"https?://(www\.)?", "", profile_url).rstrip("/).,?'\"")
    print(f"🕵️‍♂️ Booting OSINT browser for: {clean_url}...\n")
    search_query = f"site:{clean_url}"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        # --- THE IDENTITY FORGE ---
        # Force the deep network headers so Google doesn't fall back to your physical IP's language
        context = browser.new_context(
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9"
            },
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            # We still keep the URL parameters as a second layer of defense
            page.goto(f"https://www.google.com/search?q={search_query}&hl=en&gl=us")

            # --- 1. THE CAPTCHA HANDLER ---
            if "unusual traffic" in page.content() or "reCAPTCHA" in page.content():
                print("🛑 GOOGLE CAPTCHA DETECTED!")
                print("👉 Please look at the Chrome window and solve the CAPTCHA manually.")
                print("⏳ Waiting for you to solve it (60s timeout)...")
                page.wait_for_selector('h3', timeout=60000)
                print("✅ CAPTCHA solved! Proceeding...\n")

            # --- 2. THE COOKIE CRUSHER ---
            try:
                reject_button = page.locator("button:has-text('Reject all')")
                if reject_button.count() > 0:
                    reject_button.first.click()
                    page.wait_for_load_state('networkidle')
            except Exception:
                pass

                # --- 3. EXTRACTION ---
            page.wait_for_selector('h3', timeout=5000)
            html_content = page.content()

            if "did not match any documents" in html_content:
                print("❌ Google has zero records for this exact URL. The profile is hidden from search engines.")
                return

            title_element = page.locator('h3').first
            snippet_element = page.locator('.VwiC3b').first

            if title_element.count() > 0:
                print(f"👤 Name & Headline: {title_element.inner_text()}")

            if snippet_element.count() > 0:
                snippet = snippet_element.inner_text()
                print(f"📝 Public Data Snippet:\n{snippet}\n")
                # --- 4. BILINGUAL SMART METRIC PARSER ---
                # Search for English OR Hebrew follower/connection keywords using Regex
                # This ignores invisible Right-To-Left formatting characters

                # We look for a number (with optional K/M or commas) followed by the keyword
                match = re.search(r'([\d\.,]+[KM]?)\s*(?:followers|connections|עוקבים|חיבורים)', snippet, re.IGNORECASE)

                if match:
                    raw_count = match.group(1).upper().replace(",", "")

                    # Split the number from the K/M multiplier
                    num_match = re.search(r'([\d\.]+)([KM]?)', raw_count)
                    if num_match:
                        number = float(num_match.group(1))
                        multiplier = num_match.group(2)

                        if multiplier == 'K':
                            number *= 1_000
                        elif multiplier == 'M':
                            number *= 1_000_000

                        # If it found 'חיבורים' or 'connections', label it appropriately
                        label = "Connections" if "חיבורים" in snippet or "connections" in snippet.lower() else "Followers"
                        print(f"📈 Estimated {label}: {int(number):,}")

        except Exception as e:
            print(f"❌ Automation error: {e}")

        finally:
            page.wait_for_timeout(1500)
            browser.close()


# --- Test it out ---
# scrape_linkedin_osint("https://www.linkedin.com/in/avigail-nissan-9b7a44377")


if __name__ == "__main__":
    #user = input("insta username: ")
    #downloadHtml(f"https://www.instagram.com/{user}/")
    #downloadHtml("https://www.facebook.com/oshri.bouhnik")
    #downloadRenderedHtml("https://www.facebook.com/oshri.bouhnik")
    scrape_linkedin_osint("https://www.linkedin.com/in/yoni-yagur-92953739b/")