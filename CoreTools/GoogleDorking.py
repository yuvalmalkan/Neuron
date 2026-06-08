__author__ = "Yuval Malkan"



import requests
import re
import dotenv
import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")


def google_search(query: str, num_results: int = 10) -> list:
    """raw google search returns list of result snippets and links"""
    res = requests.get(
        "https://www.googleapis.com/customsearch/v1",
        params={
            "key": GOOGLE_API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "num": num_results
        },
        timeout=10
    )

    if res.status_code != 200:
        return []

    items = res.json().get("items", [])
    return [{
        "title": item.get("title"),
        "link": item.get("link"),
        "snippet": item.get("snippet")
    } for item in items]


def extract_emails_from_text(text: str) -> list:
    """pull all email addresses from any text"""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    return list(set(emails))  # deduplicate


def find_emails_by_name(first_name: str, last_name: str) -> dict:
    """
    run multiple dorks for a person and collect all emails found
    """
    full_name = f"{first_name} {last_name}"

    #different dork strategies
    dorks = [
        f'"{full_name}" email',
        f'"{full_name}" "@gmail.com" OR "@yahoo.com" OR "@hotmail.com"',
        f'"{full_name}" contact',
        f'"{full_name}" site:linkedin.com',
        f'"{full_name}" site:facebook.com',
    ]

    all_emails = []
    sources = []

    for dork in dorks:
        results = google_search(dork)
        for r in results:
            #extract emails from snippet text
            found = extract_emails_from_text(r.get("snippet", ""))
            if found:
                all_emails.extend(found)
                sources.append({
                    "emails": found,
                    "source": r.get("link"),
                    "context": r.get("snippet")
                })

    return {
        "name": full_name,
        "emails_found": list(set(all_emails)),  # remove duplicates
        "sources": sources,
        "total": len(set(all_emails))
    }


def debug_search(query: str):
    res = requests.get(
        "https://www.googleapis.com/customsearch/v1",
        params={
            "key": GOOGLE_API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "num": 10
        },
        timeout=10
    )

    print("Status:", res.status_code)
    data = res.json()

    #check for API errors
    if "error" in data:
        print("API ERROR:", data["error"]["message"])
        return

    items = data.get("items", [])
    print(f"Results returned: {len(items)}")

    for i, item in enumerate(items):
        print(f"\n--- Result {i + 1} ---")
        print("Title:", item.get("title"))
        print("Link:", item.get("link"))
        print("Snippet:", item.get("snippet"))


