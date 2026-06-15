from agents.flood_agent import flood_status
from agents.traffic_agent import traffic_status
from agents.power_agent import power_status

def city_status():
    flood = flood_status()
    traffic = traffic_status()
    power = power_status()

    risk_score = 0

    if "HIGH" in flood:
        risk_score += 4
    if "SEVERE" in traffic:
        risk_score += 3
    if "OUTAGE" in power:
        risk_score += 5

    # Decision Engine
    if risk_score >= 7:
        level = "🚨 CRITICAL"
        advice = "Avoid travel. Emergency services recommended."
    elif risk_score >= 4:
        level = "⚠️ WARNING"
        advice = "Be cautious. Some city services affected."
    else:
        level = "✅ NORMAL"
        advice = "City operating normally."

    return {
        "level": level,
        "advice": advice,
        "flood": flood,
        "traffic": traffic,
        "power": power,
        "crowd": "N/A",   # coordinator doesn't have a crowd agent yet
        "risk_score": risk_score
    }