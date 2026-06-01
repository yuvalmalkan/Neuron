__author__ = "Yuval Malkan"

import logging

#global session data
_session = {
    'user_id': None,
    'username': None,
    'email': None,
    'logged_in': False
}


def set_session(user_id, username, email):
    """
    Store user session data after successful login.

    Args:
        user_id: Unique user identifier
        username: Username
        email: User email
    """
    global _session
    _session['user_id'] = user_id
    _session['username'] = username
    _session['email'] = email
    _session['logged_in'] = True
    logging.info(f"Session started for user: {username}")


def get_session():
    """
    Get current session data.

    Returns:
        dict: Copy of session dictionary
    """
    return _session.copy()


def get_user_id():
    """
    Get current logged-in user ID.

    Returns:
        str: User ID or None if not logged in
    """
    return _session['user_id']


def get_username():
    """
    Get current logged-in username.

    Returns:
        str: Username or None if not logged in
    """
    return _session['username']


def get_email():
    """
    Get current logged-in email.

    Returns:
        str: Email or None if not logged in
    """
    return _session['email']


def is_logged_in():
    """
    Check if user is logged in.

    Returns:
        bool: True if logged in, False otherwise
    """
    return _session['logged_in']


def clear_session():
    """
    Clear session data on logout.
    """
    global _session
    _session = {
        'user_id': None,
        'username': None,
        'email': None,
        'logged_in': False
    }
    logging.info("Session cleared")
