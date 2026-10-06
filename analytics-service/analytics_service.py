from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime

app = FastAPI()

client = MongoClient("mongodb://mongo-db:27017/")
db = client["ev_analytics_db"]
collection = db["processed_telemetry"]

class ValidatedPayload(BaseModel):
    vehicle_id: str
    speed_kmh: float
    battery_percentage: float
    battery_temp_celsius: float

@app.post("/worker/process")
async def process_metrics(data: ValidatedPayload):
    log_doc = data.model_dump()
    log_doc["processed_at"] = datetime.utcnow()
    
    if data.battery_temp_celsius >= 45.0:
        log_doc["alert_level"] = "CRITICAL"
    else:
        log_doc["alert_level"] = "NOMINAL"
        
    collection.insert_one(log_doc)
    return {"status": "persisted", "alert": log_doc["alert_level"]}
