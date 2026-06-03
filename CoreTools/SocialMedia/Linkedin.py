__author__ = "Yuval Malkan"

from playwright.sync_api import sync_playwright
import re
import logging


def scrape_linkedin_osint(full_name):
    """
    args: string Firstname Lastname
    returns: dict with scraped LinkedIn profile data

    visible browser
    bypasses cookie walls
    sometimes a captcha will appear, in that case it will prompt the user to solve it manually
    """

    logging.info(f"Booting browser to search for: {full_name}...\n")

    #dork query using the provided name
    search_query = f"site:linkedin.com/in {full_name}"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        #english results
        context = browser.new_context(
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9"
            },
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        data = None

        try:

            snippet = None
            label = None
            number = None
            match = None
            profile_url = None

            page.goto(f"https://www.google.com/search?q={search_query}&hl=en&gl=us")

            #handle CAPTCHA
            if "unusual traffic" in page.content() or "reCAPTCHA" in page.content():
                logging.warning("GOOGLE CAPTCHA DETECTED!")
                logging.warning("Please look at the Chrome window and solve the CAPTCHA manually.")
                logging.warning("Waiting for you to solve it (60s timeout)...")
                page.wait_for_selector('h3', timeout=60000)
                logging.warning("CAPTCHA solved! Proceeding...\n")

            #bypass cookie wall if it appears
            try:
                reject_button = page.locator("button:has-text('Reject all')")
                if reject_button.count() > 0:
                    reject_button.first.click()
                    page.wait_for_load_state('networkidle')
            except Exception:
                pass

            page.wait_for_selector('h3', timeout=5000)
            html_content = page.content()

            if "did not match any documents" in html_content:
                logging.info("Google has zero records for this exact name query. They might not exist or are hidden.")
                return None

            title_element = page.locator('h3').first
            snippet_element = page.locator('.VwiC3b').first

            #extract the actual LinkedIn URL from the search result link wrapper
            link_element = page.locator('a:has(h3)').first
            if link_element.count() > 0:
                profile_url = link_element.get_attribute('href')


            #parse the snippet for connections/followers
            if snippet_element.count() > 0:
                snippet = snippet_element.inner_text()
                match = re.search(r'([\d\.,]+[KM]?)\s*(?:followers|connections|עוקבים|חיבורים)', snippet, re.IGNORECASE)

                if match:
                    raw_count = match.group(1).upper().replace(",", "")

                    #split the number from the K/M multiplier
                    num_match = re.search(r'([\d\.]+)([KM]?)', raw_count)
                    if num_match:
                        number = float(num_match.group(1))
                        multiplier = num_match.group(2)

                        if multiplier == 'K':
                            number *= 1_000
                        elif multiplier == 'M':
                            number *= 1_000_000

                        # Determine label
                        label = "Connections" if "חיבורים" in snippet or "connections" in snippet.lower() else "Followers"

            #return dictionary
            data = {
                "search_target": full_name,
                "discovered_profile_url": profile_url,
                "name_headline": title_element.inner_text() if title_element.count() > 0 else None,
                "public_data_snippet": snippet,
                "connection_type": label,
                "count": int(number) if match else None,
            }

        except Exception as e:
            logging.error(f"Automation error: {e}")

        finally:
            page.wait_for_timeout(1500)
            browser.close()

        return data


if __name__ == "__main__":

    result_dict = scrape_linkedin_osint("test name")
    print(result_dict)