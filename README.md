# Local Containerized EV Telemetry Backend Prototype

A local containerized backend prototype engineered to ingest, validate, and summarize high-frequency vehicle battery telematics metrics. The architecture uses a decoupled multi-service infrastructure topology running inside an isolated local network mesh.

## System Architecture & Deployment Blueprint

Use code with caution.
[ Python Client Simulator ] ──► (HTTP POST) ──► [ Node.js Ingestion Gateway (Port 3000) ]
│          │
(Synchronous Check) ──────────┘          └──────────┐
▼                                                   ▼
[ PostgreSQL 15 Database ]                         [ Python FastAPI Worker ]
│
▼
[ MongoDB 7.0 Storage ]

### Core Architecture Capabilities
* **Synchronous Error Propagation:** The ingestion server uses a synchronous proxy pattern to ensure that network write faults or component errors cascade back to the client immediately rather than providing false successes.
* **Isolated Processing Boundary:** Internal computing modules map no external port entries to the host, protecting them against direct network manipulation.
* **Database-Level Idempotency:** Implements UUID tracking rules handled by database unique key indexes to drop duplicate network transmissions safely.
* **Optimized Aggregation Operations:** Runs fleet calculations natively in MongoDB via aggregation engines across a 24-hour time window, preserving container memory footprint.

## Local Installation

```bash
git clone https://github.com
cd ev-telemetry-backend
docker-compose up --build
```

## Available Verification Endpoints
* **Historical Audit Tracking Route:** `http://localhost:3000/api/telemetry/history?limit=10`
* **Fleet Analytics Computation Dashboard:** `http://localhost:3000/api/telemetry/analytics`

## Identified System Limitations & Next Steps
1. **Device Authentication:** The system validates structural vehicle parameters against the PostgreSQL registry but lacks cryptographic token authentication (e.g., JWT or mTLS) for endpoints.
2. **Synchronous Database Operations:** PyMongo calls are handled synchronously within FastAPI handlers, which can introduce performance bottlenecks under sustained heavy workloads.
3. **Basic Network Retries:** The simulator loop uses a basic connection timeout pattern but does not implement an exponential back off retry mechanism.