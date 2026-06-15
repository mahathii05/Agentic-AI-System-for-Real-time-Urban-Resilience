import requests

API_KEY = "ZzJ85mNOLHTTLohe8XyJvpHcSAA16JZU"

def get_traffic():
    try:
        url = (
            f"https://api.tomtom.com/traffic/services/4/flowSegmentData/"
            f"absolute/10/json?point=9.9312,76.2673&key={API_KEY}"
        )
        r = requests.get(url, timeout=8).json()

        if "flowSegmentData" not in r:
            print(f"[traffic_api] Unexpected API response: {r}")
            return 30, 50   # fallback: currentSpeed=30, freeFlowSpeed=50

        data = r["flowSegmentData"]
        return data["currentSpeed"], data["freeFlowSpeed"]

    except Exception as e:
        print(f"[traffic_api] Request failed: {e}")
        return 30, 50       # fallback values