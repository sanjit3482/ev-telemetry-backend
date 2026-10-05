from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import certifi
from datetime import datetime

# Initialize the API engine
app = FastAPI(title="EV Telemetry Ingestion API")

# Connect to your verified MongoDB Cluster
MONGO_URL = "mongodb+srv://awesomesanjit0403_db_user:sanjit123@cluster0.x8r88zh.mongodb.net/?appName=Cluster0"

try:
    client = MongoClient(MONGO_URL, tlsCAFile=certifi.where())
    db = client["ev_telemetry_db"]
    collection = db["telemetry_logs"]
    print("✅ Backend API Server successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"API Server Database connection failed: {e}")

# Data Validation Template: Defines the rules for incoming car data
class TelemetryData(BaseModel):
    vehicle_id: str
    speed_kmh: float
    battery_percentage: float
    battery_temp_celsius: float

# The Ingestion Route: This is the URL window the vehicle will talk to
@app.post("/api/telemetry")
async def receive_telemetry(data: TelemetryData):
    try:
        # Convert incoming packet to a readable database dictionary
        log_document = data.model_dump()
        
        # Inject an internal server timestamp to record precise arrival time
        log_document["timestamp"] = datetime.utcnow()
        
        # Save to database
        result = collection.insert_one(log_document)
        
        return {
            "status": "success",
            "message": "Telemetry packet processed and stored",
            "inserted_id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database write failure: {str(e)}")

# Baseline Health Route
@app.get("/")
def home():
    return {"status": "online", "system": "EV Telemetry Framework"}
