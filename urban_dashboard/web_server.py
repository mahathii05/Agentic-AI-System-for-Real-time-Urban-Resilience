import sys
import os as _os_init

# Ensure project root is on path regardless of how uvicorn is invoked
_this_file  = _os_init.path.abspath(__file__)
_module_dir = _os_init.path.dirname(_this_file)           # urban_dashboard/
_project_root = _os_init.path.dirname(_module_dir)        # urban_resilience/
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from anthropic import Anthropic
from dotenv import load_dotenv
import json
import os
import requests as http_requests
from datetime import datetime

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Paths
# ----------------------------
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT  = os.path.dirname(BASE_DIR)
STATIC_DIR    = os.path.join(BASE_DIR, "static")
ALERT_FILE    = os.path.join(PROJECT_ROOT, "latest_alert.txt")

os.makedirs(STATIC_DIR, exist_ok=True)

# ----------------------------
# API Keys
# ----------------------------
anthropic_client    = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")

# ----------------------------
# Serve frontend
# ----------------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def homepage():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return JSONResponse({"error": "index.html not found"}, status_code=404)
    return FileResponse(index_path)

@app.get("/alert")
def get_alert():
    if not os.path.exists(ALERT_FILE):
        return {"status": "No data yet"}
    try:
        with open(ALERT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def fetch_real_weather_data(lat: float, lon: float):
    if not OPENWEATHER_KEY:
        return {"error": "OPENWEATHER_KEY not set in .env"}
    result = {}
    try:
        w = http_requests.get(
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}&units=metric",
            timeout=8
        ).json()
        result["city"]         = w.get("name", "Unknown Location")
        result["country"]      = w.get("sys", {}).get("country", "")
        result["temperature"]  = w.get("main", {}).get("temp", "N/A")
        result["humidity"]     = w.get("main", {}).get("humidity", "N/A")
        result["wind_speed"]   = w.get("wind", {}).get("speed", 0)
        result["weather_desc"] = w.get("weather", [{}])[0].get("description", "N/A")
        result["rain_1h"]      = w.get("rain", {}).get("1h", 0)
        result["rain_3h"]      = w.get("rain", {}).get("3h", 0)
        result["clouds"]       = w.get("clouds", {}).get("all", 0)
        result["visibility"]   = w.get("visibility", 10000)
    except Exception as e:
        result["weather_error"] = str(e)

    try:
        aq = http_requests.get(
            f"http://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}",
            timeout=8
        ).json()
        comp      = aq.get("list", [{}])[0].get("components", {})
        aqi_index = aq.get("list", [{}])[0].get("main", {}).get("aqi", 0)
        labels    = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
        result["aqi"]       = aqi_index
        result["aqi_label"] = labels.get(aqi_index, "Unknown")
        result["pm2_5"]     = comp.get("pm2_5", "N/A")
        result["pm10"]      = comp.get("pm10", "N/A")
        result["co"]        = comp.get("co", "N/A")
        result["no2"]       = comp.get("no2", "N/A")
        result["o3"]        = comp.get("o3", "N/A")
    except Exception as e:
        result["aqi_error"] = str(e)

    result["local_time"]  = datetime.utcnow().strftime("%H:%M UTC")
    result["hour_of_day"] = datetime.utcnow().hour
    return result


@app.post("/location-status")
async def location_status(request: Request):
    data = await request.json()
    lat  = data.get("lat")
    lon  = data.get("lon")
    if lat is None or lon is None:
        return JSONResponse({"error": "lat and lon required"}, status_code=400)

    real = fetch_real_weather_data(lat, lon)

    if "error" not in real:
        summary = f"""
REAL LIVE DATA for {real.get('city','?')}, {real.get('country','')}:
- Temperature: {real.get('temperature')}°C, {real.get('weather_desc')}
- Humidity: {real.get('humidity')}%, Wind: {real.get('wind_speed')} m/s
- Rainfall last 1h: {real.get('rain_1h')} mm, last 3h: {real.get('rain_3h')} mm
- Clouds: {real.get('clouds')}%, Visibility: {real.get('visibility')} m
- Air Quality: {real.get('aqi_label')} (AQI index {real.get('aqi')}/5)
- PM2.5: {real.get('pm2_5')} μg/m³, PM10: {real.get('pm10')} μg/m³
- NO2: {real.get('no2')} μg/m³, CO: {real.get('co')} μg/m³
- Time: {real.get('local_time')} (hour {real.get('hour_of_day')})"""
    else:
        summary = f"Live weather unavailable: {real.get('error')}"

    prompt = f"""You are an Urban Resilience AI analyst.
Location: Latitude {lat}, Longitude {lon}

{summary}

Using ONLY the real data above, assess urban risks for this location.
For traffic: use your knowledge of typical traffic in this specific city at hour {real.get('hour_of_day','?')}.
For flood: base on rainfall mm values and whether this city is flood-prone.
For power: consider weather stress on grid.
For crowd: use city knowledge + time of day.

Return ONLY a raw JSON object, no markdown, no backticks:
{{
  "level": "one of: ✅ NORMAL / ⚠️ WARNING / 🚨 CRITICAL",
  "city": "city name, country",
  "flood": "flood risk statement using real rainfall data",
  "traffic": "real traffic assessment for this city and time",
  "power": "power grid status",
  "crowd": "crowd density estimate",
  "aqi": "air quality description with real PM2.5 value",
  "temperature": "temp and conditions",
  "risk_score": <0-12>,
  "advice": "specific advice for someone currently at this location"
}}"""

    try:
        resp = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = resp.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
            raw = raw.strip()
        s, e2 = raw.find("{"), raw.rfind("}") + 1
        if s != -1 and e2 > s:
            raw = raw[s:e2]
        result = json.loads(raw)
        result["raw_weather"] = {
            "city":        real.get("city", ""),
            "temperature": real.get("temperature", ""),
            "humidity":    real.get("humidity", ""),
            "rain_1h":     real.get("rain_1h", 0),
            "wind_speed":  real.get("wind_speed", 0),
            "aqi":         real.get("aqi_label", ""),
            "pm2_5":       real.get("pm2_5", ""),
        }
        return result
    except json.JSONDecodeError:
        return {
            "level": "⚠️ WARNING",
            "city": real.get("city", "Unknown"),
            "flood": f"Rainfall: {real.get('rain_1h',0)}mm/h",
            "traffic": "Data unavailable",
            "power": "Data unavailable",
            "crowd": "Data unavailable",
            "aqi": real.get("aqi_label", "N/A"),
            "temperature": f"{real.get('temperature','N/A')}°C",
            "risk_score": 0,
            "advice": "Check local sources for current conditions."
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)



