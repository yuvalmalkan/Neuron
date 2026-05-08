__author__ = "Yuval Malkan"

import threading
import Maigret
import Sherlock
from SocialMedia.Facebook import Facebook_info_from_file








"""
here the full osint scan will happen in one big function that will call all the different tools and combine the results into one report.
every tool will be called on a different thread or using async 

eventually all of the data will be fed into gemini to create a final report that will be more human readable and will include all the relevant information about the user, 
including links to their profiles on different platforms, their activity, and any other relevant information that was found during the scan.

"""


#x = Sherlock.search_username("yuvalmalkan")



#function for every scan by arg, then if else to combine them


def OsintByUsername(username: str) -> dict:
    data = {}


    return data






def main():
    pass


