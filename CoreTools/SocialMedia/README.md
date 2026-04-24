# Social Media OSINT Scrapers

Comprehensive non-authenticated social media scraping toolkit for OSINT reconnaissance. Gather public profile information, posts, videos, and metadata from major social media platforms without requiring API keys or user authentication.

## Supported Platforms

- **Instagram** - Public profiles, followers, posts, hashtags
- **Twitter/X** - Profiles, tweets, followers, search, trends
- **TikTok** - Profiles, videos, followers, engagement metrics
- **LinkedIn** - Public profiles, companies, people search
- **YouTube** - Channels, videos, metadata, statistics

## Features

### Core Infrastructure

- **Rate Limiting** - Token bucket algorithm with per-platform limits to avoid detection
- **User Agent Rotation** - 12+ realistic rotating user agents (Chrome, Firefox, Safari, Edge, mobile)
- **Automatic Retry** - Exponential backoff retry logic (1s, 2s, 4s, 8s) for failed requests
- **Error Handling** - Graceful handling of 404, 429, 403, timeouts
- **Data Normalization** - Consistent output format across all platforms

### Platform-Specific Features

#### Instagram
```python
from CoreTools.SocialMedia import InstagramScraper

scraper = InstagramScraper()
profile = scraper.get_user_profile('username')
posts = scraper.get_user_posts('username', limit=10)
hashtag_posts = scraper.search_by_hashtag('python', limit=20)
```

Data extracted:
- Username, name, bio, profile picture
- Follower/following counts
- Recent posts (captions, likes, comments)
- Hashtags used

#### Twitter/X
```python
from CoreTools.SocialMedia import TwitterScraper

scraper = TwitterScraper()
profile = scraper.get_user_profile('username')
tweets = scraper.get_user_tweets('username', limit=100)
search_results = scraper.search_tweets('#python', limit=50)
trends = scraper.get_trends()
```

Data extracted:
- Profile info (name, bio, followers, following)
- Tweet text, engagement (likes, retweets)
- Tweet metadata (timestamps, language)
- Hashtags and mentions

#### TikTok
```python
from CoreTools.SocialMedia import TikTokScraper

scraper = TikTokScraper()
profile = scraper.get_user_profile('username')
videos = scraper.get_user_videos('username', limit=30)
hashtag_videos = scraper.search_by_hashtag('FYP', limit=50)
```

Data extracted:
- Profile info (username, bio, follower count)
- Video list and statistics
- Audio information
- Engagement metrics (likes, comments, shares)

#### LinkedIn
```python
from CoreTools.SocialMedia import LinkedInScraper

scraper = LinkedInScraper()
profile = scraper.get_user_profile('https://linkedin.com/in/username')
people = scraper.search_people('John Doe', location='San Francisco')
company = scraper.search_company('Google')
```

Data extracted:
- Public profile info (name, headline, location)
- Education history
- Work experience
- Skills and endorsements
- Company information

#### YouTube
```python
from CoreTools.SocialMedia import YouTubeScraper

scraper = YouTubeScraper()
channel = scraper.get_channel_info('UCxxxxxxxxxxxxxxx')
videos = scraper.get_channel_videos('UCxxxxxxxxxxxxxxx', limit=50)
search_results = scraper.search_videos('python tutorial', limit=20)
```

Data extracted:
- Channel info (name, subscribers, description)
- Video list and statistics
- Video metadata (duration, tags, descriptions)
- Social media links from channel

## Unified Interface

Use the `SocialMediaAggregator` to search across all platforms:

```python
from CoreTools.SocialMedia import SocialMediaAggregator

agg = SocialMediaAggregator()

# Search for same username across all platforms
results = agg.search_username('john_doe')
summary = agg.get_summary(results)

print(f"Found on: {summary['found_on_platforms']}")
print(f"Total followers: {summary['total_followers']}")
for account in summary['accounts']:
    print(f"  {account['platform']}: {account['followers']} followers")

# Get profile from specific platform
profile = agg.get_profile('john_doe', 'twitter')

# Get posts from platform
posts = agg.get_posts('john_doe', 'instagram', limit=20)

# Search by hashtag
hashtag_posts = agg.search_by_hashtag('cybersecurity', 'twitter')

# Check rate limiting
status = agg.get_rate_limit_status()

# Reset rate limits
agg.reset_rate_limits('twitter')
```

