__author__ = 'Yuval Malkan'

import re
import json
import os
import logging
from Constants import debug
import html
import requests
import json
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")
TEMP_FOLDER_PATH = TEMP_FOLDER



#todo maybe add a automatic bypass to login wall by clicking x

def Facebook_info_from_file(filename: str) -> dict:
    """
    Extracts profile information from a Facebook HTML file.

    Args:
        filename: HTML filename from temp folder

    Returns:
        Dictionary containing profile information including:
        - username/vanity
        - display_name
        - profile_url
        - profile_picture_url
        - user_id
        - work_info
        - education_info
        - photos_urls
    """
    filePath = os.path.join(TEMP_FOLDER, filename)

    profile = {
        "username": "",
        "display_name": "",
        "profile_url": "",
        "profile_picture_url": "",
        "user_id": "",
        "work_info": [],
        "education_info": [],
        "photos": [],
        "bio": "",
        "followers": "",
        "following": ""
    }

    try:
        with open(filePath, "r", encoding="utf-8") as file:
            data = file.read()

        # Extract display name from og:title meta tag
        display_name_match = re.search(r'<meta property="og:title" content="([^"]+)"', data)
        if display_name_match:
            profile["display_name"] = display_name_match.group(1).strip()

        # Extract profile picture URL from og:image
        profile_pic_match = re.search(r'<meta property="og:image" content="([^"]+)"', data)
        if profile_pic_match:
            profile["profile_picture_url"] = fix_profile_pic_url(profile_pic_match.group(1))

        # Extract vanity/username from og:url
        url_match = re.search(r'<meta property="og:url" content="https://www\.facebook\.com/([^"/?]+)"', data)
        if url_match:
            profile["username"] = url_match.group(1)
            profile["profile_url"] = f"https://www.facebook.com/{profile['username']}"

        # Extract user ID from meta tags or JavaScript data
        user_id_match = re.search(r'"userID":"(\d+)"', data)
        if not user_id_match:
            user_id_match = re.search(r'id":"(pfbid[^"]+)"', data)
        if user_id_match:
            profile["user_id"] = user_id_match.group(1)

        # Extract profile description/bio from og:description
        bio_match = re.search(r'<meta property="og:description" content="([^"]+)"', data)
        if bio_match:
            profile["bio"] = bio_match.group(1).strip()

        # Extract work information from JSON data
        work_info = extract_work_info(data)
        if work_info:
            profile["work_info"] = work_info

        # Extract education information
        education_info = extract_education_info(data)
        if education_info:
            profile["education_info"] = education_info

        # Extract photo URLs
        photos = extract_photos(data)
        if photos:
            profile["photos"] = photos

        # Extract follower/following counts if available
        followers_match = re.search(r'(\d+[KM]?)\s+followers', data, re.IGNORECASE)
        if followers_match:
            profile["followers"] = followers_match.group(1)

        following_match = re.search(r'(\d+[KM]?)\s+following', data, re.IGNORECASE)
        if following_match:
            profile["following"] = following_match.group(1)

    except Exception as e:
        logging.error(f"Error parsing HTML file {filename}: {str(e)}")

    return profile


def extract_work_info(data: str) -> list:
    """
    Extracts work information from the HTML JSON data.

    Args:
        data: HTML content as string

    Returns:
        List of work information dictionaries
    """
    work_items = []
    try:
        # Look for work section in the JSON-embedded data
        work_pattern = r'"title":\s*{\s*"text":"([^"]+)"[^}]*}[^}]*"field_section_type":"work"'
        matches = re.finditer(work_pattern, data, re.DOTALL)
        for match in matches:
            work_items.append({
                "company": match.group(1),
                "position": ""
            })
    except Exception as e:
        logging.warning(f"Could not extract work info: {str(e)}")

    return work_items


def extract_education_info(data: str) -> list:
    """
    Extracts education information from the HTML JSON data.

    Args:
        data: HTML content as string

    Returns:
        List of education information dictionaries
    """
    education_items = []
    try:
        # Look for education/college sections
        edu_pattern = r'"field_section_type":"(?:college|secondary_school)"[^}]*"title":\s*{\s*"text":"([^"]+)"'
        matches = re.finditer(edu_pattern, data, re.DOTALL)
        for match in matches:
            education_items.append({
                "school": match.group(1),
                "type": "school"
            })
    except Exception as e:
        logging.warning(f"Could not extract education info: {str(e)}")

    return education_items


def extract_photos(data: str) -> list:
    """
    Extracts photo URLs from the HTML data.

    Args:
        data: HTML content as string

    Returns:
        List of photo URLs
    """
    photos = []
    try:
        # Extract photo URLs from src attributes and image URLs
        photo_pattern = r'"uri":"(https://scontent[^"]+)"'
        matches = re.finditer(photo_pattern, data)

        seen_urls = set()  # Avoid duplicates
        for match in matches:
            url = match.group(1)
            # Filter for actual image URLs and avoid duplicates
            if "_n.jpg" in url or "_n.png" in url or ".webp" in url:
                if url not in seen_urls and len(photos) < 20:  # Limit to 20 photos
                    photos.append(fix_profile_pic_url(url))
                    seen_urls.add(url)
    except Exception as e:
        logging.warning(f"Could not extract photos: {str(e)}")

    return photos


def fix_profile_pic_url(url: str) -> str:
    """
    Cleans HTML-encoded characters from a URL and removes
    trailing separators that can cause hash mismatches.

    Args:
        url: String URL

    Returns:
        String cleaned URL
    """
    fixed_url = html.unescape(url)
    fixed_url = fixed_url.rstrip('&')

    return fixed_url





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


def FacebookDownloadRenderedHtml(url): #fixme make it download all the informatin facebook
    """
    Downloads Facebook profile HTML with better popup handling and scrolling for dynamic content
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
            logging.error(f"Page loaded, but hit a timeout: {e}")

        time.sleep(3)

        # Close any login popups
        if close_login_popup(page):
            logging.info("Login popup closed, waiting for content to load...")
            time.sleep(5)  # IMPORTANT: Wait for content to render

            # CRUCIAL: Scroll multiple times to trigger lazy-loading of all profile data
            # Photos, work info, education, and other details load as you scroll
            logging.info("Scrolling profile to load dynamic content...")
            for scroll_iter in range(6):  # Scroll 6 times
                page.evaluate("window.scrollBy(0, window.innerHeight);")
                time.sleep(1)  # Wait for content to load after each scroll

            # Scroll back to top to ensure all visible content is in the DOM
            page.evaluate("window.scrollTo(0, 0);")
            time.sleep(2)

            # Final wait for network to settle
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass

        time.sleep(2)

        # Extract the fully rendered HTML
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






def FullFacebookScan(username) -> dict:
    """
        scans facebook profile page
        downloading the rendered html and extracting information from it
        args: username
        returns: dict with profile information


    """
    url = "https://www.facebook.com/" + username
    FacebookDownloadRenderedHtml(url)
    path_part = url.split("://")[-1]
    filename = path_part.replace("/", "_").replace("?", "_").replace("&", "_")
    filename = filename.replace(":", "_")
    filepath = os.path.join(TEMP_FOLDER_PATH, f'{filename}.html')
    result = Facebook_info_from_file(filepath)
    return result





if __name__ == "__main__":
    result = FullFacebookScan("https://www.facebook.com/oshri.bouhnik")
    for key, value in result.items():
        print(f"{key}: {value}")
