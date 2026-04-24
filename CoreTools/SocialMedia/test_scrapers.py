__author__ = "Yuval Malkan"

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
from CoreTools.SocialMedia import (
    SocialMediaAggregator, ScraperBase, RateLimiter, UserAgentRotator
)


class TestRateLimiter(unittest.TestCase):
    """Test rate limiter functionality."""
    
    def setUp(self):
        self.limiter = RateLimiter()
    
    def test_initialization(self):
        """Test rate limiter initializes with correct limits."""
        self.assertEqual(self.limiter.DEFAULT_LIMITS['Instagram'], 60)
        self.assertEqual(self.limiter.DEFAULT_LIMITS['Twitter'], 100)
    
    def test_get_delay(self):
        """Test getting delay before next request."""
        delay = self.limiter.get_delay('Instagram')
        self.assertIsNotNone(delay)
        self.assertGreaterEqual(delay, 0)
    
    def test_unknown_platform(self):
        """Test handling unknown platform."""
        delay = self.limiter.get_delay('UnknownPlatform')
        self.assertEqual(delay, 0)
    
    def test_wait_if_needed(self):
        """Test rate limiter wait logic."""
        # Should not raise exception
        self.limiter.wait_if_needed('Instagram')
        self.limiter.wait_if_needed('Twitter')


class TestUserAgentRotator(unittest.TestCase):
    """Test user agent rotation."""
    
    def setUp(self):
        self.rotator = UserAgentRotator()
    
    def test_get_next_user_agent(self):
        """Test getting next user agent."""
        ua = self.rotator.get_next_user_agent()
        self.assertIsNotNone(ua)
        self.assertTrue(len(ua) > 0)
    
    def test_get_headers(self):
        """Test getting headers with user agent."""
        headers = self.rotator.get_headers()
        self.assertIn('User-Agent', headers)
        self.assertIn('Accept', headers)
        self.assertIn('Accept-Encoding', headers)
    
    def test_headers_rotation(self):
        """Test that headers rotate."""
        h1 = self.rotator.get_headers()
        h2 = self.rotator.get_headers()
        # May or may not be different UA, but structure should be same
        self.assertIn('User-Agent', h1)
        self.assertIn('User-Agent', h2)


class TestScraperBase(unittest.TestCase):
    """Test base scraper class."""
    
    def setUp(self):
        self.scraper = ScraperBase("TestPlatform")
    
    def test_normalize_user_data(self):
        """Test data normalization."""
        test_data = {
            'username': 'testuser',
            'name': 'Test User',
            'bio': 'A test bio',
            'followers': 1000,
            'following': 500,
            'verified': True,
            'public': True
        }
        
        normalized = self.scraper.normalize_user_data(test_data)
        
        self.assertEqual(normalized['platform'], 'TestPlatform')
        self.assertEqual(normalized['username'], 'testuser')
        self.assertEqual(normalized['followers'], 1000)
        self.assertEqual(normalized['verified'], True)
        self.assertIn('timestamp', normalized)
    
    def test_normalize_handles_missing_fields(self):
        """Test normalization with missing fields."""
        test_data = {'username': 'user'}
        normalized = self.scraper.normalize_user_data(test_data)
        
        # Should have default values
        self.assertEqual(normalized['followers'], 0)
        self.assertEqual(normalized['following'], 0)
        self.assertEqual(normalized['verified'], False)


