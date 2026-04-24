__author__ = "Yuval Malkan"

import random
import logging
from typing import Dict, List


class UserAgentRotator:
    """
    Rotate user agents and request headers for realistic HTTP requests.
    
    Helps avoid detection and rate limiting by appearing as different browsers.
    """
    
    # Realistic user agents (updated as of 2024)
    USER_AGENTS = [
        # Chrome (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Chrome (Mac)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        # Chrome (Linux)
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        # Firefox (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        # Firefox (Mac)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        # Firefox (Linux)
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
        # Safari (Mac)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        # Edge (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
        # Mobile (Chrome on Android)
        "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
        # Mobile (Safari on iOS)
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    ]
    
    # Common request headers
    COMMON_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }
    
    def __init__(self):
        """Initialize user agent rotator."""
        self.logger = logging.getLogger("UserAgentRotator")
        self.current_ua_index = random.randint(0, len(self.USER_AGENTS) - 1)
    
    def get_user_agent(self) -> str:
        """
        Get a random user agent.
        
        Returns:
            User agent string
        """
        ua = random.choice(self.USER_AGENTS)
        self.logger.debug(f"Selected user agent: {ua[:50]}...")
        return ua
    
    def get_next_user_agent(self) -> str:
        """
        Get next user agent in sequence (for consistent browsing).
        
        Returns:
            User agent string
        """
        ua = self.USER_AGENTS[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.USER_AGENTS)
        return ua
    
    def get_headers(self, platform: str = None, extra_headers: Dict = None) -> Dict:
        """
        Get realistic request headers for a platform.
        
        Args:
            platform: Platform name (for customization if needed)
            extra_headers: Additional headers to include
            
        Returns:
            Headers dictionary
        """
        headers = self.COMMON_HEADERS.copy()
        headers['User-Agent'] = self.get_user_agent()
        
        # Add platform-specific headers
        if platform and platform.lower() in ['instagram', 'twitter', 'tiktok']:
            headers['Referer'] = self._get_referer(platform)
        
        # Add extra headers if provided
        if extra_headers:
            headers.update(extra_headers)
        
        return headers
    
    def _get_referer(self, platform: str) -> str:
        """Get platform referer URL."""
        referrers = {
            'instagram': 'https://www.instagram.com/',
            'twitter': 'https://twitter.com/',
            'x': 'https://x.com/',
            'tiktok': 'https://www.tiktok.com/',
            'linkedin': 'https://www.linkedin.com/',
            'youtube': 'https://www.youtube.com/'
        }
        return referrers.get(platform.lower(), 'https://www.google.com/')
    
    def get_mobile_headers(self, platform: str = None) -> Dict:
        """
        Get mobile user agent headers.
        
        Args:
            platform: Platform name
            
        Returns:
            Headers dictionary with mobile user agent
        """
        headers = self.COMMON_HEADERS.copy()
        
        # Choose mobile user agent
        mobile_uas = [ua for ua in self.USER_AGENTS if 'Android' in ua or 'iPhone' in ua]
        headers['User-Agent'] = random.choice(mobile_uas) if mobile_uas else self.get_user_agent()
        
        if platform:
            headers['Referer'] = self._get_referer(platform)
        
        return headers
    
    def rotate_user_agents(self) -> str:
        """
        Get a different user agent than the current one.
        
        Returns:
            New user agent string
        """
        ua = self.get_next_user_agent()
        self.logger.debug(f"Rotated to user agent: {ua[:50]}...")
        return ua
    
    @staticmethod
    def get_all_user_agents() -> List[str]:
        """
        Get all available user agents.
        
        Returns:
            List of user agent strings
        """
        return UserAgentRotator.USER_AGENTS.copy()
    
    @staticmethod
    def add_custom_user_agent(ua: str):
        """
        Add custom user agent (modifies class-level list).
        
        Args:
            ua: User agent string to add
        """
        if ua not in UserAgentRotator.USER_AGENTS:
            UserAgentRotator.USER_AGENTS.append(ua)
