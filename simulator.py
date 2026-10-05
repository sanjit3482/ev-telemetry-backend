import time
import random
import requests

# Pointing to your local FastAPI gateway server endpoint
API_URL = "http://localhost:8000/api/telemetry"


vehicle_id = "EV-TESLA-99"
battery_pct = 100.0  # Start fully charged

print(f"Launching API-Routed Telemetry System for: {vehicle_id}...")

while battery_pct > 0:
    speed = random.randint(40, 80)          # Random speed between 40-80 km/h
    temperature = random.randint(30, 50)    # Random battery temp in Celsius
    battery_pct -= random.uniform(0.5, 1.2) # Burn battery slightly quicker for testing updates
    
    # Bundle data into a dictionary structure matching our FastAPI Pydantic rules
    payload = {
        "vehicle_id": vehicle_id,
        "speed_kmh": round(speed, 2),
        "battery_percentage": round(max(battery_pct, 0), 2),
        "battery_temp_celsius": float(temperature)
    }
    
    try:
        # Send an HTTP POST request over the network to your FastAPI Server
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            print(f"Gateway Handshake Verified! -> Status: {response.json()['status']} | Saved ID: {response.json()['inserted_id'][:8]}...")
        else:
            print(f"Gateway rejected data packet: Status {response.status_code}")
            
    except Exception as err:
        print(f"Could not connect to API Gateway Server: {err}")
    
    # Wait 3 seconds before sending the next telemetry packet
    time.sleep(3)
