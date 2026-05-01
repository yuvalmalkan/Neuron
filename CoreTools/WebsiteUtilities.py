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









if __name__ == "__main__":
    #user = input("insta username: ")
    #downloadHtml(f"https://www.instagram.com/{user}/")
    downloadHtml("https://www.facebook.com/oshri.bouhnik")
    #download_rendered_html("https://www.facebook.com/oshri.bouhnik")