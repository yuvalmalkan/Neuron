__author__ = "Yuval Malkan"

import threading
import Maigret
import Sherlock
from SocialMedia.Facebook import Facebook_info_from_file
from threading import Lock








"""
here the full osint scan will happen in one big function that will call all the different tools and combine the results into one report.
every tool will be called on a different thread or using async 

eventually all of the data will be fed into gemini to create a final report that will be more human readable and will include all the relevant information about the user, 
including links to their profiles on different platforms, their activity, and any other relevant information that was found during the scan.

"""


#x = Sherlock.search_username("yuvalmalkan")



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
        (Sherlock.search_username, "sherlock", username),
        (Maigret.Maigret_search_username, "maigret", username),
        # Add more functions here like:
        # (Facebook_info_from_file, "facebook", some_arg),
        # (some_other_function, "key_name", arg1, arg2),
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







def main():
    pass


