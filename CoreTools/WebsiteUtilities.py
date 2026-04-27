__author__ = "Yuval Malkan"

import os
import logging
import requests
from Constants import debug

TEMP_FOLDER_PATH = "temp/"


def downloadHtml(url):
    try:

        filename = url.split("://")[-1].replace("/", "_").replace(".", "_").replace("?", "_")

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
    user = input("insta username: ")
    downloadHtml(f"https://www.instagram.com/{user}/")