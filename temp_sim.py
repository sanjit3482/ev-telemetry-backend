import time
import random
import requests

API_URL = "http://localhost:8000/api/telemetry"
vehicle_id = "EV-TESLA-99"
battery_pct = 100.0

print(f"Launching API-Routed Telemetry System for: {vehicle_id}...")

while battery_pct > 0:
    speed = random.randint(40, 80)
    temperature = random.randint(30, 50)
    battery_pct -= random.uniform(0.5, 1.2)
    
    payload = {
        "vehicle_id": vehicle_id,
        "speed_kmh": round(speed, 2),
        "battery_percentage": round(max(battery_pct, 0), 2),
        "battery_temp_celsius": float(temperature)
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print(f"📡 Gateway Handshake Verified! -> Status: {response.json()['status']} | Saved ID: {response.json()['inserted_id'][:8]}...")
    except Exception as err:
        print(f"Error: {err}")
        
    time.sleep(3)
