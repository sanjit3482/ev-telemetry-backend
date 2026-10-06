markdown
# Distributed Real-Time EV Telemetry Microservice Ingestion Mesh

A highly performant, containerized, and decoupled backend data infrastructure pipeline engineered to ingest, validate, and compute real-time analytical metrics from streaming high-frequency Electric Vehicle (EV) sensor networks. Built using an enterprise microservices topology running five synchronized application and database containers within an isolated local network mesh.

## System Architecture & Data Flow Mesh

Use code with caution.
[ Container 1: Isolated Client Simulator Loop ]
│
▼ (HTTP POST + Unique UUID Event Tracking)
[ Container 2: Node.js/Express Ingestion Gateway ]
│
┌────────────────┴────────────────┐
▼ (Synchronous SQL Verification)  ▼ (Synchronous Network Proxy)
[ Container 3: PostgreSQL DB ]    [ Container 4: Python/FastAPI Rules Engine ]
│
▼ (Low-Memory Aggregation Engine)
[ Container 5: MongoDB LTS Storage ]

1. **Client Emulation Layer (`simulator/`):** An isolated Python loop programmatically mimicking an active vehicle computer, broadcasting sensor readings paired with a unique tracking UUID (`event_id`) every 2 seconds.
2. **Boundary Gatekeeper Layer (`ingestion-service/`):** A high-throughput Node.js Express server that intercepts inbound requests, verifies vehicle registration access tokens against relational database states, and synchronizes downstream execution streams using strict 5-second connection timeout limits.
3. **Relational Auditing DB (`database/`):** A PostgreSQL node maintaining active authorized vehicle registries to enforce identity validation at the system network perimeter.
4. **Analytical Rules Processing Layer (`analytics-service/`):** A Python FastAPI engine executing real-time thermal threshold rules (≥ 45.0°C ceiling) to catch battery over-heating risks, dynamically logging metadata tags before persistence.
5. **NoSQL Persistence Tier:** A production-supported MongoDB 7.0 document cluster logging structural telemetry payloads securely.

## Production-Grade System Optimization Features

* **Complete Fault-Cascading Error Propagation:** Eliminated false boundary acknowledgments by transforming the edge gateway into a synchronous proxy engine. Telemetry tracking status returns a `200 Success` only when the underlying NoSQL storage layer explicitly verifies a successful data save.
* **Network Perimeter Isolation:** Stripped public ports entirely from internal computation modules. The analytical service is unreachable by external network hosts, routing query paths securely through an API Gateway Proxy structural interface.
* **Transactional Idempotency Protection:** Enforced strict protection against duplicate network retry bursts. Telemetry streams generate a unique UUID per distinct physical sample reading, which is monitored by a `Unique Index Constraint` right inside MongoDB to reject duplicate writes at the data boundary without data corruption.
* **Out-Of-Memory (OOM) Protection Matrix:** Optimized data summarization endpoints by entirely eliminating the load of massive document sets into application RAM. Calculated analytics are calculated natively within MongoDB using high-performance **Aggregation Pipelines** over a bounded 24-hour time window.

## Unified System Component Topology

* **Edge Transport Layer:** Node.js 20 (LTS Alpine Runtime Environment), Express Engine
* **Computational Processing:** Python 3.10-slim, FastAPI Framework, Pydantic Schema Auditing
* **Relational Storage Boundary:** PostgreSQL 15-Alpine Database Engine
* **High-Velocity Document Vault:** MongoDB 7.0 (Production Long-Term Support Release)
* **Mesh Orchestration Infrastructure:** Docker, Docker Compose (Isolated Internal Networks)

## One-Command Local Grid Orchestration

1. **Ensure Docker Desktop is open and active in the background.**
2. **Clone and enter the optimized mesh infrastructure folder:**
   ```bash
   git clone https://github.com
   cd ev-telemetry-backend
   ```
3. **Boot up the entire multi-service microservices stack automatically:**
   ```bash
   docker-compose up --build
   ```

## Live Metrics & Verification Interfaces

With the Docker container cluster running in your environment, open your standard host browser window to access these secure gateway API proxy lookup routes:

* **Query Latest Chronological History:** `http://localhost:3000/api/telemetry/history?limit=10`
* **Fetch Bounded System Fleet Analytics:** `http://localhost:3000/api