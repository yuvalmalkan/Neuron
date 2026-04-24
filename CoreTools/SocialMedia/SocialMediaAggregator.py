__author__ = "Yuval Malkan"

import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .InstagramScraper import InstagramScraper
from .TwitterScraper import TwitterScraper
from .TikTokScraper import TikTokScraper
from .LinkedInScraper import LinkedInScraper
from .YouTubeScraper import YouTubeScraper
from .RateLimiter import RateLimiter


class SocialMediaAggregator:
    """
    Unified interface for searching across all social media platforms.
    
    Provides methods to:
    - Search for users across platforms
    - Gather profile information from all platforms
    - Find same username across multiple platforms
    - Compile unified reports
    """
    
    def __init__(self, use_threading: bool = True):
        """
        Initialize aggregator with all platform scrapers.
        
        Args:
            use_threading: Use threading for parallel requests
        """
        self.logger = logging.getLogger("SocialMediaAggregator")
        self.use_threading = use_threading
        
        # Shared rate limiter
        self.rate_limiter = RateLimiter()
        
        # Initialize platform scrapers
        self.instagram = InstagramScraper(self.rate_limiter)
        self.twitter = TwitterScraper(self.rate_limiter)
        self.tiktok = TikTokScraper(self.rate_limiter)
        self.linkedin = LinkedInScraper(self.rate_limiter)
        self.youtube = YouTubeScraper(self.rate_limiter)
        
        self.scrapers = {
            'instagram': self.instagram,
            'twitter': self.twitter,
            'tiktok': self.tiktok,
            'linkedin': self.linkedin,
            'youtube': self.youtube
        }
        
        self.logger.info("SocialMediaAggregator initialized with 5 platforms")
    
    def search_username(self, username: str, platforms: List[str] = None) -> Dict:
        """
        Search for same username across platforms.
        
        Args:
            username: Username to search
            platforms: Specific platforms to search (all if None)
            
        Returns:
            Dict with results per platform
        """
        self.logger.info(f"Searching username '{username}' across platforms")
        
        if platforms is None:
            platforms = list(self.scrapers.keys())
        
        # Normalize platform names
        platforms = [p.lower() for p in platforms if p.lower() in self.scrapers]
        
        results = {
            'username': username,
            'search_results': {}
        }
        
        if self.use_threading:
            results['search_results'] = self._search_username_threaded(username, platforms)
        else:
            results['search_results'] = self._search_username_sequential(username, platforms)
        
        return results
    
    def _search_username_sequential(self, username: str, platforms: List[str]) -> Dict:
        """
        Search username sequentially across platforms.
        
        Args:
            username: Username to search
            platforms: List of platforms
            
        Returns:
            Results dict
        """
        results = {}
        
        for platform in platforms:
            try:
                scraper = self.scrapers[platform]
                
                if platform == 'instagram':
                    profile = scraper.get_user_profile(username)
                elif platform == 'twitter':
                    profile = scraper.get_user_profile(username)
                elif platform == 'tiktok':
                    profile = scraper.get_user_profile(username)
                elif platform == 'linkedin':
                    # LinkedIn needs special handling (URL-based)
                    profile = scraper.get_user_profile(f"https://linkedin.com/in/{username}")
                elif platform == 'youtube':
                    profile = scraper.get_channel_info(f"@{username}")
                else:
                    profile = None
                
                results[platform] = profile or {'not_found': True}
            
            except Exception as e:
                self.logger.error(f"Error searching {platform}: {e}")
                results[platform] = {'error': str(e), 'not_found': True}
        
        return results
    
    def _search_username_threaded(self, username: str, platforms: List[str]) -> Dict:
        """
        Search username in parallel across platforms.
        
        Args:
            username: Username to search
            platforms: List of platforms
            
        Returns:
            Results dict
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(5, len(platforms))) as executor:
            futures = {
                executor.submit(self._fetch_platform_profile, username, platform): platform
                for platform in platforms
            }
            
            for future in as_completed(futures):
                platform = futures[future]
                try:
                    profile = future.result()
                    results[platform] = profile or {'not_found': True}
                except Exception as e:
                    self.logger.error(f"Error searching {platform}: {e}")
                    results[platform] = {'error': str(e), 'not_found': True}
        
        return results
    
    def _fetch_platform_profile(self, username: str, platform: str) -> Optional[Dict]:
        """
        Fetch profile from specific platform.
        
        Args:
            username: Username
            platform: Platform name
            
        Returns:
            Profile dict or None
        """
        try:
            scraper = self.scrapers[platform]
            
            if platform == 'instagram':
                return scraper.get_user_profile(username)
            elif platform == 'twitter':
                return scraper.get_user_profile(username)
            elif platform == 'tiktok':
                return scraper.get_user_profile(username)
            elif platform == 'linkedin':
                return scraper.get_user_profile(f"https://linkedin.com/in/{username}")
            elif platform == 'youtube':
                return scraper.get_channel_info(f"@{username}")
        
        except Exception as e:
            self.logger.debug(f"Error fetching {platform} profile: {e}")
        
        return None
    
    def get_profile(self, username: str, platform: str) -> Optional[Dict]:
        """
        Get profile from specific platform.
        
        Args:
            username: Username or handle
            platform: Platform name
            
        Returns:
            Profile dict or None
        """
        platform = platform.lower()
        
        if platform not in self.scrapers:
            self.logger.warning(f"Unknown platform: {platform}")
            return None
        
        try:
            scraper = self.scrapers[platform]
            
            if platform == 'instagram':
                return scraper.get_user_profile(username)
            elif platform == 'twitter':
                return scraper.get_user_profile(username)
            elif platform == 'tiktok':
                return scraper.get_user_profile(username)
            elif platform == 'linkedin':
                return scraper.get_user_profile(username)
            elif platform == 'youtube':
                return scraper.get_channel_info(username)
        
        except Exception as e:
            self.logger.error(f"Error fetching {platform} profile: {e}")
        
        return None
    
    def get_posts(self, username: str, platform: str, limit: int = 20) -> List[Dict]:
        """
        Get posts/videos from platform.
        
        Args:
            username: Username
            platform: Platform name
            limit: Number of posts
            
        Returns:
            List of posts
        """
        platform = platform.lower()
        
        if platform not in self.scrapers:
            return []
        
        try:
            scraper = self.scrapers[platform]
            
            if platform == 'instagram':
                return scraper.get_user_posts(username, limit)
            elif platform == 'twitter':
                return scraper.get_user_tweets(username, limit)
            elif platform == 'tiktok':
                return scraper.get_user_videos(username, limit)
            elif platform == 'youtube':
                return scraper.get_channel_videos(username, limit)
            else:
                return []
        
        except Exception as e:
            self.logger.error(f"Error fetching posts from {platform}: {e}")
            return []
    
    def search_by_hashtag(self, hashtag: str, platform: str, limit: int = 20) -> List[Dict]:
        """
        Search by hashtag on platform.
        
        Args:
            hashtag: Hashtag (with or without #)
            platform: Platform name
            limit: Number of results
            
        Returns:
            List of posts/content
        """
        platform = platform.lower()
        
        if platform not in self.scrapers:
            return []
        
        # Remove # if present
        hashtag = hashtag.lstrip('#')
        
        try:
            scraper = self.scrapers[platform]
            
            if platform == 'instagram':
                return scraper.search_by_hashtag(hashtag, limit)
            elif platform == 'tiktok':
                return scraper.search_by_hashtag(hashtag, limit)
            else:
                return []
        
        except Exception as e:
            self.logger.error(f"Error searching hashtag: {e}")
            return []
    
    def get_rate_limit_status(self) -> Dict:
        """
        Get rate limit status for all platforms.
        
        Returns:
            Dict with status for each platform
        """
        status = {}
        
        for platform in self.scrapers:
            status[platform] = self.rate_limiter.get_status(platform)
        
        return status
    
    def reset_rate_limits(self, platform: str = None):
        """
        Reset rate limit counters.
        
        Args:
            platform: Specific platform or all if None
        """
        self.rate_limiter.reset(platform)
        self.logger.info(f"Rate limits reset for {platform or 'all platforms'}")
    
    def close(self):
        """Close all scraper sessions."""
        for scraper in self.scrapers.values():
            try:
                scraper.close()
            except:
                pass
        
        self.logger.info("All scraper sessions closed")
    
    def get_summary(self, results: Dict) -> Dict:
        """
        Generate summary of search results.
        
        Args:
            results: Results from search_username()
            
        Returns:
            Summary dict
        """
        summary = {
            'username': results.get('username'),
            'found_on_platforms': [],
            'not_found_platforms': [],
            'error_platforms': [],
            'total_followers': 0,
            'accounts': []
        }
        
        for platform, profile in results.get('search_results', {}).items():
            if not profile or profile.get('not_found') or profile.get('error'):
                summary['not_found_platforms'].append(platform)
            else:
                summary['found_on_platforms'].append(platform)
                summary['accounts'].append({
                    'platform': platform,
                    'username': profile.get('username'),
                    'name': profile.get('name'),
                    'followers': profile.get('followers', 0),
                    'profile_url': profile.get('profile_url'),
                    'verified': profile.get('verified', False)
                })
                summary['total_followers'] += profile.get('followers', 0)
        
        return summary
