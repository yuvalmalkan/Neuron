__author__ = "Yuval Malkan"

import logging
import json
import re
from typing import Optional, List, Dict
from datetime import datetime
from .ScraperBase import ScraperBase
from .UserAgent import UserAgentRotator
from .RateLimiter import RateLimiter


class TikTokScraper(ScraperBase):
    """
    TikTok scraper for public profiles and videos without authentication.
    
    Extracts:
    - User profile information (username, name, bio, followers)
    - Video list with metadata
    - Video engagement (views, likes, comments)
    - Hashtags and sounds
    - User verification status
    
    Note: Uses reverse-engineered public endpoints.
    """
    
    BASE_URL = "https://www.tiktok.com"
    API_URL = "https://api.tiktok.com/v1"
    
    def __init__(self, rate_limiter: RateLimiter = None):
        """
        Initialize TikTok scraper.
        
        Args:
            rate_limiter: RateLimiter instance (shared across scrapers)
        """
        super().__init__("TikTok", timeout=15)
        self.user_agent_rotator = UserAgentRotator()
        self.rate_limiter = rate_limiter or RateLimiter()
    
    def get_user_profile(self, username: str) -> Optional[Dict]:
        """
        Get public profile information.
        
        Args:
            username: TikTok username (without @)
            
        Returns:
            User profile dict or None
        """
        try:
            self.logger.info(f"Fetching profile for @{username}")
            
            # Rate limiting
            self.rate_limiter.wait_if_needed("TikTok")
            
            # Clean username
            username = username.lstrip('@')
            
            # Fetch profile page
            url = f"{self.BASE_URL}/@{username}"
            
            # Use minimal headers
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
            
            # Extract profile data from page
            profile_data = self._extract_profile_from_html(html, username)
            
            if profile_data:
                self.rate_limiter.record_request("TikTok")
                self.log_activity("fetch_profile", username, "success")
                return profile_data
            else:
                self.log_activity("fetch_profile", username, "failed", "Could not parse profile")
                return None
        
        except Exception as e:
            self.logger.error(f"Error fetching profile for @{username}: {e}")
            self.log_activity("fetch_profile", username, "failed", str(e))
            return None
    
    def _extract_profile_from_html(self, html: str, username: str) -> Optional[Dict]:
        """
        Extract profile data from HTML.
        
        Args:
            html: HTML content of profile page
            username: Username
            
        Returns:
            Profile dict or None
        """
        try:
            # Look for SIGI state in HTML
            sigi_match = re.search(r'<script id="SIGI_STATE"[^>]*>([^<]+)</script>', html)
            
            if sigi_match:
                try:
                    data = json.loads(sigi_match.group(1))
                    # Navigate to user data
                    if 'UserModule' in data and 'userInfo' in data['UserModule']:
                        user_info = data['UserModule']['userInfo']
                        
                        profile = {
                            'username': user_info.get('user', {}).get('uniqueId', username),
                            'name': user_info.get('user', {}).get('nickname', ''),
                            'bio': user_info.get('user', {}).get('signature', ''),
                            'profile_url': f"{self.BASE_URL}/@{username}",
                            'profile_picture': user_info.get('user', {}).get('avatarLarger', ''),
                            'followers': user_info.get('stats', {}).get('followerCount', 0),
                            'following': user_info.get('stats', {}).get('followingCount', 0),
                            'verified': user_info.get('user', {}).get('verified', False),
                            'public': True,
                            'video_count': user_info.get('stats', {}).get('videoCount', 0)
                        }
                        
                        return self.normalize_user_data(profile)
                
                except json.JSONDecodeError:
                    pass
            
            # Fallback: Extract from meta tags
            name_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
            followers_match = re.search(r'Followers.*?([0-9.,]+)', html)
            
            profile = {
                'username': username,
                'name': name_match.group(1) if name_match else '',
                'bio': '',
                'profile_url': f"{self.BASE_URL}/@{username}",
                'followers': int(followers_match.group(1).replace(',', '')) if followers_match else 0,
                'following': 0,
                'verified': 'verified' in html.lower(),
                'public': True,
                'video_count': 0
            }
            
            return self.normalize_user_data(profile)
        
        except Exception as e:
            self.logger.debug(f"Error parsing profile HTML: {e}")
            return None
    
    def get_user_videos(self, username: str, limit: int = 30) -> List[Dict]:
        """
        Get recent videos from user (limited without authentication).
        
        Args:
            username: TikTok username
            limit: Number of videos to retrieve
            
        Returns:
            List of video dicts
        """
        try:
            self.logger.info(f"Fetching videos for @{username}")
            
            self.rate_limiter.wait_if_needed("TikTok")
            
            username = username.lstrip('@')
            url = f"{self.BASE_URL}/@{username}"
            headers = self.user_agent_rotator.get_headers("TikTok")
            
            response = self.get(url, headers=headers, delay=1)
            
            if not self.validate_response(response):
                self.log_activity("fetch_videos", username, "failed")
                return []
            
            self.rate_limiter.record_request("TikTok")
            
            # Extract videos from page
            videos = self._extract_videos_from_html(response.text, limit)
            
            self.log_activity("fetch_videos", username, "success", f"Found {len(videos)} videos")
            return videos
        
        except Exception as e:
            self.logger.error(f"Error fetching videos for @{username}: {e}")
            self.log_activity("fetch_videos", username, "failed", str(e))
            return []
    
    def _extract_videos_from_html(self, html: str, limit: int) -> List[Dict]:
        """
        Extract video data from HTML.
        
        Args:
            html: HTML content
            limit: Max videos to extract
            
        Returns:
            List of video dicts
        """
        videos = []
        
        try:
            # Extract video data from SIGI state
            sigi_match = re.search(r'<script id="SIGI_STATE"[^>]*>([^<]+)</script>', html)
            
            if sigi_match:
                try:
                    data = json.loads(sigi_match.group(1))
                    
                    # Navigate to video list
                    if 'FeedModule' in data:
                        for video_item in data.get('FeedModule', {}).get('feedItems', [])[:limit]:
                            if 'video' in video_item:
                                video = video_item['video']
                                
                                video_dict = {
                                    'id': video.get('id'),
                                    'content': video.get('desc', '')[:300],
                                    'timestamp': datetime.fromtimestamp(
                                        video.get('createTime', 0)
                                    ).isoformat() if video.get('createTime') else datetime.now().isoformat(),
                                    'likes': video.get('stats', {}).get('diggCount', 0),
                                    'comments': video.get('stats', {}).get('commentCount', 0),
                                    'shares': video.get('stats', {}).get('shareCount', 0),
                                    'views': video.get('stats', {}).get('playCount', 0),
                                    'media': [video.get('downloadAddr')]
                                }
                                
                                videos.append(self.normalize_post_data(video_dict))
                
                except (json.JSONDecodeError, KeyError):
                    pass
        
        except Exception as e:
            self.logger.debug(f"Error extracting videos: {e}")
        
        return videos
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        Get detailed information about a video.
        
        Args:
            video_id: TikTok video ID
            
        Returns:
            Video details dict or None
        """
        try:
            self.logger.info(f"Fetching video details for {video_id}")
            
            self.rate_limiter.wait_if_needed("TikTok")
            
            # Try to fetch via different methods
            # Note: This is limited without authentication
            
            self.rate_limiter.record_request("TikTok")
            self.log_activity("fetch_video_details", video_id, "attempted")
            
            return None  # Limited without auth
        
        except Exception as e:
            self.logger.error(f"Error fetching video details: {e}")
            return None
    
    def search_by_hashtag(self, hashtag: str, limit: int = 20) -> List[Dict]:
        """
        Search videos by hashtag (limited without authentication).
        
        Args:
            hashtag: Hashtag to search (without #)
            limit: Number of videos to retrieve
            
        Returns:
            List of video dicts
        """
        try:
            self.logger.info(f"Searching hashtag #{hashtag}")
            
            self.rate_limiter.wait_if_needed("TikTok")
            
            hashtag = hashtag.lstrip('#')
            url = f"{self.BASE_URL}/tag/{hashtag}"
            headers = self.user_agent_rotator.get_headers("TikTok")
            
            response = self.get(url, headers=headers, delay=2)
            
            if not self.validate_response(response):
                self.log_activity("search_hashtag", hashtag, "failed")
                return []
            
            self.rate_limiter.record_request("TikTok")
            
            # Extract videos from hashtag page
            videos = self._extract_videos_from_html(response.text, limit)
            
            self.log_activity("search_hashtag", hashtag, "success", f"Found {len(videos)} videos")
            return videos
        
        except Exception as e:
            self.logger.error(f"Error searching hashtag #{hashtag}: {e}")
            self.log_activity("search_hashtag", hashtag, "failed", str(e))
            return []
    
    def get_trending_videos(self, count: int = 20) -> List[Dict]:
        """
        Get trending videos (limited without authentication).
        
        Args:
            count: Number of videos to retrieve
            
        Returns:
            List of video dicts
        """
        try:
            self.logger.info("Fetching trending videos")
            
            self.rate_limiter.wait_if_needed("TikTok")
            
            url = f"{self.BASE_URL}/feed"
            headers = self.user_agent_rotator.get_headers("TikTok")
            
            response = self.get(url, headers=headers, delay=2)
            
            if not self.validate_response(response):
                return []
            
            self.rate_limiter.record_request("TikTok")
            
            videos = self._extract_videos_from_html(response.text, count)
            
            return videos
        
        except Exception as e:
            self.logger.error(f"Error fetching trending videos: {e}")
            return []
    
    def get_followers_count(self, username: str) -> Optional[int]:
        """
        Get follower count.
        
        Args:
            username: TikTok username
            
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
            username: TikTok username
            
        Returns:
            True if verified, False otherwise, None if error
        """
        profile = self.get_user_profile(username)
        if profile:
            return profile.get('verified', False)
        return None
