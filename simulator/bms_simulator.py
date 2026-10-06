import time
import random
import requests
import uuid

INGESTION_URL = "http://ingestion-gateway:3000/api/telemetry"

print("🚀 Containerized BMS Simulator Loop Active with Idempotency Tracing...")

while True:
    # Generate a unique tracking ID once per distinct physical sample reading
    unique_event_id = str(uuid.uuid4())
    
    payload = {
        "event_id": unique_event_id,
        "vehicle_id": "EV-TESLA-99",
        "speed_kmh": round(random.uniform(30, 90), 2),
        "battery_percentage": 88.4,
        "battery_temp_celsius": round(random.uniform(35, 50), 2)
    }
    
    try:
        res = requests.post(INGESTION_URL, json=payload)
        print(f"📡 Transmitted ID: {unique_event_id[:8]}... | Gateway Response: {res.status_code}")
    except Exception as e:
        print(f"❌ Network channel busy: {e}")
        
    time.sleep(2)
