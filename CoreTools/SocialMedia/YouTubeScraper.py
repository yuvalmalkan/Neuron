__author__ = "Yuval Malkan"

import logging
import json
import re
from typing import Optional, List, Dict
from datetime import datetime
from .ScraperBase import ScraperBase
from .UserAgent import UserAgentRotator
from .RateLimiter import RateLimiter


class YouTubeScraper(ScraperBase):
    """
    YouTube scraper for public channels and videos without authentication.
    
    Extracts:
    - Channel information (name, subscribers, description)
    - Video list with metadata
    - Video statistics (views, likes, comments)
    - Channel links and about info
    - Video tags and category
    
    Note: Uses public page scraping and reverse-engineered endpoints.
    """
    
    BASE_URL = "https://www.youtube.com"
    
    def __init__(self, rate_limiter: RateLimiter = None):
        """
        Initialize YouTube scraper.
        
        Args:
            rate_limiter: RateLimiter instance (shared across scrapers)
        """
        super().__init__("YouTube", timeout=15)
        self.user_agent_rotator = UserAgentRotator()
        self.rate_limiter = rate_limiter or RateLimiter()
    
    def get_channel_info(self, channel_id_or_url: str) -> Optional[Dict]:
        """
        Get public channel information.
        
        Args:
            channel_id_or_url: Channel ID, username, or full channel URL
            
        Returns:
            Channel info dict or None
        """
        try:
            # Normalize input
            channel_id = self._normalize_channel_identifier(channel_id_or_url)
            
            self.logger.info(f"Fetching channel info for {channel_id}")
            
            # Rate limiting
            self.rate_limiter.wait_if_needed("YouTube")
            
            # Determine URL format
            if channel_id.startswith('UC'):
                url = f"{self.BASE_URL}/channel/{channel_id}"
            else:
                url = f"{self.BASE_URL}/{channel_id}"
            
            # Use minimal headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Download HTML directly
            import requests
            response = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code != 200:
                self.log_activity("fetch_channel", channel_id, "failed", f"HTTP {response.status_code}")
                return None
            
            html = response.text
            self.logger.debug(f"Downloaded HTML: {len(html)} bytes")
            
            # Extract channel data
            channel_data = self._extract_channel_from_html(html, channel_id)
            
            if channel_data:
                self.rate_limiter.record_request("YouTube")
                self.log_activity("fetch_channel", channel_id, "success")
                return channel_data
            else:
                self.log_activity("fetch_channel", channel_id, "failed", "Could not parse channel")
                return None
        
        except Exception as e:
            self.logger.error(f"Error fetching channel: {e}")
            self.log_activity("fetch_channel", channel_id_or_url, "failed", str(e))
            return None
    
    def _normalize_channel_identifier(self, identifier: str) -> str:
        """
        Normalize channel identifier to standard format.
        
        Args:
            identifier: Channel ID, username, or URL
            
        Returns:
            Normalized channel ID or path
        """
        if identifier.startswith('http'):
            # Extract from URL
            match = re.search(r'youtube\.com/(@|channel/|c/)?([^/?]+)', identifier)
            if match:
                prefix = match.group(1) or ''
                value = match.group(2)
                return f"{prefix}{value}" if prefix else value
        
        # Return as-is if appears to be channel ID
        if identifier.startswith('UC'):
            return identifier
        
        # Assume it's a username/handle
        return f"@{identifier}" if not identifier.startswith('@') else identifier
    
    def _extract_channel_from_html(self, html: str, channel_id: str) -> Optional[Dict]:
        """
        Extract channel data from HTML meta tags.
        
        Args:
            html: HTML content of channel page
            channel_id: Channel identifier
            
        Returns:
            Channel dict or None
        """
        try:
            from bs4 import BeautifulSoup
            
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract meta tags
            title_tag = soup.find('meta', {'property': 'og:title'})
            desc_tag = soup.find('meta', {'property': 'og:description'})
            image_tag = soup.find('meta', {'property': 'og:image'})
            
            name = title_tag.get('content', '') if title_tag else ''
            description = desc_tag.get('content', '') if desc_tag else ''
            image_url = image_tag.get('content', '') if image_tag else ''
            
            self.logger.debug(f"Extracted: name={name}, desc={description[:50]}, image={image_url[:50]}")
            
            channel = {
                'channel_id': channel_id,
                'name': name,
                'description': description,
                'profile_url': f"{self.BASE_URL}/{channel_id}",
                'profile_picture': image_url,
                'subscribers': 0,
                'total_views': 0,
                'video_count': 0,
                'verified': False,
                'public': True,
                'links': [],
                'social_media': {}
            }
            
            # Extract social media links
            channel['links'] = self._extract_links_from_html(html)
            channel['social_media'] = self._extract_social_media_from_html(html)
            
            return self.normalize_user_data(channel)
        
        except Exception as e:
            self.logger.debug(f"Error parsing channel HTML: {e}")
            return None
    
    def _parse_count(self, count_str: str) -> int:
        """
        Parse count string like '1.2K', '5.5M' to integer.
        
        Args:
            count_str: Count string
            
        Returns:
            Parsed count
        """
        try:
            count_str = count_str.strip().upper()
            
            multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
            
            for suffix, multiplier in multipliers.items():
                if suffix in count_str:
                    value = float(count_str.replace(suffix, '').replace(',', ''))
                    return int(value * multiplier)
            
            return int(count_str.replace(',', ''))
        
        except ValueError:
            return 0
    
    def _extract_links_from_html(self, html: str) -> List[str]:
        """
        Extract external links from channel about section.
        
        Args:
            html: HTML content
            
        Returns:
            List of URLs
        """
        links = []
        
        try:
            # Look for common link patterns
            link_patterns = [
                r'https?://(?:www\.)?(?:twitter|x)\.com/\S+',
                r'https?://(?:www\.)?instagram\.com/\S+',
                r'https?://(?:www\.)?facebook\.com/\S+',
                r'https?://(?:www\.)?youtube\.com/\S+',
                r'https?://(?:www\.)?tiktok\.com/\S+',
                r'https?://(?:www\.)?twitch\.tv/\S+',
                r'https?://(?:www\.)?patreon\.com/\S+',
                r'https?://[a-z0-9\-\.]+\.[a-z]{2,}(?:/[^\s"\'<>]*)?'
            ]
            
            for pattern in link_patterns:
                for match in re.finditer(pattern, html):
                    url = match.group(0).rstrip(')')
                    if url not in links and len(links) < 20:
                        links.append(url)
        
        except Exception as e:
            self.logger.debug(f"Error extracting links: {e}")
        
        return links
    
    def _extract_social_media_from_html(self, html: str) -> Dict:
        """
        Extract social media handles from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Dict of social media handles
        """
        social = {}
        
        try:
            # Twitter/X
            twitter_match = re.search(r'(?:twitter|x)\.com/(@?\w+)', html, re.IGNORECASE)
            if twitter_match:
                social['twitter'] = twitter_match.group(1)
            
            # Instagram
            instagram_match = re.search(r'instagram\.com/(@?\w+)', html, re.IGNORECASE)
            if instagram_match:
                social['instagram'] = instagram_match.group(1)
            
            # TikTok
            tiktok_match = re.search(r'tiktok\.com/(@?\w+)', html, re.IGNORECASE)
            if tiktok_match:
                social['tiktok'] = tiktok_match.group(1)
        
        except Exception as e:
            self.logger.debug(f"Error extracting social media: {e}")
        
        return social
    
    def get_channel_videos(self, channel_id: str, limit: int = 50) -> List[Dict]:
        """
        Get recent videos from channel (limited without authentication).
        
        Args:
            channel_id: Channel ID or username
            limit: Number of videos to retrieve
            
        Returns:
            List of video dicts
        """
        try:
            self.logger.info(f"Fetching videos for channel {channel_id}")
            
            self.rate_limiter.wait_if_needed("YouTube")
            
            # Normalize channel ID
            channel_id = self._normalize_channel_identifier(channel_id)
            
            # Build URL
            if channel_id.startswith('UC'):
                url = f"{self.BASE_URL}/channel/{channel_id}/videos"
            else:
                url = f"{self.BASE_URL}/{channel_id}/videos"
            
            headers = self.user_agent_rotator.get_headers("YouTube")
            response = self.get(url, headers=headers, delay=1)
            
            if not self.validate_response(response):
                self.log_activity("fetch_videos", channel_id, "failed")
                return []
            
            self.rate_limiter.record_request("YouTube")
            
            # Extract videos
            videos = self._extract_videos_from_html(response.text, limit)
            
            self.log_activity("fetch_videos", channel_id, "success", f"Found {len(videos)} videos")
            return videos
        
        except Exception as e:
            self.logger.error(f"Error fetching videos: {e}")
            self.log_activity("fetch_videos", channel_id, "failed", str(e))
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
            # Look for video entries in HTML (usually in script tags)
            # This is a simplified extraction
            video_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
            
            for match in re.finditer(video_pattern, html):
                if len(videos) >= limit:
                    break
                
                video_id = match.group(1)
                
                video = {
                    'id': video_id,
                    'content': f"Video: {video_id}",
                    'timestamp': datetime.now().isoformat(),
                    'likes': 0,
                    'comments': 0,
                    'shares': 0,
                    'url': f"{self.BASE_URL}/watch?v={video_id}"
                }
                
                videos.append(self.normalize_post_data(video))
        
        except Exception as e:
            self.logger.debug(f"Error extracting videos: {e}")
        
        return videos
    
    def search_videos(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for videos (limited without authentication).
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of video dicts
        """
        try:
            self.logger.info(f"Searching videos for: {query}")
            
            self.rate_limiter.wait_if_needed("YouTube")
            
            url = f"{self.BASE_URL}/results?search_query={self.url_encode(query)}"
            headers = self.user_agent_rotator.get_headers("YouTube")
            
            response = self.get(url, headers=headers, delay=2)
            
            if not self.validate_response(response):
                return []
            
            self.rate_limiter.record_request("YouTube")
            
            videos = self._extract_videos_from_html(response.text, limit)
            
            return videos
        
        except Exception as e:
            self.logger.error(f"Error searching videos: {e}")
            return []
    
    def get_video_statistics(self, video_id: str) -> Optional[Dict]:
        """
        Get video statistics (very limited without authentication).
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video stats dict or None
        """
        try:
            self.logger.info(f"Fetching stats for video {video_id}")
            
            self.rate_limiter.wait_if_needed("YouTube")
            
            url = f"{self.BASE_URL}/watch?v={video_id}"
            headers = self.user_agent_rotator.get_headers("YouTube")
            
            response = self.get(url, headers=headers, delay=1)
            
            if not self.validate_response(response):
                return None
            
            self.rate_limiter.record_request("YouTube")
            
            # Extract stats from page
            stats = self._extract_video_stats(response.text)
            
            return stats
        
        except Exception as e:
            self.logger.error(f"Error fetching video stats: {e}")
            return None
    
    def _extract_video_stats(self, html: str) -> Optional[Dict]:
        """
        Extract video statistics from page HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Stats dict or None
        """
        try:
            # Extract view count
            views_match = re.search(
                r'(?:views|watched).*?([0-9.,]+)',
                html,
                re.IGNORECASE
            )
            
            # Extract likes (harder without auth)
            likes_match = re.search(
                r'(?:likes?).*?([0-9.,]+)',
                html,
                re.IGNORECASE
            )
            
            stats = {
                'views': self._parse_count(views_match.group(1)) if views_match else 0,
                'likes': self._parse_count(likes_match.group(1)) if likes_match else 0,
                'comments': 0
            }
            
            return stats
        
        except Exception as e:
            self.logger.debug(f"Error extracting stats: {e}")
            return None
