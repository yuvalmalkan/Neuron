__author__ = 'Yuval Malkan'

import re
import json
import os
import logging
from Constants import debug
import html

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

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
            followers_str = followers.group(1)
            profile["followers"] = followers_str


        following = re.search(r'(\d+[,\d]*)\s+Following', data)
        if following:
            profile["following"] = following.group(1)



        posts = re.search(r'(\d+)\s+Posts', data)
        if posts:
            profile["number_of_posts"] = int(posts.group(1))




        display_name = re.search(r'Posts\s+-\s+([^(]+?)\s+\(&#064;', data)
        if display_name:
            display_name = display_name.group(1).strip()
            textToRemove = "See Instagram photos and videos from "
            display_name = display_name[len(textToRemove)::]
            profile["display_name"] = display_name




        username = re.search(r'&#064;([^)]+)\)', data)
        if username:
            profile["username"] = username.group(1)


        bio = re.search(r'on Instagram:\s+&quot;([^&]*)', data)
        if bio:
            profile["bio"] = bio.group(1)



        profile_picture_url = re.search(r'property="og:image"\s+content="([^"]*)"', data)
        if profile_picture_url:
            profile["profile_picture_url"] = fix_profile_pic_url(profile_picture_url.group(1))


        profile_url = f"https://www.instagram.com/{profile['username']}/"
        profile["profile_url"] = profile_url



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








if __name__ == "__main__":

    print(get_info_from_html("www_instagram_com_____darco____.html"))



