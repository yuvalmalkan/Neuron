__author__ = 'Yuval Malkan'


def get_info_from_html(filePath: str) -> dict:
    """
    Get profile info from html file,

    args: html file path
    return: profile info as dict, e.g. {"username": "yuvalmalkan", "full_name": "Yuval Malkan", "bio": "Software Engineer", ...}
    """

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



    with open(filePath, "r", encoding="utf-8") as data:
        data = data.read()










