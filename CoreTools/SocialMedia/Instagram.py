__author__ = 'Yuval Malkan'

import re
import json
import os


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

TEMP_FOLDER = os.path.join(BASE_DIR, "temp")


def get_info_from_html(filename: str) -> dict:
    """
    Get profile info from html file,

    args: html file path
    return: profile info as dict, e.g. {"username": "yuvalmalkan", "full_name": "Yuval Malkan", "bio": "Software Engineer", ...}
    """

    filePath = os.path.join(TEMP_FOLDER, filename)

    profile = {
        "username": "",
        "display_name": "",
        "bio": "",
        "profile_picture_url": "",
        "followers": 0,
        "following": 0,
        "profile_url": "",
        "number_of_posts": 0
    }



    with open(filePath, "r", encoding="utf-8") as file:
        data = file.read()


        username =  re.search(r"username: (.*)", data) #todo fix search


        if username:
            profile["username"] = username.group(1)

        return profile







if __name__ == "__main__":

    print(get_info_from_html("www_instagram_com_yuvalmalkan_.html"))



