const express = require('express');
const http = require('http');
const { Pool } = require('pg');

const app = express();
app.use(express.json());

// Establish resilient PostgreSQL connection pooling using environment configuration matrices
const pgPool = new Pool({
    user: process.env.DB_USER || 'postgres_admin',
    host: process.env.DB_HOST || 'postgres-db',
    database: process.env.DB_NAME || 'ev_fleet_db',
    password: process.env.DB_PASSWORD, 
    port: parseInt(process.env.DB_PORT || '5432', 10),
    max: 10,
    idleTimeoutMillis: 30000
});

// 1. Post Route: Synchronous Proxy for Fleet Payload Telemetry Ingestion
app.post('/api/telemetry', async (req, res) => {
    const { vehicle_id } = req.body;
    let isResponseSent = false;
    
    try {
        const authCheck = await pgPool.query(
            'SELECT is_active FROM authorized_vehicles WHERE vehicle_id = \$1', 
            [vehicle_id]
        );

        if (authCheck.rows.length === 0 || !authCheck.rows[0].is_active) {
            isResponseSent = true;
            return res.status(401).json({ status: 'denied', message: 'Unauthorized Vehicle ID' });
        }

        const payloadString = JSON.stringify(req.body);
        
        const options = {
            host: 'analytics-processor',
            port: 8000,
            path: '/worker/process',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payloadString)
            },
            timeout: 5000 
        };

        const forwardRequest = http.request(options, (workerRes) => {
            let data = '';
            workerRes.on('data', (chunk) => { data += chunk; });
            workerRes.on('end', () => {
                if (isResponseSent) return;
                isResponseSent = true;

                if (workerRes.statusCode >= 400 && workerRes.statusCode < 500) {
                    return res.status(workerRes.statusCode).send(data);
                } else if (workerRes.statusCode === 200 || workerRes.statusCode === 201) {
                    return res.status(200).json({ status: 'success', message: 'Data saved successfully' });
                } else {
                    return res.status(502).json({ status: 'error', message: 'Downstream processing failure' });
                }
            });
        });

        forwardRequest.on('error', (err) => {
            if (isResponseSent) return;
            isResponseSent = true;
            console.error('Downstream connection error caught:', err.message);
            return res.status(503).json({ status: 'error', message: 'Downstream processing service unavailable' });
        });

        forwardRequest.on('timeout', () => {
            if (isResponseSent) return;
            isResponseSent = true;
            forwardRequest.destroy(); 
            console.error('⏳ Gateway downstream request timeout triggered');
            return res.status(504).json({ status: 'error', message: 'Downstream processing timed out' });
        });

        forwardRequest.write(payloadString);
        forwardRequest.end();

    } catch (err) {
        console.error('Gateway internal pipeline error:', err);
        if (!isResponseSent) {
            res.status(500).json({ error: 'Internal gateway pipeline processing failure' });
        }
    }
});

// 2. Get Route: Secure Proxy to query historical telemetry document records
app.get('/api/telemetry/history', (req, res) => {
    const limit = req.query.limit || 10;
    let isResFinished = false;

    const proxyReq = http.get(`http://analytics-processor:8000/api/telemetry/history?limit=${limit}`, (workerRes) => {
        let data = '';
        workerRes.on('data', (chunk) => { data += chunk; });
        workerRes.on('end', () => {
            if (isResFinished) return;
            isResFinished = true;

            try {
                const parsedBody = JSON.parse(data);
                return res.status(workerRes.statusCode).json(parsedBody);
            } catch (parseError) {
                console.error("Invalid JSON signature received on history track");
                return res.status(502).json({ error: 'Bad Gateway: Invalid structural response format received from downstream analytics node' });
            }
        });
    });

    proxyReq.setTimeout(4000, () => {
        if (isResFinished) return;
        isResFinished = true;
        proxyReq.destroy();
        return res.status(504).json({ error: 'Gateway Timeout: Analytics pipeline failed to respond within limits' });
    });

    proxyReq.on('error', (err) => {
        if (isResFinished) return;
        isResFinished = true;
        return res.status(502).json({ error: 'Failed to communicate with secure analytics node' });
    });
});

// 3. Get Route: Secure Proxy to compile fleet mathematical aggregates dashboards
app.get('/api/telemetry/analytics', (req, res) => {
    let isResFinished = false;

    const proxyReq = http.get('http://analytics-processor:8000/api/telemetry/analytics', (workerRes) => {
        let data = '';
        workerRes.on('data', (chunk) => { data += chunk; });
        workerRes.on('end', () => {
            if (isResFinished) return;
            isResFinished = true;

            try {
                const parsedBody = JSON.parse(data);
                return res.status(workerRes.statusCode).json(parsedBody);
            } catch (parseError) {
                console.error("Invalid JSON signature received on analytics track");
                return res.status(502).json({ error: 'Bad Gateway: Invalid structural data payload from database engine' });
            }
        });
    });

    proxyReq.setTimeout(4000, () => {
        if (isResFinished) return;
        isResFinished = true;
        proxyReq.destroy();
        return res.status(504).json({ error: 'Gateway Timeout: Fleet analytics compilation timed out' });
    });

    proxyReq.on('error', (err) => {
        if (isResFinished) return;
        isResFinished = true;
        return res.status(502).json({ error: 'Failed to compile real-time fleet analytics aggregates' });
    });
});

// Start the network listening bridge
const PORT = 3000;
app.listen(PORT, () => {
    console.log(`📡 Node.js Ingestion Service live on port ${PORT}`);
});
