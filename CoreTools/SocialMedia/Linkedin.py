__author__ = "Yuval Malkan"

#cant scrape linkedin without login, and login requires captcha, so i will not implement it for now

from playwright.sync_api import sync_playwright
import re
import logging



def scrape_linkedin_osint(profile_url): #fixme add proper logging and make it better
    """
    args: string profile_url (linkedin profile URL)
    returns: void # todo make it return a dict with the scraped info or something similar


    visible browser
    bypasses cookie walls

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
                print(f"Name & Headline: {title_element.inner_text()}")

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


