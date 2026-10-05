import time
import random
from datetime import datetime
from pymongo import MongoClient
import certifi

MONGO_URL = "mongodb+srv://awesomesanjit0403_db_user:sanjit123@cluster0.x8r88zh.mongodb.net/?appName=Cluster0"


try:
    client = MongoClient(MONGO_URL, tlsCAFile=certifi.where())
    db = client["ev_telemetry_db"]
    collection = db["telemetry_logs"]
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"Connection failed: {e}")
    exit()

vehicle_id = "EV-TESLA-99"
battery_pct = 100.0  # Start fully charged

print(f"Starting live telemetry simulation for vehicle: {vehicle_id}...")

while battery_pct > 0:
    speed = random.randint(40, 80)          # Random speed between 40-80 km/h
    temperature = random.randint(30, 50)    # Random battery temp in Celsius
    battery_pct -= random.uniform(0.1, 0.5) # Battery drops slowly
    
    # Bundle the data packet into JSON format
    data_packet = {
        "vehicle_id": vehicle_id,
        "timestamp": datetime.utcnow(),
        "speed_kmh": round(speed, 2),
        "battery_percentage": round(max(battery_pct, 0), 2),
        "battery_temp_celsius": temperature
    }
    
    # Save the log directly to your MongoDB Cloud database
    try:
        collection.insert_one(data_packet)
        print(f"📡 Transmitted Log -> Battery: {data_packet['battery_percentage']}% | Speed: {speed}km/h | Temp: {temperature}°C")
    except Exception as err:
        print(f"Failed to send log: {err}")
    
    # Wait 3 seconds before sending the next telemetry packet
    time.sleep(3)
