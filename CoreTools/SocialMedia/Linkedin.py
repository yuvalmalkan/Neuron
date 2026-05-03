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

    sometimes a captcha will appear, in that case it will prompt the user to solve it manually

    """

    clean_url = re.sub(r"https?://(www\.)?", "", profile_url).rstrip("/).,?'\"")
    logging.info(f"Booting browser for: {clean_url}...\n")
    search_query = f"site:{clean_url}"

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )


        #so the results will be english only
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

            page.goto(f"https://www.google.com/search?q={search_query}&hl=en&gl=us")

            #if a captcha appeared do this
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
                logging.info("Google has zero records for this exact URL. The profile is hidden from search engines.")
                return


            title_element = page.locator('h3').first
            snippet_element = page.locator('.VwiC3b').first

            if title_element.count() > 0:
                print(f"Name & Headline: {title_element.inner_text()}")

            if snippet_element.count() > 0:
                snippet = snippet_element.inner_text()

                print(f"Public Data Snippet:\n{snippet}\n") #todo add auto transliation for public data

                #look for a number followed by k or m
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

                        # translate
                        label = "Connections" if "חיבורים" in snippet or "connections" in snippet.lower() else "Followers"
                        print(f"estimated {label}: {int(number):,}")

        except Exception as e:
            logging.error(f"Automation error: {e}")

        finally:
            page.wait_for_timeout(1500)
            browser.close()


