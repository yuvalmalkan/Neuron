__author__ = 'Yuval Malkan'

import re
import json
import os
import logging
from Constants import debug
import html

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")




#todo maybe add a automatic bypass to login wall by clicking x

def get_info_from_html(filename: str) -> dict:
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


if __name__ == "__main__":
    filename = input("Enter filename: ")
    result = get_info_from_html(filename)
    for key, value in result.items():
        print(f"{key}: {value}")
