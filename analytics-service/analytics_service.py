from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymongo import MongoClient, errors
from datetime import datetime, timedelta

app = FastAPI(title="EV Telemetry Processing & Analytics API")

client = MongoClient("mongodb://mongo-db:27017/", maxPoolSize=50, waitQueueTimeoutMS=5000)
db = client["ev_analytics_db"]
collection = db["processed_telemetry"]

# 🚨 ENFORCE IDEMPOTENCY: Create a unique database index constraint on startup
# This acts as an iron shield preventing identical duplicate events from writing twice
collection.create_index("event_id", unique=True)

class ValidatedPayload(BaseModel):
    event_id: str = Field(..., min_length=36, max_length=36) # Rigid UUID character validation
    vehicle_id: str = Field(..., min_length=3, max_length=50)
    speed_kmh: float = Field(..., ge=0.0, le=300.0)
    battery_percentage: float = Field(..., ge=0.0, le=100.0)
    battery_temp_celsius: float = Field(..., ge=-40.0, le=150.0)

@app.post("/worker/process")
async def process_metrics(data: ValidatedPayload):
    try:
        log_doc = data.model_dump()
        log_doc["processed_at"] = datetime.utcnow()
        
        if data.battery_temp_celsius >= 45.0:
            log_doc["alert_level"] = "CRITICAL"
        else:
            log_doc["alert_level"] = "NOMINAL"
            
        collection.insert_one(log_doc)
        return {"status": "persisted", "alert": log_doc["alert_level"]}
        
    except errors.DuplicateKeyError:
        # Catch duplicate retries gracefully at the database constraint boundary
        # Return a 200/201 equivalent because the data is already safe in our storage vault
        return {"status": "ignored", "message": "Duplicate event payload detected and dropped safely."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database write failure: {str(e)}")

@app.get("/api/telemetry/history")
async def get_vehicle_history(limit: int = 10):
    try:
        safety_limit = min(max(limit, 1), 100)
        logs = list(collection.find({}, {"_id": 0}).sort("processed_at", -1).limit(safety_limit))
        return {"total_records_returned": len(logs), "history": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/telemetry/analytics")
async def get_fleet_analytics():
    try:
        time_boundary = datetime.utcnow() - timedelta(hours=24)
        
        pipeline = [
            {"$match": {"processed_at": {"$gte": time_boundary}}},
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
