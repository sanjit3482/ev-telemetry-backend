from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime

app = FastAPI(title="EV Telemetry Processing & Analytics API")

# Connects to the companion MongoDB container running inside the same network mesh
client = MongoClient("mongodb://mongo-db:27017/")
db = client["ev_analytics_db"]
collection = db["processed_telemetry"]

class ValidatedPayload(BaseModel):
    vehicle_id: str
    speed_kmh: float
    battery_percentage: float
    battery_temp_celsius: float

# POST API: Receives and processes streaming car data
@app.post("/worker/process")
async def process_metrics(data: ValidatedPayload):
    log_doc = data.model_dump()
    log_doc["processed_at"] = datetime.utcnow()
    
    # Evaluate threshold rules in real-time
    if data.battery_temp_celsius >= 45.0:
        log_doc["alert_level"] = "CRITICAL"
    else:
        log_doc["alert_level"] = "NOMINAL"
        
    collection.insert_one(log_doc)
    return {"status": "persisted", "alert": log_doc["alert_level"]}

# GET API: Historical Data Query Route
@app.get("/api/telemetry/history")
async def get_vehicle_history(limit: int = 10):
    # Fetch the latest logs sorted by most recent arrival time
    logs = list(collection.find({}, {"_id": 0}).sort("processed_at", -1).limit(limit))
    return {"total_records_returned": len(logs), "history": logs}

# GET API: Real-Time Fleet Analytics Calculations Route
@app.get("/api/telemetry/analytics")
async def get_fleet_analytics():
    # Fetch all records to compile rapid aggregations
    all_docs = list(collection.find({}, {"_id": 0}))
    
    if not all_docs:
        return {"message": "No telemetry data collected yet."}
        
    # Extract structural calculation arrays
    speeds = [doc["speed_kmh"] for doc in all_docs]
    temps = [doc["battery_temp_celsius"] for doc in all_docs]
    critical_alerts = sum(1 for doc in all_docs if doc.get("alert_level") == "CRITICAL")
    
    return {
        "fleet_metrics_summary": {
            "total_telemetry_packets_processed": len(all_docs),
            "average_fleet_speed_kmh": round(sum(speeds) / len(speeds), 2),
            "maximum_recorded_battery_temp_celsius": max(temps),
            "total_critical_thermal_alerts_triggered": critical_alerts
        },
        "system_health": "OPTIMAL" if critical_alerts == 0 else "WARNING_THERMAL_THREATS_PRESENT"
    }
