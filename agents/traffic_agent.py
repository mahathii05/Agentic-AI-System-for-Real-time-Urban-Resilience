from ingestion.traffic_api import get_traffic

def traffic_status():
    try:
        current, free = get_traffic()
        if current / free < 0.5:
            return "Heavy Traffic"
        return "Traffic Normal"
    except Exception as e:
        print(f"[traffic_agent] Error: {e}")
        return "Traffic Normal"