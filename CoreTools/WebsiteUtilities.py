__author__ = "Yuval Malkan"

import logging

import requests


def downloadHtml(url):
    """
    downloads a websites source code

    args: url

    """

    try:

        response = requests.get(url)

        # Check if the request was successful (Status Code 200)
        response.raise_for_status()

        html_content = response.text

        logging.debug("Successfully downloaded source code!")
        # print(html_content)

        with open('page_source.html', 'w', encoding='utf-8') as file:
            file.write(html_content)

    except requests.exceptions.RequestException as e:
        logging.debug(f"An error occurred: {e}")



if __name__ == "__main__":
    downloadHtml("https://www.instagram.com")