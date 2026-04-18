__author__ = "Yuval Malkan"

import uuid
import re
import logging


class User:
    """
    User model class representing a single user in the system.
    
    Fields:
        - unique_id: UUID4 string, automatically generated
        - username: Unique identifier for login (3-20 chars, alphanumeric + underscore)
        - email: User email address (must be valid format)
        - password_hash: Argon2 hash of password (never store plain password)
    """
    
    def __init__(self, username: str, email: str, password_hash: str):
        """
        Create a new User instance.
        
        Args:
            username: Username (3-20 chars, alphanumeric + underscore)
            email: Email address (validated)
            password_hash: Argon2 hash of password (pre-hashed by caller)
            
        Raises:
            ValueError: If any input validation fails
        """
        self.unique_id = str(uuid.uuid4())
        self.username = self._validate_username(username)
        self.email = self._validate_email(email)
        self.password_hash = password_hash
        
        logging.debug(f"User created: id={self.unique_id}, username={username}")
    
    @staticmethod
    def _validate_username(username: str) -> str:
        """
        Validate username format.
        
        Args:
            username: Username to validate
            
        Returns:
            Username if valid
            
        Raises:
            ValueError: If username is invalid
        """
        if not username or len(username) < 3 or len(username) > 20:
            raise ValueError("Username must be 3-20 characters long")
        
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValueError("Username can only contain alphanumeric characters and underscore")
        
        return username
    
    @staticmethod
    def _validate_email(email: str) -> str:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            Email if valid
            
        Raises:
            ValueError: If email is invalid
        """
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        
        if not email or not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        if len(email) > 254:
            raise ValueError("Email is too long (max 254 characters)")
        
        return email
    
    def to_dict(self) -> dict:
        """
        Convert User object to dictionary for serialization.
        
        Returns:
            Dictionary representation of User
        """
        return {
            'unique_id': self.unique_id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """
        Create User object from dictionary (deserialization).
        
        Args:
            data: Dictionary with keys: unique_id, username, email, password_hash
            
        Returns:
            User instance
            
        Raises:
            ValueError: If required keys are missing
            KeyError: If required keys are missing
        """
        required_keys = {'unique_id', 'username', 'email', 'password_hash'}
        if not required_keys.issubset(data.keys()):
            raise ValueError(f"Missing required fields: {required_keys - set(data.keys())}")
        
        user = cls(data['username'], data['email'], data['password_hash'])
        user.unique_id = data['unique_id']  # Restore original UUID instead of generating new one
        return user
    
    def __repr__(self) -> str:
        return f"User(id={self.unique_id}, username={self.username}, email={self.email})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False
        return self.unique_id == other.unique_id
