__author__ = "Yuval Malkan"

import time
import logging
from datetime import datetime, timedelta
from typing import Dict
from collections import deque


class RateLimiter:
    """
    Rate limiter for managing requests per platform.
    
    Implements token bucket algorithm to ensure we don't exceed
    platform rate limits while maintaining good performance.
    """
    
    # Default rate limits (requests per minute)
    DEFAULT_LIMITS = {
        'Instagram': 60,
        'Twitter': 100,
        'TikTok': 60,
        'LinkedIn': 20,
        'YouTube': 100
    }
    
    def __init__(self, limits: Dict[str, int] = None):
        """
        Initialize rate limiter.
        
        Args:
            limits: Dictionary of platform -> requests_per_minute
        """
        self.limits = limits or self.DEFAULT_LIMITS
        self.request_times = {platform: deque() for platform in self.limits}
        self.logger = logging.getLogger("RateLimiter")
    
    def get_delay(self, platform: str) -> float:
        """
        Get delay before next request for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Delay in seconds (0 if no delay needed)
        """
        if platform not in self.limits:
            self.logger.warning(f"Unknown platform: {platform}")
            return 0
        
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Remove requests older than 1 minute
        while self.request_times[platform] and self.request_times[platform][0] < one_minute_ago:
            self.request_times[platform].popleft()
        
        # Get limit and current request count
        limit = self.limits[platform]
        current_count = len(self.request_times[platform])
        
        if current_count < limit:
            # We have room for more requests
            return 0
        
        # Calculate delay until oldest request leaves the window
        if self.request_times[platform]:
            oldest = self.request_times[platform][0]
            delay = (oldest + timedelta(minutes=1) - now).total_seconds()
            return max(0, delay)
        
        return 0
    
    def wait_if_needed(self, platform: str):
        """
        Wait if necessary before making request.
        
        Args:
            platform: Platform name
        """
        delay = self.get_delay(platform)
        if delay > 0:
            self.logger.info(f"{platform}: Rate limit approaching, waiting {delay:.2f}s")
            time.sleep(delay)
    
    def record_request(self, platform: str):
        """
        Record a request for rate limiting.
        
        Args:
            platform: Platform name
        """
        if platform not in self.request_times:
            self.logger.warning(f"Unknown platform: {platform}")
            return
        
        self.request_times[platform].append(datetime.now())
    
    def get_requests_in_window(self, platform: str) -> int:
        """
        Get number of requests in current 1-minute window.
        
        Args:
            platform: Platform name
            
        Returns:
            Number of requests
        """
        if platform not in self.request_times:
            return 0
        
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Count requests in window
        count = sum(1 for req_time in self.request_times[platform] 
                   if req_time > one_minute_ago)
        return count
    
    def get_status(self, platform: str) -> Dict:
        """
        Get rate limit status for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Status dict with limit and current count
        """
        if platform not in self.limits:
            return {}
        
        return {
            'platform': platform,
            'limit': self.limits[platform],
            'requests_in_window': self.get_requests_in_window(platform),
            'remaining': self.limits[platform] - self.get_requests_in_window(platform)
        }
    
    def set_limit(self, platform: str, limit: int):
        """
        Set rate limit for platform.
        
        Args:
            platform: Platform name
            limit: Requests per minute
        """
        self.limits[platform] = limit
        if platform not in self.request_times:
            self.request_times[platform] = deque()
        self.logger.info(f"Set {platform} rate limit to {limit} requests/minute")
    
    def reset(self, platform: str = None):
        """
        Reset rate limit counters.
        
        Args:
            platform: Platform to reset (all if None)
        """
        if platform:
            self.request_times[platform] = deque()
            self.logger.info(f"Reset rate limit for {platform}")
        else:
            for p in self.request_times:
                self.request_times[p] = deque()
            self.logger.info("Reset all rate limits")