@app.get("/api/air-quality")
async def air_quality_map(lat: float, lon: float):
    """Return real AQI data for any lat/lon — used by the Air Quality map layer."""
    data = fetch_real_weather_data(lat, lon)
    if "aqi_error" in data and "aqi" not in data:
        return JSONResponse({"error": "Air quality data unavailable", "detail": data.get("aqi_error")}, status_code=503)
    return {
        "aqi":       data.get("aqi"),
        "aqi_label": data.get("aqi_label", "Unknown"),
        "pm2_5":     data.get("pm2_5", "N/A"),
        "pm10":      data.get("pm10", "N/A"),
        "no2":       data.get("no2", "N/A"),
        "o3":        data.get("o3", "N/A"),
        "co":        data.get("co", "N/A"),
        "city":      data.get("city", ""),
    }


def build_city_system_prompt(lat=None, lon=None) -> str:
    """Build live-data system prompt. If lat/lon given, fetches weather for that location."""
    # Support both direct run and uvicorn module run
    import sys, os as _os
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    try:
        from coordinator import city_status
        status = city_status()
    except Exception:
        status = {"level": "Unknown", "flood": "N/A", "traffic": "N/A",
                  "power": "N/A", "crowd": "N/A", "risk_score": 0,
                  "advice": "Unable to fetch agent data."}

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    weather_block = ""
    location_note = "No specific location pinned. Answer for whatever city the user asks about using your knowledge."

    if lat is not None and lon is not None:
        try:
            w = fetch_real_weather_data(lat, lon)
            if "weather_error" not in w and "error" not in w:
                city_name = f"{w.get('city','?')}, {w.get('country','')}"
                location_note = f"User has pinned location: {city_name} (Lat {lat}, Lon {lon})"
                weather_block = f"""
=== LIVE WEATHER FOR PINNED LOCATION: {city_name} ===
Temperature : {w.get('temperature','N/A')}°C  — {w.get('weather_desc','N/A')}
Humidity    : {w.get('humidity','N/A')}%   Wind: {w.get('wind_speed','N/A')} m/s
Rainfall    : {w.get('rain_1h',0)} mm (1h)  /  {w.get('rain_3h',0)} mm (3h)
Clouds      : {w.get('clouds','N/A')}%   Visibility: {w.get('visibility','N/A')} m
Air Quality : {w.get('aqi_label','N/A')} (AQI {w.get('aqi','N/A')}/5)
PM2.5       : {w.get('pm2_5','N/A')} µg/m³   PM10: {w.get('pm10','N/A')} µg/m³"""
        except Exception as ex:
            weather_block = f"Weather fetch error for ({lat},{lon}): {ex}"

    return f"""You are the Claude City Assistant for the Urban Resilience AI platform.
Timestamp: {now}
{location_note}

=== CITY AGENT DATA (Kochi base agents — always available) ===
Flood Agent   : {status.get('flood','N/A')}
Traffic Agent : {status.get('traffic','N/A')}
Power Agent   : {status.get('power','N/A')}
Crowd Agent   : {status.get('crowd','N/A')}
Risk Score    : {status.get('risk_score',0)}/12
Risk Level    : {status.get('level','N/A')}
Advice        : {status.get('advice','N/A')}
{weather_block}

STRICT RULES:
1. You have LIVE weather data above for the pinned location. Always use it — cite real values.
2. NEVER say you lack real-time data. For the pinned location you have live data.
3. For any city worldwide the user asks about — answer using your training knowledge + urban risk expertise.
4. Format with markdown: **bold**, bullet points, tables, headers.
5. For the pinned location always cite the actual temperature, rainfall, AQI values from above.
6. End every response with a clear action/recommendation."""


@app.post("/claude")
async def chat_with_claude(request: Request):
    data = await request.json()
    user_message = data.get("message", "").strip()
    history      = data.get("history", [])
    lat          = data.get("lat")
    lon          = data.get("lon")

    if not user_message:
        return JSONResponse({"error": "No message provided"}, status_code=400)

    messages = []
    for turn in history[-10:]:
        role    = turn.get("role", "user")
        content_text = turn.get("content", "")
        if role in ("user", "assistant") and content_text:
            messages.append({"role": role, "content": content_text})
    messages.append({"role": "user", "content": user_message})

    try:
        resp = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1400,
            system=build_city_system_prompt(lat=lat, lon=lon),
            messages=messages
        )
        return {"reply": resp.content[0].text}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)