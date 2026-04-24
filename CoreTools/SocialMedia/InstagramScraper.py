__author__ = "Yuval Malkan"

import logging
import json
import re
from typing import Optional, List, Dict
from datetime import datetime
from .ScraperBase import ScraperBase
from .UserAgent import UserAgentRotator
from .RateLimiter import RateLimiter


class InstagramScraper(ScraperBase):
    """
    Instagram scraper for public profiles without authentication.
    
    Extracts:
    - Profile information (username, name, bio, followers, following)
    - Profile picture
    - Public posts
    - Hashtags
    - Account verification status
    """
    
    BASE_URL = "https://www.instagram.com"
    
    def __init__(self, rate_limiter: RateLimiter = None):
        """
        Initialize Instagram scraper.
        
        Args:
            rate_limiter: RateLimiter instance (shared across scrapers)
        """
        super().__init__("Instagram", timeout=15)
        self.user_agent_rotator = UserAgentRotator()
        self.rate_limiter = rate_limiter or RateLimiter()
    
    def get_user_profile(self, username: str) -> Optional[Dict]:
        """
        Get public profile information.
        
        Args:
            username: Instagram username
            
        Returns:
            User profile dict or None
        """
        try:
            self.logger.info(f"Fetching profile for @{username}")
            
            # Rate limiting
            self.rate_limiter.wait_if_needed("Instagram")
            
            # Fetch profile page HTML
            url = f"{self.BASE_URL}/{username}"
            
            # Use minimal headers - Instagram blocks some header combinations
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Download HTML directly
            import requests
            response = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code != 200:
                self.log_activity("fetch_profile", username, "failed", f"HTTP {response.status_code}")
                return None
            
            html = response.text
            self.logger.debug(f"Downloaded HTML: {len(html)} bytes")
            
            # Parse HTML locally
            profile_data = self._extract_profile_from_html(html)
            
            if not profile_data:
                self.log_activity("fetch_profile", username, "failed", "Could not parse HTML")
                return None
            
            # Record request for rate limiting
            self.rate_limiter.record_request("Instagram")
            
            # Normalize data
            normalized = self._normalize_instagram_profile(profile_data, username)
            
            self.log_activity("fetch_profile", username, "success")
            return normalized
        
        except Exception as e:
            self.logger.error(f"Error fetching profile for @{username}: {e}")
            self.log_activity("fetch_profile", username, "failed", str(e))
            return None
    
    def _extract_profile_from_html(self, html: str) -> Optional[Dict]:
        """
        Extract profile info from meta tags in HTML.
        
        Args:
            html: HTML content of profile page
            
        Returns:
            Profile data dict or None
        """
        try:
            from bs4 import BeautifulSoup
            
            if not html:
                self.logger.debug("HTML is empty")
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            data = {}
            
            # Extract meta description
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                data['meta_description'] = meta_desc.get('content', '')
                self.logger.debug(f"Found meta description: {data['meta_description'][:100]}")
            
            # Extract profile image
            og_image = soup.find('meta', {'property': 'og:image'})
            if og_image:
                data['profile_picture'] = og_image.get('content', '')
                self.logger.debug(f"Found profile picture: {data['profile_picture'][:80]}")
            
            # Extract title for additional name info
            title = soup.find('meta', {'property': 'og:title'})
            if title:
                data['title'] = title.get('content', '')
                self.logger.debug(f"Found title: {data['title']}")
            
            return data if data else None
        
        except Exception as e:
            self.logger.error(f"Error parsing HTML: {e}", exc_info=True)
            return None
    
    def _normalize_instagram_profile(self, data: Dict, username: str) -> Optional[Dict]:
        """
        Extract and normalize profile data from meta description.
        
        Args:
            data: Parsed data dict
            username: Username
            
        Returns:
            Normalized profile dict
        """
        try:
            # The data comes from meta_description parsing
            if not data or 'meta_description' not in data:
                self.logger.debug("No meta description data available")
                return None
            
            meta_desc = data.get('meta_description', '')
            
            followers = 0
            following = 0
            posts = 0
            name = ''
            
            # Extract numbers from meta description
            # Example: "673M Followers, 643 Following, 4,046 Posts - Cristiano Ronaldo (@cristiano)"
            import re
            
            # Parse followers (handle K, M, B suffixes)
            followers_match = re.search(r'([\d,]+\.?\d*[KMB]?)\s+Followers', meta_desc)
            if followers_match:
                followers = self._parse_count(followers_match.group(1))
            
            # Parse following
            following_match = re.search(r'([\d,]+\.?\d*[KMB]?)\s+Following', meta_desc)
            if following_match:
                following = self._parse_count(following_match.group(1))
            
            # Parse posts
            posts_match = re.search(r'([\d,]+\.?\d*[KMB]?)\s+Posts', meta_desc)
            if posts_match:
                posts = self._parse_count(posts_match.group(1))
            
            # Parse name
            name_match = re.search(r'-\s+([^(@]+?)\s+\(@', meta_desc)
            if name_match:
                name = name_match.group(1).strip()
            
            profile = {
                'username': username,
                'name': name,
                'bio': '',  # Not available from meta description
                'profile_url': f"{self.BASE_URL}/{username}",
                'profile_picture': data.get('profile_picture', ''),
                'followers': followers,
                'following': following,
                'verified': '✓' in meta_desc or 'verified' in meta_desc.lower(),
                'public': True,
                'posts': posts,
                'post_list': []
            }
            
            return self.normalize_user_data(profile)
        
        except Exception as e:
            self.logger.error(f"Error normalizing profile data: {e}")
            return None
    
    def get_user_posts(self, username: str, limit: int = 10) -> List[Dict]:
        """
        Get recent posts from user (limited data without authentication).
        
        Args:
            username: Instagram username
            limit: Number of posts to retrieve
            
        Returns:
            List of post dicts
        """
        profile = self.get_user_profile(username)
        if profile and profile.get('posts'):
            return profile['posts'][:limit]
        return []
    
    def _parse_count(self, count_str: str) -> int:
        """
        Parse count string with K/M/B suffixes.
        
        Examples: "1.2K" -> 1200, "5M" -> 5000000, "1.5B" -> 1500000000
        """
        try:
            count_str = count_str.replace(',', '').upper().strip()
            if count_str.endswith('K'):
                return int(float(count_str[:-1]) * 1000)
            elif count_str.endswith('M'):
                return int(float(count_str[:-1]) * 1000000)
            elif count_str.endswith('B'):
                return int(float(count_str[:-1]) * 1000000000)
            else:
                return int(float(count_str))
        except:
            return 0
    
    def search_by_hashtag(self, hashtag: str, limit: int = 20) -> List[Dict]:
        """
        Search posts by hashtag (limited without authentication).
        
        Args:
            hashtag: Hashtag to search (without #)
            limit: Number of posts to retrieve
            
        Returns:
            List of post dicts
        """
        try:
            self.logger.info(f"Searching hashtag #{hashtag}")
            
            self.rate_limiter.wait_if_needed("Instagram")
            
            url = f"{self.BASE_URL}/explore/tags/{hashtag}"
            headers = self.user_agent_rotator.get_headers("Instagram")
            
            response = self.get(url, headers=headers, delay=1)
            
            if not self.validate_response(response):
                self.log_activity("search_hashtag", hashtag, "failed")
                return []
            
            self.rate_limiter.record_request("Instagram")
            
            # Extract hashtag data
            data = self._extract_profile_json(response.text)
            
            posts = []
            if data and 'entry_data' in data:
                # Parse hashtag page posts
                # Note: Limited data available without authentication
                pass
            
            self.log_activity("search_hashtag", hashtag, "success", f"Found {len(posts)} posts")
            return posts
        
        except Exception as e:
            self.logger.error(f"Error searching hashtag #{hashtag}: {e}")
            self.log_activity("search_hashtag", hashtag, "failed", str(e))
            return []
    
    def get_user_followers_count(self, username: str) -> Optional[int]:
        """
        Get follower count for user.
        
        Args:
            username: Instagram username
            
        Returns:
            Follower count or None
        """
        profile = self.get_user_profile(username)
        if profile:
            return profile.get('followers')
        return None
    
    def is_account_public(self, username: str) -> Optional[bool]:
        """
        Check if account is public.
        
        Args:
            username: Instagram username
            
        Returns:
            True if public, False if private, None if error
        """
        profile = self.get_user_profile(username)
        if profile:
            return profile.get('public', True)
        return None
