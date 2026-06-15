from agents.flood_agent import flood_status
from agents.traffic_agent import traffic_status
from agents.power_agent import power_status
from agents.event_agent import crowd_status

def city_status():

    flood = flood_status()
    traffic = traffic_status()
    power = power_status()
    crowd = crowd_status()

    risk_score = 0

    if "High" in flood:
        risk_score += 4
    if "Heavy" in traffic or "Severe" in traffic:
        risk_score += 3
    if "Outage" in power:
        risk_score += 5
    if "Surge" in crowd:
        risk_score += 2

    # Decision Engine
    if risk_score >= 7:
        level = "🚨 CRITICAL"
        advice = "Avoid travel. Stay indoors. Emergency services advised."
    elif risk_score >= 4:
        level = "⚠️ WARNING"
        advice = "Be cautious. Some services affected."
    else:
        level = "✅ NORMAL"
        advice = "City operating normally."

    report = f"""
========= URBAN RESILIENCE REPORT =========

Risk Level: {level}

Flood Status: {flood}
Traffic Status: {traffic}
Power Status: {power}
Crowd Status: {crowd}

City Guidance:
{advice}

===========================================
"""

    return report
