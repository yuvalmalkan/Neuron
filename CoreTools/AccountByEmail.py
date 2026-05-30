import os
import json
import argparse
import requests
import concurrent.futures
from urllib.parse import quote
from rich.console import Console
from rich.progress import Progress

console = Console()

# Default User-Agent to prevent basic blocks
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"


def load_data():
    """Loads the site configurations from email-data.json"""
    json_path = "email-data.json"
    if not os.path.exists(json_path):
        console.print(f"[bold red]Error:[/bold red] '{json_path}' not found in the current directory.")
        exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("sites", [])


def execute_pre_check(session, pre_check_data):
    """Executes a pre-check to fetch necessary cookies/tokens before the main request."""
    try:
        url = pre_check_data.get("endpoint")
        method = pre_check_data.get("method", "GET")

        headers = pre_check_data.get("headers", {}) or {}
        headers["User-Agent"] = USER_AGENT

        res = session.request(method, url, headers=headers, timeout=10)

        if pre_check_data.get("type") == "cookie":
            cookie_name = pre_check_data.get("cookie_name")
            return session.cookies.get(cookie_name)
    except Exception:
        pass
    return None


def check_site(email, site):
    """Checks a single site for the existence of the email."""
    session = requests.Session()

    name = site.get("name")
    url = site.get("uri_check").replace("{account}", quote(email))
    method = site.get("method", "GET")
    data = site.get("data")
    headers = site.get("headers", {}) or {}

    e_code = site.get("e_code")
    e_string = site.get("e_string")
    m_string = site.get("m_string")

    # Handle pre-checks (e.g., getting CSRF tokens)
    pre_check = site.get("pre_check")
    if pre_check:
        token = execute_pre_check(session, pre_check)
        if token:
            for k, v in headers.items():
                if "{csrftoken_value}" in str(v):
                    headers[k] = v.replace("{csrftoken_value}", token)

    headers["User-Agent"] = USER_AGENT
    if data:
        data = data.replace("{account}", email)

    try:
        response = session.request(method, url, data=data, headers=headers, timeout=15)
        res_text = response.text
        res_code = response.status_code

        # Validation Logic
        if m_string and m_string in res_text:
            return name, False, url

        if res_code == e_code and (not e_string or e_string in res_text):
            return name, True, url

        return name, False, url
    except requests.RequestException:
        return name, False, url


def main():
    parser = argparse.ArgumentParser(description="Standalone Email OSINT Checker")
    parser.add_argument("-e", "--email", help="The email address to search.")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Number of concurrent threads.")
    args = parser.parse_args()

    # Interactive prompt if no arguments are provided
    if args.email:
        email = args.email
    else:
        console.print("[bold blue]🐦 Blackbird Email Checker (Standalone)[/bold blue]")
        try:
            email = input("Enter the email address to search: ").strip()
        except KeyboardInterrupt:
            console.print("\n[bold red]Cancelled.[/bold red]")
            exit(0)

        if not email:
            console.print("[bold red]Error:[/bold red] Email cannot be empty.")
            exit(1)

    sites = load_data()

    console.print(f"\n[bold blue]Starting Search for:[/bold blue] [bold white]{email}[/bold white]")
    console.print(f"[dim]Loaded {len(sites)} modules from email-data.json[/dim]\n")

    found_accounts = []

    # Run checks concurrently
    with Progress() as progress:
        task = progress.add_task("[cyan]Scanning modules...", total=len(sites))

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            future_to_site = {executor.submit(check_site, email, site): site for site in sites}

            for future in concurrent.futures.as_completed(future_to_site):
                site_name, exists, url = future.result()
                progress.advance(task)

                if exists:
                    found_accounts.append({"name": site_name, "url": url})
                    progress.console.print(
                        f"[bold green][+][/bold green] Found on [bold white]{site_name}[/bold white] -> [dim]{url}[/dim]")

    # Print summary
    console.print("\n[bold blue]--- Summary ---[/bold blue]")
    if found_accounts:
        console.print(f"[bold green]Matches found on {len(found_accounts)} sites:[/bold green]")
        for acc in found_accounts:
            console.print(f"  - [bold]{acc['name']}[/bold]: {acc['url']}")
    else:
        console.print("[bold yellow]No accounts found using this email.[/bold yellow]")


if __name__ == "__main__":
    main()