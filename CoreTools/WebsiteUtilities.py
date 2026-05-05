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
            filename = f"instagram_{username}"  # fixme remove hardcoded instagram


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




def close_login_popup(page):
    """
    Detects and closes Facebook login popups by clicking the X button.

    Args:
        page: Playwright page object

    Returns:
        bool: True if popup was closed, False if no popup found
    """
    try:
        # Wait a moment for popup to appear if it exists
        time.sleep(1)

        # Multiple selectors for the close button across different Facebook layouts
        close_button_selectors = [
            'button[aria-label="Close"]',
            'button[aria-label="close"]',
            'div[role="button"][aria-label="Close"]',
            'div[role="button"][aria-label="close"]',
            'button.x9f619.x1iyjqo2',  # Facebook's X button class
            '[data-testid="modal_close_button"]',
            'button[aria-label*="Close"]',
            'svg[aria-label="Close"] ..',  # SVG close icon
            '.x1iyjqo2.xs83m0k.x6ikm8r.x10wlt62',  # Another close button variant
        ]

        popup_selectors = [
            '[role="dialog"]',
            '.xw3o3--iframe',
            '.x9f619',
        ]

        # Check if a popup/dialog is visible
        for popup_selector in popup_selectors:
            try:
                popups = page.query_selector_all(popup_selector)
                if popups:
                    logging.info(f"Found popup with selector: {popup_selector}")

                    # Try to find and click the close button within the popup
                    for close_selector in close_button_selectors:
                        try:
                            close_button = page.query_selector(close_selector)
                            if close_button:
                                logging.info(f"Found close button: {close_selector}")
                                page.click(close_selector)
                                time.sleep(1)  # Wait for popup to close
                                logging.info("Successfully closed login popup")
                                return True
                        except Exception:
                            continue
            except Exception:
                continue

        return False

    except Exception as e:
        logging.warning(f"Error handling login popup: {e}")
        return False


def FacebookDownloadRenderedHtml(url):
    """
    Downloads Facebook profile with better popup handling and content loading
    """
    with sync_playwright() as p:
        path_part = url.split("://")[-1]
        filename = path_part.replace("/", "_").replace("?", "_").replace("&", "_")
        filename = filename.replace(":", "_")

        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        logging.info(f"Navigating to {url}...")
        try:
            page.goto(url, wait_until="networkidle", timeout=15000)
        except Exception as e:
            logging.error(f"Timeout: {e}")

        time.sleep(3)  # Increased from 2 to 3

        # Close any login popups
        if close_login_popup(page):
            logging.info("Popup closed, waiting for content to load...")
            time.sleep(5)  # INCREASE THIS - was 2, now 5 seconds

            # Scroll to load dynamic content
            page.evaluate("window.scrollBy(0, window.innerHeight * 3)")
            time.sleep(3)

            # Scroll back to top
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(2)

            # Wait for page to settle
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass

        time.sleep(2)

        html_content = page.content()
        filepath = os.path.join(TEMP_FOLDER_PATH, f'{filename}.html')

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Successfully saved to {filename}")
        browser.close()




def FacebookDownloadRenderedHtmlWithRetry(url, max_retries=3):
    """
    Downloads Facebook profile HTML with retry logic for popup handling.

    Args:
        url: Facebook profile URL
        max_retries: Maximum number of retry attempts

    Returns:
        str: Filename if successful, None if failed
    """
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1}/{max_retries}")
            FacebookDownloadRenderedHtml(url)

            # Check if the HTML was successfully saved and contains meaningful data
            path_part = url.split("://")[-1]
            filename = path_part.replace("/", "_").replace("?", "_").replace("&", "_")
            filename = filename.replace(":", "_")
            filepath = os.path.join(TEMP_FOLDER_PATH, f'{filename}.html')

            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check for common Facebook profile indicators
                    if 'og:title' in content or 'profile' in content.lower():
                        logging.info(f"Successfully downloaded and verified Facebook profile")
                        return filename
                    else:
                        logging.warning(f"HTML downloaded but may contain popup or error page")

        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {e}")

        if attempt < max_retries - 1:
            logging.info(f"Retrying in 2 seconds...")
            time.sleep(2)

    logging.error(f"Failed to download Facebook profile after {max_retries} attempts")
    return None





if __name__ == "__main__":
    user = input("username: ")
    # downloadHtml(f"https://www.instagram.com/{user}/")
    FacebookDownloadRenderedHtmlWithRetry("https://www.facebook.com/wrytrwzn.883988")
    # downloadRenderedHtml(f"https://www.tiktok.com/@shaniamramm") #not working