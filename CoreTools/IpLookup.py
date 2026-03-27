__author__ = "Yuval Malkan"

import requests
import re
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
        # Run a single ping command (macOS/Linux syntax)
        output = subprocess.check_output(["ping", "-c", "1", "-W", "2", ip], text=True)

        # Extract TTL using a basic regex
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




import subprocess

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



"""
Connection-specific DNS Suffix  . : lan
   IPv6 Address. . . . . . . . . . . : 2a0d:6fc2:5ad1:8c00:f005:2ad8:39cf:d2ea
   Temporary IPv6 Address. . . . . . : 2a0d:6fc2:5ad1:8c00:d447:dd17:d773:8e7a
   Link-local IPv6 Address . . . . . : fe80::f955:e95:a49e:852e%17
   IPv4 Address. . . . . . . . . . . : 192.168.1.175
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : fe80::d635:1dff:fe4f:e24d%17
                                       192.168.1.1

"""


