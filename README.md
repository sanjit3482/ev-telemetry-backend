# Real-Time EV Telemetry Ingestion Pipeline

A high-performance, decoupled backend data pipeline designed to ingest, validate, and monitor streaming data packets from Electric Vehicle (EV) internal sensors. Built using a microservices-inspired architecture with **Python**, **FastAPI**, and **MongoDB Atlas**.

## System Architecture & Data Flow

[ Mock EV Client ]
│  (High-Frequency Simulated Telemetry Packets)
▼
[ HTTP POST Request ] ──► [ FastAPI Ingestion Gateway Server ]
│
├─► [ Pydantic Data Validation ]
├─► [ Real-Time Alert Engine ]
│
▼
[ MongoDB Atlas (Cloud) ]


1. **The Client (`simulator.py`):** Programmatically simulates an onboard vehicle computer broadcasting metrics (Speed, State of Charge, Thermal readings) every 3 seconds.
2. **The Gateway (`main.py`):** A secure FastAPI server that handles data validation and applies operational business logic rules.
3. **The Database:** A remote cloud cluster logging time-stamped historical time-series logs.

## Core Technical Features

* **Decoupled Architecture:** Eliminates dangerous client-to-database connections by routing all sensor tracking traffic through a secure intermediate API gateway layer.
* **Strict Type Enforcement:** Leverages Pydantic schemas to dynamically audit and validate inbound JSON payload structures, dropping malformed payloads before they affect the storage tier.
* **Real-Time Threat Detection:** Built-in threshold rule evaluation instantly monitors thermal readings, tagging records with a `CRITICAL_ALERT` operational flag if battery temps cross a 45°C safety ceiling.
* **Cloud Persistence:** Seamless integration with MongoDB Atlas cluster databases, injecting automated server-side internal processing timestamps for audit tracing.

## Tech Stack & Key Vocab

* **Language:** Python 3
* **Framework:** FastAPI, Uvicorn
* **Database:** MongoDB Cloud (Atlas Platform), PyMongo
* **Validation:** Pydantic Models
* **Network Protocol:** REST Architecture (HTTP POST / GET Methods)

## Local Installation & Execution

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd ev-telemetry-backend
   ```

2. **Install core dependencies:**
   ```bash
   pip3 install fastapi uvicorn pymongo certifi requests
   ```

3. **Boot up the Ingestion API Gatekeeper Server:**
   ```bash
   python3 -m uvicorn main:app --reload
   ```

4. **Launch the Real-Time Vehicle Simulator Loop (In a separate terminal tab):**
   ```bash
   python3 simulator.py
   ```

