#!/usr/bin/env python3
"""
Social Media OSINT Scraper - Interactive Tester

Test social media scrapers with real data from public profiles.
No authentication required - uses public page scraping.

Usage:
    python3 test_scraper_interactive.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from CoreTools.SocialMedia import SocialMediaAggregator


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70)


def print_profile(profile):
    """Print formatted profile information."""
    if not profile:
        print("❌ Profile not found or error occurred")
        return
    
    print(f"Platform:    {profile.get('platform', 'Unknown')}")
    print(f"Username:    {profile.get('username', '')}")
    print(f"Name:        {profile.get('name', '')}")
    print(f"Bio:         {profile.get('bio', '')}")
    print(f"Followers:   {profile.get('followers', 0):,}")
    print(f"Following:   {profile.get('following', 0):,}")
    print(f"Verified:    {'✓' if profile.get('verified') else '✗'}")
    print(f"Public:      {'✓' if profile.get('public') else '✗'}")
    print(f"Profile URL: {profile.get('profile_url', '')}")
    print(f"Timestamp:   {profile.get('timestamp', '')}")


def test_single_platform():
    """Test a single platform."""
    print_header("SINGLE PLATFORM SEARCH")
    
    platforms = {
        '1': 'instagram',
        '2': 'twitter',
        '3': 'tiktok',
        '4': 'linkedin',
        '5': 'youtube',
        '0': 'exit'
    }
    
    print("\nSelect Platform:")
    for key, platform in list(platforms.items())[:-1]:
        print(f"  {key}. {platform.capitalize()}")
    print(f"  {list(platforms.keys())[-1]}. Exit")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice not in platforms:
        print("❌ Invalid choice")
        return
    
    platform = platforms[choice]
    
    if choice == '0':
        return False
    
    username = input(f"\nEnter username (without @): ").strip()
    
    if not username:
        print("❌ Username cannot be empty")
        return
    
    print_header(f"SEARCHING {platform.upper()}")
    print(f"⏳ Fetching {platform} profile for @{username}...\n")
    
    agg = SocialMediaAggregator()
    profile = agg.get_profile(username, platform)
    
    print_profile(profile)
    
    return True


def test_all_platforms():
    """Test username across all platforms."""
    print_header("CROSS-PLATFORM SEARCH")
    
    username = input("\nEnter username (without @): ").strip()
    
    if not username:
        print("❌ Username cannot be empty")
        return
    
    print_header(f"SEARCHING FOR @{username} ON ALL PLATFORMS")
    print(f"⏳ This may take a minute...\n")
    
    agg = SocialMediaAggregator()
    results = agg.search_username(username)
    
    summary = agg.get_summary({'username': username, 'search_results': results})
    
    print(f"\nUsername: {summary['username']}")
    print(f"Found on: {', '.join(summary['found_on_platforms']) or 'None'}")
    print(f"Total Followers: {summary['total_followers']:,}")
    print(f"\nAccounts:\n")
    
    for account in summary['accounts']:
        print(f"  {account.get('platform', 'Unknown').upper()}:")
        print(f"    Username: {account.get('username', '')}")
        print(f"    Name: {account.get('name', '')}")
        print(f"    Followers: {account.get('followers', 0):,}")
        print(f"    Verified: {'✓' if account.get('verified') else '✗'}")
        print(f"    URL: {account.get('profile_url', '')}\n")
    
    if summary['not_found_platforms']:
        print(f"Not found on: {', '.join(summary['not_found_platforms'])}")
    
    return True


def main():
    """Main interactive menu."""
    agg = None
    
    try:
        print_header("SOCIAL MEDIA OSINT SCRAPER - INTERACTIVE TESTER")
        
        while True:
            print("\nSelect Search Type:")
            print("  1. Single Platform Search")
            print("  2. Cross-Platform Search (All)")
            print("  0. Exit")
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == '1':
                if not test_single_platform():
                    break
            elif choice == '2':
                if not test_all_platforms():
                    break
            elif choice == '0':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
            
            input("\nPress Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if agg:
            agg.close()


if __name__ == '__main__':
    main()
