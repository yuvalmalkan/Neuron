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










if __name__ == "__main__":
    user = input("username: ")
    #downloadHtml(f"https://www.instagram.com/{user}/")
    #downloadHtml("https://www.instagram.com/tre6enjoyer/")
    # downloadRenderedHtml(f"https://www.tiktok.com/@shaniamramm") #not working