## Rate Limiting

Built-in rate limiting to avoid detection and respect platform resources:

| Platform | Limit | Window |
|----------|-------|--------|
| Instagram | 60 | 1 minute |
| Twitter | 100 | 1 minute |
| TikTok | 60 | 1 minute |
| LinkedIn | 20 | 1 minute |
| YouTube | 100 | 1 minute |

Rate limiter uses token bucket algorithm and automatically adds delays between requests.

## Data Normalization

All scrapers return standardized profile format:

```python
{
    'platform': 'instagram',
    'username': 'john_doe',
    'name': 'John Doe',
    'bio': 'Software developer',
    'profile_url': 'https://instagram.com/john_doe',
    'followers': 1000,
    'following': 500,
    'verified': True,
    'public': True,
    'timestamp': '2024-04-24T10:30:00',
    'posts': [...]  # Platform-specific posts/content
}
```

## Error Handling

Scrapers gracefully handle common errors:

- **404 Not Found** - Profile doesn't exist (returns empty profile)
- **429 Too Many Requests** - Rate limited (auto-retry with backoff)
- **403 Forbidden** - Access denied (returns error message)
- **Timeout** - Request timed out (auto-retry up to 3 times)
- **Connection Error** - Network issue (auto-retry with backoff)

## Security & Ethics

### Important Notes

⚠️ **Terms of Service**: These scrapers may violate some platforms' Terms of Service. Use responsibly and legally.

⚠️ **Rate Limiting**: Scrapers implement conservative rate limits to minimize detection risk and respect platform resources.

⚠️ **Private Data**: Only public data is scraped. Private accounts will not return data.

⚠️ **Robots.txt**: Some platforms don't allow scraping. Respect platform policies.

### Best Practices

1. **Use rate limiting** - Always use the built-in rate limiter
2. **Cache results** - Minimize repeated requests for same profiles
3. **Rotate user agents** - Built-in rotation helps avoid detection
4. **Add delays** - Implement additional delays between requests
5. **Log activity** - Track what data you're collecting and why
6. **Respect privacy** - Only collect necessary data
7. **Follow laws** - Ensure compliance with local regulations

## Testing

Run the test suite:

```bash
python3 -m unittest CoreTools.SocialMedia.test_scrapers -v
```

Tests cover:
- Rate limiting functionality
- User agent rotation
- Data normalization
- Error handling
- Aggregator functionality
- Edge cases and invalid inputs

## Architecture

```
CoreTools/SocialMedia/
├── __init__.py                 # Package exports
├── ScraperBase.py              # Base class for all scrapers
├── RateLimiter.py              # Rate limiting engine
├── UserAgent.py                # User agent rotation
├── InstagramScraper.py         # Instagram implementation
├── TwitterScraper.py           # Twitter/X implementation
├── TikTokScraper.py            # TikTok implementation
├── LinkedInScraper.py          # LinkedIn implementation
├── YouTubeScraper.py           # YouTube implementation
├── SocialMediaAggregator.py    # Unified interface
└── test_scrapers.py            # Unit tests
```

## Future Enhancements

- [ ] Caching layer for frequently accessed profiles
- [ ] Database storage for scraped data
- [ ] Comparison views (profile changes over time)
- [ ] Export to CSV/JSON
- [ ] Webhook notifications for profile updates
- [ ] Additional platforms (Reddit, Telegram, Discord)
- [ ] Sentiment analysis on posts
- [ ] Network graph visualization

## Troubleshooting

**"403 Forbidden" errors**: Platform detected scraping. Wait before retrying.

**"429 Too Many Requests"**: Rate limit exceeded. Check `agg.get_rate_limit_status()`.

**Empty profile data**: Profile may be private or deleted. Check profile URL.

**Timeout errors**: Network issue or platform slow. Implement retry logic.

## Author

Yuval Malkan

## License

Project Neuron - See LICENSE for details
