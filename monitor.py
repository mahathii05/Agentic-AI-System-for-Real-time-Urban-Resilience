import time
import json
import traceback
from coordinator import city_status

def monitor_city():
    print("Urban Resilience Monitoring Started...")

    while True:
        try:
            status = city_status()

            status["zones"] = [
                {"type": "flood",   "lat": 10.020, "lon": 76.340, "level": status["flood"]},
                {"type": "traffic", "lat": 10.000, "lon": 76.360, "level": status["traffic"]},
                {"type": "crowd",   "lat": 10.030, "lon": 76.320, "level": status["crowd"]},
                {"type": "power",   "lat": 10.015, "lon": 76.350, "level": status["power"]}
            ]

            print("\n===== CITY STATUS UPDATE =====")
            print(json.dumps(status, indent=2, ensure_ascii=False))

            with open("latest_alert.txt", "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print("Monitoring error:", e)
            traceback.print_exc()

        time.sleep(20)

if __name__ == "__main__":
    monitor_city()