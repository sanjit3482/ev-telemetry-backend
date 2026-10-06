import time
import random
import requests

INGESTION_URL = "http://ingestion-gateway:3000/api/telemetry"

print("🚀 Containerized BMS Simulator Loop Active...")

while True:
    payload = {
        "vehicle_id": "EV-TESLA-99",
        "speed_kmh": round(random.uniform(30, 90), 2),
        "battery_percentage": 88.4,
        "battery_temp_celsius": round(random.uniform(35, 50), 2)
    }
    try:
        res = requests.post(INGESTION_URL, json=payload)
        print(f"📡 Transmitted -> Ingestion Status Response: {res.status_code} | {res.json()['status']}")
    except Exception as e:
        print(f"❌ Network channel busy: {e}")
    time.sleep(2)
