from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymongo import MongoClient
from datetime import datetime, timedelta

app = FastAPI(title="EV Telemetry Processing & Analytics API")

# Resilient internal MongoDB client pooling
client = MongoClient("mongodb://mongo-db:27017/", maxPoolSize=50, waitQueueTimeoutMS=5000)
db = client["ev_analytics_db"]
collection = db["processed_telemetry"]

class ValidatedPayload(BaseModel):
    vehicle_id: str = Field(..., min_length=3, max_length=50)
    speed_kmh: float = Field(..., ge=0.0, le=300.0)
    battery_percentage: float = Field(..., ge=0.0, le=100.0)
    battery_temp_celsius: float = Field(..., ge=-40.0, le=150.0)

# POST API: Receives and processes streaming car data from Gateway
@app.post("/worker/process")
async def process_metrics(data: ValidatedPayload):
    try:
        log_doc = data.model_dump()
        log_doc["processed_at"] = datetime.utcnow()
        
        # Enforce explicit thermal threat rules (>= 45.0°C Safety Ceiling)
        if data.battery_temp_celsius >= 45.0:
            log_doc["alert_level"] = "CRITICAL"
        else:
            log_doc["alert_level"] = "NOMINAL"
            
        collection.insert_one(log_doc)
        return {"status": "persisted", "alert": log_doc["alert_level"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database write failure: {str(e)}")

# GET API: Historical Data Query Route (Bounded and Paged)
@app.get("/api/telemetry/history")
async def get_vehicle_history(limit: int = 10):
    try:
        # Enforce maximum safety bounds on limit parameters
        safety_limit = min(max(limit, 1), 100)
        logs = list(collection.find({}, {"_id": 0}).sort("processed_at", -1).limit(safety_limit))
        return {"total_records_returned": len(logs), "history": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET API: Low-Memory Aggregation Pipeline Route (Amazon-Scale Optimization)
@app.get("/api/telemetry/analytics")
async def get_fleet_analytics():
    try:
        # Step 1: Bounded Time Window - Look back at data from the past 24 hours
        time_boundary = datetime.utcnow() - timedelta(hours=24)
        
        # Step 2: Native MongoDB Aggregation Pipeline Engine execution
        pipeline = [
            {
                "$match": {
                    "processed_at": {"$gte": time_boundary}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_packets": {"$sum": 1},
                    "avg_speed": {"$avg": "$speed_kmh"},
                    "max_temp": {"$max": "$battery_temp_celsius"},
                    "critical_alerts": {
                        "$sum": {
                            "$cond": [{"$eq": ["$alert_level", "CRITICAL"]}, 1, 0]
                        }
                    }
                }
            }
        ]
        
        aggregation_result = list(collection.aggregate(pipeline))
        
        if not aggregation_result:
            return {"message": "No telemetry data collected in the past 24 hours."}
            
        summary = aggregation_result[0]
        
        return {
            "fleet_metrics_summary": {
                "total_telemetry_packets_processed_24h": summary["total_packets"],
                "average_fleet_speed_kmh": round(summary["avg_speed"], 2),
                "maximum_recorded_battery_temp_celsius": round(summary["max_temp"], 2),
                "total_critical_thermal_alerts_triggered": summary["critical_alerts"]
            },
            "system_health": "OPTIMAL" if summary["critical_alerts"] == 0 else "WARNING_THERMAL_THREATS_PRESENT"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aggregation pipeline failure: {str(e)}")
