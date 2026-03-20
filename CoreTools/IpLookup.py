__author__ = "Yuval Malkan"

import requests


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



if __name__ == "__main__":
    ip = input("Enter IP address: ")
    result = get_ip_info(ip)
    for key, value in result.items():
        print(f"{key:<12} {value}")
