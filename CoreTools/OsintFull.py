__author__ = "Yuval Malkan"

import threading
from Maigret import Maigret_search_username
from Sherlock import search_username
from accountFinder import findByUsername
from ByPhone.telegram_lookup import lookup_username_sync
from SocialMedia.Instagram import get_info_from_html as instagram_search
from SocialMedia.Facebook import Facebook_info_from_file
from SocialMedia.Linkedin import scrape_linkedin_osint
from GoogleDorking import find_emails_by_name
from threading import Lock

"""
here the full osint scan will happen in one big function that will call all the different tools and combine the results into one report.
every tool will be called on a different thread or using async 

eventually all of the data will be fed into gemini to create a final report that will be more human readable and will include all the relevant information about the user, 
including links to their profiles on different platforms, their activity, and any other relevant information that was found during the scan.
"""


#function for every scan by arg, then if else to combine them

def run_function_in_thread(func, results_dict, key, *args, **kwargs):
    """Helper function to run a function in a thread and store result"""
    try:
        result = func(*args, **kwargs)
        results_dict[key] = result
    except Exception as e:
        results_dict[key] = {"error": str(e)}


def OsintByUsername(username: str) -> dict:
    results = {}
    threads = []

    # Define all the functions you want to run
    functions_to_run = [
        (search_username, "sherlock", username),
        (Maigret_search_username, "maigret", username),
        (findByUsername, "accountFinder", username),
        (lookup_username_sync, "telegram", username),

        # Add more functions here like:
        # (instagram_search, "instagram", some_html_filename),
        # (Facebook_info_from_file, "facebook", some_html_filename),
        # (scrape_linkedin_osint, "linkedin", profile_url),
        # (find_emails_by_name, "google_dork", first_name, last_name),
    ]

    # Create and start a thread for each function
    for func, key, *args in functions_to_run:
        thread = threading.Thread(
            target=run_function_in_thread,
            args=(func, results, key, *args)
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    return results






if __name__ == "__main__":
    username = input("Enter username to scan: ")
    report = OsintByUsername(username)
    print(report)