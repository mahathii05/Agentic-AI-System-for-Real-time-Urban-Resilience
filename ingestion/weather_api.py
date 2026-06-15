import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_KEY")   # matches your .env file

def get_weather(city="Kochi"):
    if not API_KEY:
        print("[weather_api] WARNING: OPENWEATHER_KEY not set in .env — using fallback values")
        return {"temp": 28.0, "humidity": 75, "rain": 0}

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        r = requests.get(url, timeout=8).json()

        if "main" not in r:
            print(f"[weather_api] Unexpected API response: {r.get('message', r)}")
            return {"temp": 28.0, "humidity": 75, "rain": 0}

        return {
            "temp":     r["main"]["temp"],
            "humidity": r["main"]["humidity"],
            "rain":     r.get("rain", {}).get("1h", 0)
        }

    except Exception as e:
        print(f"[weather_api] Request failed: {e}")
        return {"temp": 28.0, "humidity": 75, "rain": 0}