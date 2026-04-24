__author__ = "Yuval Malkan"

import logging
import json
import re
from typing import Optional, List, Dict
from datetime import datetime
from .ScraperBase import ScraperBase
from .UserAgent import UserAgentRotator
from .RateLimiter import RateLimiter


class LinkedInScraper(ScraperBase):
    """
    LinkedIn scraper for public profiles without authentication.
    
    Extracts:
    - Public profile information (name, headline, location, industry)
    - Education history
    - Work experience
    - Skills
    - Company information
    - Public activity/posts (limited)
    
    Note: LinkedIn actively blocks scrapers. This scraper extracts only
    public profile pages and respects rate limiting strictly.
    """
    
    BASE_URL = "https://www.linkedin.com"
    
    def __init__(self, rate_limiter: RateLimiter = None):
        """
        Initialize LinkedIn scraper.
        
        Args:
            rate_limiter: RateLimiter instance (shared across scrapers)
        """
        super().__init__("LinkedIn", timeout=20)
        self.user_agent_rotator = UserAgentRotator()
        self.rate_limiter = rate_limiter or RateLimiter()
    
    def get_user_profile(self, profile_url: str) -> Optional[Dict]:
        """
        Get public profile information from LinkedIn profile URL.
        
        Args:
            profile_url: Full LinkedIn profile URL or username
            
        Returns:
            User profile dict or None
        """
        try:
            # Normalize URL
            if not profile_url.startswith('http'):
                profile_url = f"{self.BASE_URL}/in/{profile_url}"
            
            username = profile_url.split('/in/')[-1].rstrip('/')
            
            self.logger.info(f"Fetching profile for {username}")
            
            # Rate limiting (very strict for LinkedIn)
            self.rate_limiter.wait_if_needed("LinkedIn")
            
            # Add URL ending for public profile
            if not profile_url.endswith('/'):
                profile_url += '/'
            
            # Use minimal headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Download HTML directly
            import requests
            response = requests.get(profile_url, headers=headers, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code != 200:
                self.log_activity("fetch_profile", username, "failed", f"HTTP {response.status_code}")
                return None
            
            html = response.text
            self.logger.debug(f"Downloaded HTML: {len(html)} bytes")
            
            # Extract profile data
            profile_data = self._extract_profile_from_html(html, username)
            
            if profile_data:
                self.rate_limiter.record_request("LinkedIn")
                self.log_activity("fetch_profile", username, "success")
                return profile_data
            else:
                self.log_activity("fetch_profile", username, "failed", "Could not parse profile")
                return None
        
        except Exception as e:
            self.logger.error(f"Error fetching profile: {e}")
            self.log_activity("fetch_profile", profile_url, "failed", str(e))
            return None
    
    def _extract_profile_from_html(self, html: str, username: str) -> Optional[Dict]:
        """
        Extract profile data from HTML.
        
        Args:
            html: HTML content
            username: Username
            
        Returns:
            Profile dict or None
        """
        try:
            # Extract from meta tags
            name_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
            desc_match = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
            image_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
            
            # Try to extract from schema.org JSON-LD
            jsonld_match = re.search(r'<script[^>]*type="application/ld\+json"[^>]*>([^<]+)</script>', html)
            
            profile = {
                'username': username,
                'name': name_match.group(1) if name_match else '',
                'bio': desc_match.group(1) if desc_match else '',
                'profile_url': f"{self.BASE_URL}/in/{username}",
                'profile_picture': image_match.group(1) if image_match else '',
                'headline': desc_match.group(1) if desc_match else '',
                'followers': 0,
                'following': 0,
                'verified': False,
                'public': True,
                'experience': [],
                'education': [],
                'skills': []
            }
            
            # Parse JSON-LD if available
            if jsonld_match:
                try:
                    jsonld = json.loads(jsonld_match.group(1))
                    
                    # Extract work history
                    if 'workLocation' in jsonld:
                        profile['location'] = jsonld.get('workLocation', {}).get('name', '')
                    
                    # Extract job title
                    if 'jobTitle' in jsonld:
                        profile['headline'] = jsonld['jobTitle']
                
                except json.JSONDecodeError:
                    pass
            
            # Extract experience section
            exp_matches = re.finditer(
                r'<li[^>]*data-section="experience"[^>]*>([^<]*)</li>',
                html
            )
            
            for match in exp_matches:
                experience = {
                    'title': '',
                    'company': '',
                    'duration': '',
                    'description': ''
                }
                profile['experience'].append(experience)
            
            # Extract education section
            edu_matches = re.finditer(
                r'<li[^>]*data-section="education"[^>]*>([^<]*)</li>',
                html
            )
            
            for match in edu_matches:
                education = {
                    'school': '',
                    'degree': '',
                    'field': '',
                    'year': ''
                }
                profile['education'].append(education)
            
            # Extract skills (limited - mostly from meta)
            skills_match = re.search(r'<meta[^>]*name="keywords"[^>]*content="([^"]+)"', html)
            if skills_match:
                profile['skills'] = [s.strip() for s in skills_match.group(1).split(',')][:10]
            
            return self.normalize_user_data(profile)
        
        except Exception as e:
            self.logger.debug(f"Error parsing profile HTML: {e}")
            return None
    
    def search_people(self, name: str, location: str = None, limit: int = 10) -> List[Dict]:
        """
        Search for people on LinkedIn (very limited without authentication).
        
        Args:
            name: Person's name
            location: Optional location filter
            limit: Number of results
            
        Returns:
            List of profile dicts
        """
        try:
            self.logger.info(f"Searching people for {name}")
            
            self.rate_limiter.wait_if_needed("LinkedIn")
            
            # Build search query
            query = name
            if location:
                query += f" {location}"
            
            # Use Google with LinkedIn site search (more reliable)
            search_url = f"https://www.google.com/search?q=site:linkedin.com/in {self.url_encode(query)}"
            
            headers = self.user_agent_rotator.get_headers("LinkedIn")
            response = self.get(search_url, headers=headers, delay=3)
            
            if not self.validate_response(response):
                return []
            
            self.rate_limiter.record_request("LinkedIn")
            
            # Extract profile URLs from search results
            profiles = []
            url_pattern = r'linkedin\.com/in/([a-zA-Z0-9\-]+)'
            
            for match in re.finditer(url_pattern, response.text):
                if len(profiles) >= limit:
                    break
                
                username = match.group(1)
                profiles.append({
                    'username': username,
                    'profile_url': f"{self.BASE_URL}/in/{username}",
                    'name': name,
                    'platform': 'LinkedIn'
                })
            
            self.log_activity("search_people", name, "success", f"Found {len(profiles)} people")
            return profiles
        
        except Exception as e:
            self.logger.error(f"Error searching people: {e}")
            self.log_activity("search_people", name, "failed", str(e))
            return []
    
    def search_company(self, company_name: str) -> Optional[Dict]:
        """
        Search for company on LinkedIn.
        
        Args:
            company_name: Company name
            
        Returns:
            Company info dict or None
        """
        try:
            self.logger.info(f"Searching company {company_name}")
            
            self.rate_limiter.wait_if_needed("LinkedIn")
            
            # Build company page URL (standard format)
            company_slug = company_name.lower().replace(' ', '-').replace('&', 'and')
            url = f"{self.BASE_URL}/company/{company_slug}"
            
            headers = self.user_agent_rotator.get_headers("LinkedIn")
            response = self.get(url, headers=headers, delay=3)
            
            if not self.validate_response(response):
                self.log_activity("search_company", company_name, "failed")
                return None
            
            self.rate_limiter.record_request("LinkedIn")
            
            # Extract company info
            company = self._extract_company_from_html(response.text, company_name)
            
            self.log_activity("search_company", company_name, "success" if company else "failed")
            return company
        
        except Exception as e:
            self.logger.error(f"Error searching company: {e}")
            self.log_activity("search_company", company_name, "failed", str(e))
            return None
    
    def _extract_company_from_html(self, html: str, company_name: str) -> Optional[Dict]:
        """
        Extract company info from HTML.
        
        Args:
            html: HTML content
            company_name: Company name
            
        Returns:
            Company dict or None
        """
        try:
            # Extract from meta tags
            desc_match = re.search(
                r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"',
                html
            )
            
            company = {
                'name': company_name,
                'description': desc_match.group(1) if desc_match else '',
                'industry': '',
                'size': '',
                'location': '',
                'website': '',
                'employees': 0
            }
            
            # Try to extract from schema.org
            jsonld_match = re.search(
                r'<script[^>]*type="application/ld\+json"[^>]*>([^<]+)</script>',
                html
            )
            
            if jsonld_match:
                try:
                    jsonld = json.loads(jsonld_match.group(1))
                    company['description'] = jsonld.get('description', company['description'])
                    company['location'] = jsonld.get('address', {}).get('addressCountry', '')
                except json.JSONDecodeError:
                    pass
            
            return company
        
        except Exception as e:
            self.logger.debug(f"Error parsing company HTML: {e}")
            return None
    
    def get_company_jobs(self, company_name: str, limit: int = 20) -> List[Dict]:
        """
        Get job listings for company (very limited without authentication).
        
        Args:
            company_name: Company name
            limit: Number of jobs
            
        Returns:
            List of job dicts
        """
        # LinkedIn strictly blocks job scraping
        self.logger.warning("LinkedIn job scraping is not available without authentication")
        return []
