from ingestion.weather_api import get_weather

def flood_status():
    try:
        data = get_weather()
        if data["rain"] > 15 or data["humidity"] > 90:
            return "High Flood Risk"
        return "Normal Flood Risk"
    except Exception as e:
        print(f"[flood_agent] Error: {e}")
        return "Normal Flood Risk"