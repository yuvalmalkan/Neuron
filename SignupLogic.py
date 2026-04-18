__author__ = "Yuval Malkan"

import logging
from User import User
from UserDatabase import UserDatabase
from EncryptionManager import hash_password_argon2
from Constants import (
    RESP_SIGNUP_OK, RESP_SIGNUP_USER_EXISTS, RESP_SIGNUP_EMAIL_EXISTS,
    RESP_SIGNUP_INVALID_USERNAME, RESP_SIGNUP_INVALID_EMAIL, RESP_SIGNUP_INVALID_PASSWORD
)


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)"
    
    # Check for at least one uppercase, one lowercase, one digit
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and digits"
    
    return True, ""


def handle_signup(username: str, email: str, password: str, db: UserDatabase) -> tuple[bool, str, User | None]:
    """
    Handle user signup with validation and user creation.
    
    Args:
        username: Desired username
        email: User email address
        password: User password (plain text, will be hashed)
        db: UserDatabase instance
        
    Returns:
        Tuple of (success: bool, response_code: str, user: User | None)
    """
    try:
        # Validate password strength
        pwd_valid, pwd_error = validate_password(password)
        if not pwd_valid:
            logging.warning(f"Signup failed for '{username}': {pwd_error}")
            return False, RESP_SIGNUP_INVALID_PASSWORD, None
        
        # Check if username already exists
        if db.user_exists(username):
            logging.warning(f"Signup failed: username '{username}' already exists")
            return False, RESP_SIGNUP_USER_EXISTS, None
        
        # Check if email already exists (case-insensitive)
        if db.get_user_by_email(email):
            logging.warning(f"Signup failed: email '{email}' already exists")
            return False, RESP_SIGNUP_EMAIL_EXISTS, None
        
        # Validate username format (via User class validation)
        try:
            User._validate_username(username)
        except ValueError as e:
            logging.warning(f"Signup failed: invalid username - {e}")
            return False, RESP_SIGNUP_INVALID_USERNAME, None
        
        # Validate email format (via User class validation)
        try:
            User._validate_email(email)
        except ValueError as e:
            logging.warning(f"Signup failed: invalid email - {e}")
            return False, RESP_SIGNUP_INVALID_EMAIL, None
        
        # Hash password using Argon2
        password_hash = hash_password_argon2(password)
        
        # Create new user
        new_user = User(username, email, password_hash)
        
        # Add to database
        db.add_user(new_user)
        
        logging.info(f"User signup successful: {username} ({new_user.unique_id})")
        return True, RESP_SIGNUP_OK, new_user
    
    except ValueError as e:
        logging.error(f"Signup validation error: {e}")
        return False, RESP_SIGNUP_INVALID_USERNAME, None
    
    except Exception as e:
        logging.error(f"Unexpected error during signup: {e}")
        return False, "ERROR", None
