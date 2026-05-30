__author__ = 'Yuval Malkan'

import re

def parse_target_input(text: str) -> dict:
    result = {}

    # Email — must match before username so @domain isn't grabbed as a handle
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', text, re.I)
    if email_match:
        result['email'] = email_match.group(0)
        # Remove the matched email from text before searching for @username
        remaining = text[:email_match.start()] + text[email_match.end():]
    else:
        remaining = text

    # Username: @handle (searched on text with email removed)
    user_match = re.search(r'@([\w._]+)', remaining)
    if user_match:
        result['username'] = user_match.group(1)

    # Phone
    phone_match = re.search(r'(\+?[\d\-\s]{7,15})', text)
    if phone_match:
        result['phone'] = phone_match.group(1).strip()

    # Name
    name_match = re.search(r'(?:scan|name[:\s]+)([A-Za-z ]{3,30})', text, re.I)
    if name_match:
        result['name'] = name_match.group(1).strip()

    return result