__author__ = 'Yuval Malkan'

import re

def parse_target_input(text: str) -> dict:
    """
    Extract structured fields from free-form target description.

    args: user input string
    returns: dictionary with structured fields

    """
    result = {}

    # Phone
    phone_match = re.search(r'(\+?[\d\-\s]{7,15})', text)
    if phone_match:
        result['phone'] = phone_match.group(1).strip()

    # Email
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', text, re.I)
    if email_match:
        result['email'] = email_match.group(0)

    # Username: @handle
    user_match = re.search(r'@([\w._]+)', text)
    if user_match:
        result['username'] = user_match.group(1)

    # Name: anything before a comma, or after keywords like "name:" / "scan "
    name_match = re.search(r'(?:scan|name[:\s]+)([A-Za-z ]{3,30})', text, re.I)
    if name_match:
        result['name'] = name_match.group(1).strip()

    return result