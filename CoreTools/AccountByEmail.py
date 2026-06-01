__author__ = "Yuval Malkan"

import os
import json
import requests
import concurrent.futures
from urllib.parse import quote

#default user agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"


def _load_data(json_path: str) -> list:
    """internal function to load site configurations."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Configuration file '{json_path}' not found.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("sites", [])


def _execute_pre_check(session: requests.Session, pre_check_data: dict) -> str:
    """internal function to fetch necessary cookies/tokens before the main request."""
    try:
        url = pre_check_data.get("endpoint")
        method = pre_check_data.get("method", "GET")

        headers = pre_check_data.get("headers", {}) or {}
        headers["User-Agent"] = USER_AGENT

        session.request(method, url, headers=headers, timeout=10)

        if pre_check_data.get("type") == "cookie":
            cookie_name = pre_check_data.get("cookie_name")
            return session.cookies.get(cookie_name)
    except Exception:
        pass
    return None


def _check_site(email: str, site: dict) -> dict:
    """internal function to check a single site for the existence of the email"""
    session = requests.Session()

    name = site.get("name")
    url = site.get("uri_check").replace("{account}", quote(email))
    method = site.get("method", "GET")
    data = site.get("data")
    headers = site.get("headers", {}) or {}

    e_code = site.get("e_code")
    e_string = site.get("e_string")
    m_string = site.get("m_string")


    #handle pre checks
    pre_check = site.get("pre_check")
    if pre_check:
        token = _execute_pre_check(session, pre_check)
        if token:
            for k, v in headers.items():
                if "{csrftoken_value}" in str(v):
                    headers[k] = v.replace("{csrftoken_value}", token)

    headers["User-Agent"] = USER_AGENT
    if data:
        data = data.replace("{account}", email)

    result = {
        "site": name,
        "exists": False,
        "url": url,
        "category": site.get("cat", "unknown")
    }



    try:
        response = session.request(method, url, data=data, headers=headers, timeout=15)
        res_text = response.text
        res_code = response.status_code

        #validation Logic
        if m_string and m_string in res_text:
            return result

        if res_code == e_code and (not e_string or e_string in res_text):
            result["exists"] = True
            return result

        return result

    except requests.RequestException:
        return result


def scan_email(email: str, json_path: str = "email-data.json", max_threads: int = 10) -> dict:
    """
    Scans various platforms to check if an email is registered.

    Args:
        email (str): The target email address.
        json_path (str): Path to the JSON configuration file.
        max_threads (int): Number of concurrent requests to make.

    Returns:
        dict: A dictionary containing the target email, summary metrics, and a list of all results.
    """
    # Ensure the path is relative to the current file if an absolute path isn't provided
    if not os.path.isabs(json_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, json_path)

    sites = _load_data(json_path)

    final_output = {
        "target_email": email,
        "total_scanned": len(sites),
        "total_found": 0,
        "found_accounts": [],
        "all_results": []
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_site = {executor.submit(_check_site, email, site): site for site in sites}

        for future in concurrent.futures.as_completed(future_to_site):
            try:
                res = future.result()
                final_output["all_results"].append(res)

                if res["exists"]:
                    final_output["found_accounts"].append(res)
                    final_output["total_found"] += 1
            except Exception as exc:
                pass

    return final_output

if __name__ == "__main__":
    print(scan_email("test@gmail.com"))