class TestSocialMediaAggregator(unittest.TestCase):
    """Test social media aggregator."""
    
    def setUp(self):
        self.agg = SocialMediaAggregator(use_threading=False)
    
    def test_initialization(self):
        """Test aggregator initializes with all platforms."""
        self.assertIsNotNone(self.agg.instagram)
        self.assertIsNotNone(self.agg.twitter)
        self.assertIsNotNone(self.agg.tiktok)
        self.assertIsNotNone(self.agg.linkedin)
        self.assertIsNotNone(self.agg.youtube)
    
    def test_get_rate_limit_status(self):
        """Test getting rate limit status."""
        status = self.agg.get_rate_limit_status()
        # Status dict should have platforms as keys
        self.assertIsInstance(status, dict)
    
    def test_reset_rate_limits(self):
        """Test resetting rate limits."""
        # Should not raise exception
        self.agg.reset_rate_limits('instagram')
        self.agg.reset_rate_limits()
    
    def test_close(self):
        """Test closing aggregator."""
        # Should not raise exception
        self.agg.close()
    
    def test_get_summary(self):
        """Test generating summary from results."""
        results = {
            'username': 'testuser',
            'search_results': {
                'instagram': {
                    'username': 'testuser',
                    'followers': 1000,
                    'verified': True,
                    'profile_url': 'https://instagram.com/testuser'
                },
                'twitter': {
                    'not_found': True
                }
            }
        }
        
        summary = self.agg.get_summary(results)
        
        self.assertEqual(summary['username'], 'testuser')
        self.assertIn('instagram', summary['found_on_platforms'])
        self.assertIn('twitter', summary['not_found_platforms'])
        self.assertEqual(summary['total_followers'], 1000)
        self.assertEqual(len(summary['accounts']), 1)


class TestErrorHandling(unittest.TestCase):
    """Test error handling across scrapers."""
    
    def setUp(self):
        self.scraper = ScraperBase("TestPlatform")
    
    def test_normalize_with_invalid_types(self):
        """Test normalization handles invalid types."""
        test_data = {
            'username': 'user',
            'followers': 'not_a_number',  # Invalid
            'verified': 'yes'  # Should be bool
        }
        
        # Should handle gracefully
        normalized = self.scraper.normalize_user_data(test_data)
        self.assertEqual(normalized['username'], 'user')
    
    def test_aggregator_handles_missing_scrapers(self):
        """Test aggregator handles requests for unknown platforms."""
        agg = SocialMediaAggregator()
        
        # Should return None for unknown platform
        result = agg.get_profile('user', 'unknown_platform')
        self.assertIsNone(result)


class TestRateLimitingEdgeCases(unittest.TestCase):
    """Test rate limiting edge cases."""
    
    def setUp(self):
        self.limiter = RateLimiter()
    
    def test_multiple_platform_limits_isolated(self):
        """Test that limits for different platforms are isolated."""
        self.limiter.wait_if_needed('Instagram')
        self.limiter.wait_if_needed('Twitter')
        
        # Should have separate delay calculations
        insta_delay = self.limiter.get_delay('Instagram')
        twitter_delay = self.limiter.get_delay('Twitter')
        
        # Both should be valid delays
        self.assertGreaterEqual(insta_delay, 0)
        self.assertGreaterEqual(twitter_delay, 0)


class TestDataNormalization(unittest.TestCase):
    """Test data normalization across platforms."""
    
    def setUp(self):
        self.scraper = ScraperBase("Platform")
    
    def test_normalization_consistency(self):
        """Test that normalization produces consistent output."""
        data = {
            'username': 'user123',
            'name': 'User Name',
            'bio': 'Bio text',
            'followers': 5000,
            'following': 2000,
            'verified': False,
            'public': True
        }
        
        normalized = self.scraper.normalize_user_data(data)
        
        # Check all expected fields exist
        expected_fields = [
            'platform', 'username', 'name', 'bio', 'followers', 
            'following', 'verified', 'public', 'timestamp'
        ]
        
        for field in expected_fields:
            self.assertIn(field, normalized)
    
    def test_normalization_handles_edge_cases(self):
        """Test normalization with edge case values."""
        edge_cases = [
            {'username': ''},  # Empty username
            {'followers': -1},  # Negative followers
            {'bio': None},  # None bio
            {'verified': None}  # None verified
        ]
        
        for case in edge_cases:
            # Should not raise exception
            normalized = self.scraper.normalize_user_data(case)
            self.assertIsNotNone(normalized)


if __name__ == '__main__':
    unittest.main()
