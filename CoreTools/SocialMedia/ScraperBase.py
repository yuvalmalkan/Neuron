__author__ = "Yuval Malkan"

import requests
import logging
import time
from datetime import datetime
from typing import Optional, Dict, List
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ScraperBase:
    """
    Base class for all social media scrapers.
    
    Provides common functionality for:
    - HTTP requests with retry logic
    - Error handling
    - Data normalization
    - Logging
    - Response validation
    - Timeout handling
    """
    
    def __init__(self, platform_name: str, timeout: int = 10, max_retries: int = 3):
        """
        Initialize scraper base.
        
        Args:
            platform_name: Name of the platform (e.g., 'Instagram', 'Twitter')
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.platform_name = platform_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"{platform_name}Scraper")
        
        # Create session with retry strategy
        self.session = self._create_session_with_retries()
    
    def _create_session_with_retries(self) -> requests.Session:
        """
        Create a requests session with automatic retry logic.
        
        Returns:
            Configured requests.Session
        """
        session = requests.Session()
        
        # Configure retries with exponential backoff
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,  # 1s, 2s, 4s, 8s between retries
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(self, method: str, url: str, headers: Dict = None, 
                     params: Dict = None, data: Dict = None, 
                     delay: float = 0) -> Optional[requests.Response]:
        """
        Make HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc)
            url: URL to request
            headers: Custom headers
            params: Query parameters
            data: Request body data
            delay: Delay before making request (seconds)
            
        Returns:
            Response object or None if failed
        """
        if delay > 0:
            time.sleep(delay)
        
        try:
            self.logger.debug(f"Making {method} request to {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', 60)
                self.logger.warning(f"Rate limited. Retry after {retry_after} seconds")
                return None
            
            # Check for success
            if response.status_code == 404:
                self.logger.warning(f"Resource not found: {url}")
                return None
            
            if response.status_code == 403:
                self.logger.warning(f"Access forbidden: {url}")
                return None
            
            response.raise_for_status()
            
            self.logger.debug(f"Successfully fetched {url}")
            return response
        
        except requests.Timeout:
            self.logger.error(f"Timeout while fetching {url}")
            return None
        
        except requests.ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            return None
        
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None
    
    def get(self, url: str, headers: Dict = None, params: Dict = None, 
            delay: float = 0) -> Optional[requests.Response]:
        """
        Make GET request.
        
        Args:
            url: URL to request
            headers: Custom headers
            params: Query parameters
            delay: Delay before request
            
        Returns:
            Response object or None
        """
        return self._make_request("GET", url, headers, params, delay=delay)
    
    def post(self, url: str, headers: Dict = None, data: Dict = None, 
             delay: float = 0) -> Optional[requests.Response]:
        """
        Make POST request.
        
        Args:
            url: URL to request
            headers: Custom headers
            data: Request body
            delay: Delay before request
            
        Returns:
            Response object or None
        """
        return self._make_request("POST", url, headers, data=data, delay=delay)
    
    def normalize_user_data(self, data: Dict) -> Dict:
        """
        Normalize user data to standard format.
        
        Args:
            data: Raw data from scraper
            
        Returns:
            Normalized user data dict
        """
        return {
            'platform': self.platform_name,
            'username': data.get('username', ''),
            'name': data.get('name', ''),
            'bio': data.get('bio', ''),
            'profile_url': data.get('profile_url', ''),
            'profile_picture': data.get('profile_picture'),
            'followers': data.get('followers', 0),
            'following': data.get('following', 0),
            'verified': data.get('verified', False),
            'public': data.get('public', True),
            'timestamp': datetime.now().isoformat(),
            'posts': data.get('posts', [])
        }
    
    def normalize_post_data(self, post: Dict) -> Dict:
        """
        Normalize post/content data to standard format.
        
        Args:
            post: Raw post data from scraper
            
        Returns:
            Normalized post data dict
        """
        return {
            'platform': self.platform_name,
            'post_id': post.get('id', ''),
            'author': post.get('author', ''),
            'content': post.get('content', ''),
            'timestamp': post.get('timestamp'),
            'likes': post.get('likes', 0),
            'comments': post.get('comments', 0),
            'shares': post.get('shares', 0),
            'media': post.get('media', []),
            'hashtags': post.get('hashtags', []),
            'url': post.get('url', '')
        }
    
    def log_activity(self, action: str, username: str = None, status: str = "success", 
                    details: str = None):
        """
        Log scraping activity.
        
        Args:
            action: Action performed (e.g., 'fetch_profile')
            username: Target username
            status: Status of action (success, failed, rate_limited, etc)
            details: Additional details
        """
        message = f"{action}|{username or 'N/A'}|{status}"
        if details:
            message += f"|{details}"
        
        if status == "success":
            self.logger.info(message)
        else:
            self.logger.warning(message)
    
    def validate_response(self, response: Optional[requests.Response]) -> bool:
        """
        Validate HTTP response.
        
        Args:
            response: Response object to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        if response is None:
            return False
        
        if response.status_code != 200:
            return False
        
        if not response.content:
            return False
        
        return True
    
    def url_encode(self, value: str) -> str:
        """
        URL encode a string safely.
        
        Args:
            value: String to encode
            
        Returns:
            URL-encoded string
        """
        return quote(value, safe='')
    
    def close(self):
        """Close the session."""
        self.session.close()
        self.logger.debug("Session closed")
