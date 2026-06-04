__author__ = "Yuval Malkan"

import logging
from User import User
from UserDatabase import UserDatabase
from EncryptionManager import verify_password_argon2
from Constants import RESP_LOGIN_OK, RESP_LOGIN_FAIL, RESP_LOGIN_USER_NOT_FOUND, PASSWORD_PEPPER


def handle_login(username: str, password: str, db: UserDatabase) -> tuple[bool, str, User | None]:
    """
    Handle user login with credential verification.
    
    Args:
        username: Username to login
        password: Password to verify (plain text)
        db: UserDatabase instance
        
    Returns:
        Tuple of (success: bool, response_code: str, user: User | None)
    """
    try:
        # Look up user by username
        user = db.get_user(username)
        
        if not user:
            logging.warning(f"Login failed: user '{username}' not found")
            return False, RESP_LOGIN_USER_NOT_FOUND, None



        # Verify password hash
        peppered_password = password + PASSWORD_PEPPER
        if not verify_password_argon2(user.password_hash, peppered_password):
            logging.warning(f"Login failed: incorrect password for '{username}'")
            return False, RESP_LOGIN_FAIL, None


        logging.info(f"User login successful: {username} ({user.unique_id})")
        return True, RESP_LOGIN_OK, user

    except Exception as e:
        logging.error(f"Unexpected error during login: {e}")
        return False, "ERROR", None
