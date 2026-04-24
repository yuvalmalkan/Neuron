__author__ = "Yuval Malkan"

import logging
import json
import re
from typing import Optional, List, Dict
from datetime import datetime
from .ScraperBase import ScraperBase
from .UserAgent import UserAgentRotator
from .RateLimiter import RateLimiter


class TwitterScraper(ScraperBase):
    """
    Twitter/X scraper for public profiles and tweets without authentication.
    
    Extracts:
    - User profile information (name, bio, followers, following)
    - Public tweets
    - Tweet engagement (likes, retweets, replies)
    - Hashtags and mentions
    - User verification status
    
    Note: Uses public endpoints and Nitter mirrors for reliability.
    """
    
    BASE_URL = "https://twitter.com"
    NITTER_MIRROR = "https://nitter.net"  # Fallback mirror
    
    def __init__(self, rate_limiter: RateLimiter = None, use_nitter: bool = True):
        """
        Initialize Twitter scraper.
        
        Args:
            rate_limiter: RateLimiter instance (shared across scrapers)
            use_nitter: Use Nitter mirror instead of Twitter (more reliable without auth)
        """
        super().__init__("Twitter", timeout=15)
        self.user_agent_rotator = UserAgentRotator()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.use_nitter = use_nitter
        self.base_url = self.NITTER_MIRROR if use_nitter else self.BASE_URL
    
    def get_user_profile(self, username: str) -> Optional[Dict]:
        """
        Get public profile information.
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            User profile dict or None
        """
        try:
            self.logger.info(f"Fetching profile for @{username}")
            
            # Rate limiting
            self.rate_limiter.wait_if_needed("Twitter")
            
            # Clean username
            username = username.lstrip('@')
            
            # Use minimal headers for page scraping
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Use Nitter mirror (more reliable without auth)
            url = f"{self.base_url}/{username}"
            
            import requests
            response = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code != 200:
                self.log_activity("fetch_profile", username, "failed", f"HTTP {response.status_code}")
                return None
            
            html = response.text
            self.logger.debug(f"Downloaded HTML: {len(html)} bytes")
            
            # Extract profile from HTML
            profile = self._extract_profile_from_html(html, username)
            
            if profile:
                self.rate_limiter.record_request("Twitter")
                self.log_activity("fetch_profile", username, "success")
                return profile
            else:
                self.log_activity("fetch_profile", username, "failed")
                return None
        
        except Exception as e:
            self.logger.error(f"Error fetching profile for @{username}: {e}")
            self.log_activity("fetch_profile", username, "failed", str(e))
            return None
    
    def _extract_profile_from_html(self, html: str, username: str) -> Optional[Dict]:
        """
        Extract profile from Nitter HTML page.
        
        Args:
            html: HTML content
            username: Username
            
        Returns:
            Profile dict or None
        """
        try:
            from bs4 import BeautifulSoup
            
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for profile header info
            profile_header = soup.find('div', {'class': 'profile-card'})
            if not profile_header:
                # Fallback for other page structures
                profile_header = soup
            
            # Extract name
            name_tag = profile_header.find('a', {'class': 'fullname'})
            name = name_tag.text.strip() if name_tag else ''
            
            # Extract bio/description
            bio_tag = profile_header.find('div', {'class': 'bio'})
            bio = bio_tag.text.strip() if bio_tag else ''
            
            # Extract stats (followers, following, posts)
            followers = 0
            following = 0
            posts = 0
            
            stats_section = profile_header.find('div', {'class': 'stats'})
            if stats_section:
                stat_items = stats_section.find_all('div', {'class': 'stat-item'})
                for item in stat_items:
                    label = item.find('span', {'class': 'stat-label'})
                    value = item.find('span', {'class': 'stat-value'})
                    if label and value:
                        label_text = label.text.lower().strip()
                        value_text = value.text.strip().replace(',', '')
                        
                        if 'follower' in label_text:
                            followers = int(value_text) if value_text.isdigit() else 0
                        elif 'following' in label_text:
                            following = int(value_text) if value_text.isdigit() else 0
                        elif 'post' in label_text or 'tweet' in label_text:
                            posts = int(value_text) if value_text.isdigit() else 0
            
            # Check for verified status
            verified = profile_header.find('svg', {'class': 'verified'}) is not None
            
            profile = {
                'username': username,
                'name': name,
                'bio': bio,
                'profile_url': f"{self.base_url}/{username}",
                'profile_picture': '',
                'followers': followers,
                'following': following,
                'verified': verified,
                'public': True,
                'posts': posts
            }
            
            return self.normalize_user_data(profile)
        
        except Exception as e:
            self.logger.debug(f"HTML parsing error: {e}")
            return None
    
    def _fetch_profile_api(self, username: str) -> Optional[Dict]:
        """
        Fetch profile using public API endpoints.
        
        Args:
            username: Twitter username
            
        Returns:
            Profile dict or None
        """
        try:
            # Use public API endpoint
            url = f"https://api.twitter.com/2/users/by/username/{username}"
            params = {"user.fields": "public_metrics,verified"}
            headers = self.user_agent_rotator.get_headers("Twitter")
            
            response = self.get(url, headers=headers, params=params, delay=1)
            
            if not self.validate_response(response):
                return None
            
            data = response.json()
            if 'data' not in data:
                return None
            
            user_data = data['data']
            
            profile = {
                'username': user_data.get('username', username),
                'name': user_data.get('name', ''),
                'bio': '',  # Not in API v2 basic fields
                'profile_url': f"https://twitter.com/{username}",
                'followers': user_data.get('public_metrics', {}).get('followers_count', 0),
                'following': user_data.get('public_metrics', {}).get('following_count', 0),
                'verified': user_data.get('verified', False),
                'public': True,
                'posts': user_data.get('public_metrics', {}).get('tweet_count', 0)
            }
            
            return self.normalize_user_data(profile)
        
        except Exception as e:
            self.logger.debug(f"API fetch failed for @{username}: {e}")
            return None
    
    def _fetch_profile_page(self, username: str) -> Optional[Dict]:
        """
        Fetch profile by scraping page.
        
        Args:
            username: Twitter username
            
        Returns:
            Profile dict or None
        """
        try:
            url = f"{self.base_url}/{username}"
            headers = self.user_agent_rotator.get_headers("Twitter")
            
            response = self.get(url, headers=headers, delay=1)
            
            if not self.validate_response(response):
                return None
            
            html = response.text
            
            # Extract profile info from page
            profile = self._parse_profile_html(html, username)
            
            return profile
        
        except Exception as e:
            self.logger.debug(f"Page scraping failed for @{username}: {e}")
            return None
    
    def _parse_profile_html(self, html: str, username: str) -> Optional[Dict]:
        """
        Parse profile data from HTML.
        
        Args:
            html: HTML content
            username: Username
            
        Returns:
            Profile dict or None
        """
        try:
            # Extract name
            name_match = re.search(r'<h2[^>]*>([^<]+)</h2>', html)
            name = name_match.group(1) if name_match else ''
            
            # Extract bio
            bio_match = re.search(r'<p[^>]*class="[^"]*description[^"]*"[^>]*>([^<]+)</p>', html)
            bio = bio_match.group(1) if bio_match else ''
            
            # Extract follower count
            followers_match = re.search(r'(?:followers|following)["\']?\s*:?\s*([0-9.,]+)', html, re.IGNORECASE)
            followers = int(followers_match.group(1).replace(',', '')) if followers_match else 0
            
            # Extract verified status
            verified = 'verified' in html.lower()
            
            profile = {
                'username': username,
                'name': name.strip(),
                'bio': bio.strip(),
                'profile_url': f"https://twitter.com/{username}",
                'followers': followers,
                'following': 0,
                'verified': verified,
                'public': True,
                'posts': 0
            }
            
            return self.normalize_user_data(profile)
        
        except Exception as e:
            self.logger.debug(f"HTML parsing error: {e}")
            return None
    
    def get_user_tweets(self, username: str, limit: int = 20) -> List[Dict]:
        """
        Get recent tweets from user.
        
        Args:
            username: Twitter username
            limit: Number of tweets to retrieve (max based on API limits)
            
        Returns:
            List of tweet dicts
        """
        try:
            self.logger.info(f"Fetching tweets for @{username}")
            
            self.rate_limiter.wait_if_needed("Twitter")
            
            username = username.lstrip('@')
            url = f"{self.base_url}/{username}"
            headers = self.user_agent_rotator.get_headers("Twitter")
            
            response = self.get(url, headers=headers, delay=1)
            
            if not self.validate_response(response):
                self.log_activity("fetch_tweets", username, "failed")
                return []
            
            self.rate_limiter.record_request("Twitter")
            
            # Extract tweets from page (limited without auth)
            tweets = self._extract_tweets_from_html(response.text, limit)
            
            self.log_activity("fetch_tweets", username, "success", f"Found {len(tweets)} tweets")
            return tweets
        
        except Exception as e:
            self.logger.error(f"Error fetching tweets for @{username}: {e}")
            self.log_activity("fetch_tweets", username, "failed", str(e))
            return []
    
    def _extract_tweets_from_html(self, html: str, limit: int) -> List[Dict]:
        """
        Extract tweets from page HTML.
        
        Args:
            html: HTML content
            limit: Max tweets to extract
            
        Returns:
            List of tweet dicts
        """
        tweets = []
        
        try:
            # Simple tweet extraction (limited without auth)
            tweet_pattern = r'<div[^>]*class="[^"]*tweet[^"]*"[^>]*>([^<]*)</div>'
            tweet_matches = re.finditer(tweet_pattern, html)
            
            for match in tweet_matches:
                if len(tweets) >= limit:
                    break
                
                tweet_text = match.group(1).strip()
                if tweet_text:
                    tweet = {
                        'id': len(tweets),
                        'content': tweet_text[:300],  # Truncate for safety
                        'timestamp': datetime.now().isoformat(),
                        'likes': 0,
                        'comments': 0,
                        'shares': 0
                    }
                    tweets.append(self.normalize_post_data(tweet))
        
        except Exception as e:
            self.logger.debug(f"Error extracting tweets: {e}")
        
        return tweets
    
    def search_tweets(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search public tweets (limited without authentication).
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of tweet dicts
        """
        try:
            self.logger.info(f"Searching tweets for: {query}")
            
            self.rate_limiter.wait_if_needed("Twitter")
            
            # Encode query
            encoded_query = self.url_encode(query)
            url = f"{self.base_url}/search?q={encoded_query}"
            headers = self.user_agent_rotator.get_headers("Twitter")
            
            response = self.get(url, headers=headers, delay=2)
            
            if not self.validate_response(response):
                self.log_activity("search_tweets", query, "failed")
                return []
            
            self.rate_limiter.record_request("Twitter")
            
            # Extract tweets
            tweets = self._extract_tweets_from_html(response.text, limit)
            
            self.log_activity("search_tweets", query, "success", f"Found {len(tweets)} tweets")
            return tweets
        
        except Exception as e:
            self.logger.error(f"Error searching tweets: {e}")
            self.log_activity("search_tweets", query, "failed", str(e))
            return []
    
    def get_trending_topics(self, count: int = 10) -> List[str]:
        """
        Get trending topics (very limited without authentication).
        
        Args:
            count: Number of trending topics
            
        Returns:
            List of hashtag strings
        """
        try:
            self.logger.info("Fetching trending topics")
            
            self.rate_limiter.wait_if_needed("Twitter")
            
            url = f"{self.base_url}/explore"
            headers = self.user_agent_rotator.get_headers("Twitter")
            
            response = self.get(url, headers=headers, delay=2)
            
            if not self.validate_response(response):
                return []
            
            self.rate_limiter.record_request("Twitter")
            
            # Extract trending hashtags
            trends = []
            hashtag_pattern = r'#\w+'
            matches = re.finditer(hashtag_pattern, response.text)
            
            for match in matches:
                if len(trends) >= count:
                    break
                hashtag = match.group(0)
                if hashtag not in trends:
                    trends.append(hashtag)
            
            return trends
        
        except Exception as e:
            self.logger.error(f"Error fetching trends: {e}")
            return []
    
    def get_followers_count(self, username: str) -> Optional[int]:
        """
        Get follower count.
        
        Args:
            username: Twitter username
            
        Returns:
            Follower count or None
        """
        profile = self.get_user_profile(username)
        if profile:
            return profile.get('followers')
        return None
    
    def is_verified(self, username: str) -> Optional[bool]:
        """
        Check if account is verified.
        
        Args:
            username: Twitter username
            
        Returns:
            True if verified, False otherwise, None if error
        """
        profile = self.get_user_profile(username)
        if profile:
            return profile.get('verified', False)
        return None
