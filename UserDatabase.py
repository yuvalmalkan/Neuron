__author__ = "Yuval Malkan"

import pickle
import os
import logging
from typing import Optional, Dict
from User import User


class UserDatabase:
    """
    User database manager using pickle file persistence.
    
    Stores all users in a single pickle file (Databases/users.pkl) as a dictionary
    indexed by username for fast lookups.
    
    Thread-safety: Not thread-safe. For concurrent access, consider adding locks.
    """
    
    def __init__(self, db_file: str = 'Databases/users.pkl'):
        """
        Initialize UserDatabase manager.
        
        Args:
            db_file: Path to pickle database file (default: Databases/users.pkl)
        """
        # Ensure directory exists
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logging.debug(f"Created directory: {db_dir}")
        
        self.db_file = db_file
        self.users: Dict[str, User] = {}
        
        if os.path.exists(db_file):
            self._load_from_disk()
            logging.info(f"Loaded {len(self.users)} users from {db_file}")
        else:
            logging.info(f"Database file {db_file} does not exist, starting with empty database")




    def _load_from_disk(self) -> None:
        """Load users from pickle file."""
        try:
            with open(self.db_file, 'rb') as f:
                data = pickle.load(f)
                
            if not isinstance(data, dict):
                raise ValueError(f"Invalid database format: expected dict, got {type(data)}")
            
            self.users = {}
            for username, user_dict in data.items():
                self.users[username] = User.from_dict(user_dict)
            
            logging.debug(f"Successfully loaded {len(self.users)} users from disk")
        
        except Exception as e:
            logging.error(f"Error loading database: {e}")
            raise



    def _save_to_disk(self) -> None:
        """Save users to pickle file."""
        try:
            data = {username: user.to_dict() for username, user in self.users.items()}
            
            with open(self.db_file, 'wb') as f:
                pickle.dump(data, f)
            
            logging.debug(f"Successfully saved {len(self.users)} users to disk")
        
        except Exception as e:
            logging.error(f"Error saving database: {e}")
            raise



    def add_user(self, user: User) -> bool:
        """
        Add a new user to the database.
        
        Args:
            user: User object to add
            
        Returns:
            True if user added successfully
            
        Raises:
            ValueError: If username already exists or user is invalid
        """
        if user.username in self.users:
            raise ValueError(f"Username '{user.username}' already exists")
        
        if self._email_exists(user.email):
            raise ValueError(f"Email '{user.email}' already exists")
        
        self.users[user.username] = user
        self._save_to_disk()
        
        logging.info(f"User added: {user.username}")
        return True



    def get_user(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to lookup
            
        Returns:
            User object if found, None otherwise
        """
        return self.users.get(username)




    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: Email to lookup
            
        Returns:
            User object if found, None otherwise
        """
        for user in self.users.values():
            if user.email.lower() == email.lower():
                return user
        return None



    def get_user_by_id(self, unique_id: str) -> Optional[User]:
        """
        Get user by unique ID (UUID).
        
        Args:
            unique_id: UUID to lookup
            
        Returns:
            User object if found, None otherwise
        """
        for user in self.users.values():
            if user.unique_id == unique_id:
                return user
        return None



    def user_exists(self, username: str) -> bool:
        """
        Check if username exists in database.
        
        Args:
            username: Username to check
            
        Returns:
            True if username exists, False otherwise
        """
        return username in self.users




    def _email_exists(self, email: str) -> bool:
        """
        Check if email exists in database (case-insensitive).
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists, False otherwise
        """
        email_lower = email.lower()
        for user in self.users.values():
            if user.email.lower() == email_lower:
                return True
        return False




    def update_user(self, user: User) -> bool:
        """
        Update an existing user.
        
        Args:
            user: User object with updated data
            
        Returns:
            True if user updated successfully
            
        Raises:
            ValueError: If user not found
        """
        if user.username not in self.users:
            raise ValueError(f"User '{user.username}' not found")
        
        self.users[user.username] = user
        self._save_to_disk()
        
        logging.info(f"User updated: {user.username}")
        return True




    def delete_user(self, username: str) -> bool:
        """
        Delete a user from the database.
        
        Args:
            username: Username to delete
            
        Returns:
            True if user deleted successfully
            
        Raises:
            ValueError: If user not found
        """
        if username not in self.users:
            raise ValueError(f"User '{username}' not found")
        
        del self.users[username]
        self._save_to_disk()
        
        logging.info(f"User deleted: {username}")
        return True



    def get_all_users(self) -> list:
        """
        Get all users from database.
        
        Returns:
            List of all User objects
        """
        return list(self.users.values())




    def get_user_count(self) -> int:
        """
        Get total number of users in database.
        
        Returns:
            Number of users
        """
        return len(self.users)
