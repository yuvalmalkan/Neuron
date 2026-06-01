__author__ = "Yuval Malkan"

import requests
import re
import subprocess
import subprocess

def get_ip_info(ip: str) -> dict:
    res = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)

    if res.status_code != 200:
        return {"error": "Could not fetch IP info"}

    data = res.json()

    return {
        "ip": data.get("ip"),
        "hostname": data.get("hostname"),
        "city": data.get("city"),
        "region": data.get("region"),
        "country": data.get("country"),
        "location": data.get("loc"),
        "isp": data.get("org"),
        "timezone": data.get("timezone"),
    }




def ping_and_fingerprint(ip: str) -> dict:
    try:
        #run ping command
        output = subprocess.check_output(["ping", "-c", "1", "-W", "2", ip], text=True)

        #extract ttl using regex
        ttl_match = re.search(r"ttl=(\d+)", output)
        if ttl_match:
            ttl = int(ttl_match.group(1))

            if ttl <= 64:
                os_guess = "Linux/macOS/BSD"
            elif ttl <= 128:
                os_guess = "Windows"
            else:
                os_guess = "Network Hardware (Cisco/Solaris)"

            return {"status": "Up", "ttl": ttl, "os_guess": os_guess}

    except subprocess.CalledProcessError:
        return {"status": "Down/Unreachable", "ttl": None, "os_guess": "Unknown"}






def get_whois_info(ip: str) -> str:
    try:
        output = subprocess.check_output(["whois", ip], text=True)
        return output

    except subprocess.CalledProcessError:
        return "WHOIS lookup failed"






if __name__ == "__main__":
    ip = input("Enter IP address: ")
    result = get_ip_info(ip)

    for key, value in result.items():
        print(f"{key:<12} {value}")

    result = ping_and_fingerprint(ip)

    for key, value in result.items():
        print(f"{key:<12} {value}")

    print(f"who is: {get_whois_info(ip)}")





