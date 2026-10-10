__author__ = 'Yuval Malkan'

import re
import json
import os
import logging
from Constants import debug
import html
import time

#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")


def get_info_from_html(filename: str) -> dict:
    """
    args: html filename(from temp folder)
    returns: profile info in a dict
    """
    filePath = os.path.join(TEMP_FOLDER, filename)

    profile = {
        "username": "",
        "display_name": "",
        "bio": "",
        "profile_picture_url": "",
        "followers": "",
        "following": "",
        "profile_url": "",
        "number_of_posts": 0
    }

    with open(filePath, "r", encoding="utf-8") as file:
        data = file.read()

        followers = re.search(r'(\d+[KM]?)\s+Followers', data)
        if followers:
            profile["followers"] = followers.group(1)

        following = re.search(r'(\d+[,\d]*)\s+Following', data)
        if following:
            profile["following"] = following.group(1)

        posts = re.search(r'(\d+)\s+Posts', data)
        if posts:
            profile["number_of_posts"] = int(posts.group(1))

        # FIXED: Extract display name using the og:title meta tag
        display_name = re.search(r'<meta property="og:title" content="([^&#]+)', data)
        if display_name:
            profile["display_name"] = display_name.group(1).strip()

        # FIXED: Extract username using the reliable canonical link tag
        username = re.search(r'<link rel="canonical" href="https://www.instagram.com/([^/]+)/"', data)
        if username:
            profile["username"] = username.group(1)
        else:
            # Fallback that restricts extraction to valid Instagram characters only (no HTML)
            username = re.search(r'&#064;([a-zA-Z0-9_.]+)', data)
            if username:
                profile["username"] = username.group(1)

        # FIXED: Extract bio more accurately
        bio = re.search(r'on Instagram:\s+&quot;(.*?)&quot;', data)
        if bio:
            profile["bio"] = bio.group(1)

        profile_picture_url = re.search(r'property="og:image"\s+content="([^"]*)"', data)
        if profile_picture_url:
            profile["profile_picture_url"] = fix_profile_pic_url(profile_picture_url.group(1))

        # Now that the username is HTML-free, the link will assemble correctly
        profile["profile_url"] = f"https://www.instagram.com/{profile['username']}/" if profile['username'] else ""

    return profile




def fix_profile_pic_url(url: str) -> str:
    """
    Cleans HTML-encoded characters from a URL and removes
    trailing separators that can cause hash mismatches.

    args: string url
    returns: string cleaned url
    """

    fixed_url = html.unescape(url)
    fixed_url = fixed_url.rstrip('&')

    return fixed_url

def InstagramFullScan(username) -> dict:
    from CoreTools.WebsiteUtilities import downloadHtml

    #download the Instagram profile page
    downloadHtml(f"https://www.instagram.com/{username}/")
    time.sleep(2)


    #make filename for the downloaded html
    filename = f"instagram_{username}.html"


    #extract and return profile information
    try:
        profile_info = get_info_from_html(filename)
        return profile_info
    except Exception as e:
        logging.error(f"Error extracting Instagram info for {username}: {e}")
        return {"error": str(e)}


if __name__ == "__main__":

    filename = input("Enter filename ")
    #print(get_info_from_html(filename))
    print(InstagramFullScan(filename))



