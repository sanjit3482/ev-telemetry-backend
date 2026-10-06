const express = require('express');
const { Pool } = require('pg');
const http = require('http');
const app = express();
app.use(express.json());

// Establish resilient PostgreSQL connection pooling
// SECURE PATTERN: Database credentials are read dynamically from env variables
const pgPool = new Pool({
    user: process.env.DB_USER || 'postgres_admin',
    host: process.env.DB_HOST || 'postgres-db',
    database: process.env.DB_NAME || 'ev_fleet_db',
    password: process.env.DB_PASSWORD, // Safely loaded from your hidden .env file
    port: parseInt(process.env.DB_PORT || '5432', 10),
    max: 10,
    idleTimeoutMillis: 30000
});


app.post('/api/telemetry', async (req, res) => {
    const { vehicle_id } = req.body;
    
    // 🚨 STATE TRACKER: Guarantees the gateway only responds exactly once to the client
    let isResponseSent = false;
    
    try {
        // 1. Verify vehicle access boundaries against your relational database registry
        const authCheck = await pgPool.query(
            'SELECT is_active FROM authorized_vehicles WHERE vehicle_id = $1', 
            [vehicle_id]
        );

        // ✅ FIXED INDEX CHECK: Safely drilling down into the array sequence row target
        if (authCheck.rows.length === 0 || !authCheck.rows[0].is_active) {
            isResponseSent = true;
            return res.status(401).json({ status: 'denied', message: 'Unauthorized Vehicle ID' });
        }

        const payloadString = JSON.stringify(req.body);
        
        // 2. Prepare structural options to securely proxy the payload inside the private network mesh
        const options = {
            host: 'analytics-processor',
            port: 8000,
            path: '/worker/process',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payloadString)
            },
            timeout: 5000 // 5-second hard safety execution threshold
        };

        const forwardRequest = http.request(options, (workerRes) => {
            let data = '';
            workerRes.on('data', (chunk) => { data += chunk; });
            workerRes.on('end', () => {
                // Safeguard against executing post-timeout responses
                if (isResponseSent) return;
                isResponseSent = true;

                // Safely propagate target 4xx error ranges if validation rules fail downstream
                if (workerRes.statusCode >= 400 && workerRes.statusCode < 500) {
                    return res.status(workerRes.statusCode).send(data);
                } else if (workerRes.statusCode === 200 || workerRes.statusCode === 201) {
                    return res.status(200).json({ status: 'success', message: 'Data saved successfully' });
                } else {
                    return res.status(502).json({ status: 'error', message: 'Downstream processing failure' });
                }
            });
        });

        // Handle network drops or offline service paths safely
        forwardRequest.on('error', (err) => {
            if (isResponseSent) return;
            isResponseSent = true;
            console.error('❌ Downstream connection error caught:', err.message);
            return res.status(503).json({ status: 'error', message: 'Downstream processing service unavailable' });
        });

        // Handle connection timeout intervals without dropping the server process
        forwardRequest.on('timeout', () => {
            if (isResponseSent) return;
            isResponseSent = true;
            forwardRequest.destroy(); // Sever the lagged socket pipe cleanly
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


// Proxy Route to securely query vehicle telemetry history logs
app.get('/api/telemetry/history', (req, res) => {
    const limit = req.query.limit || 10;
    http.get(`http://analytics-processor:8000/api/telemetry/history?limit=${limit}`, (workerRes) => {
        let data = '';
        workerRes.on('data', (chunk) => { data += chunk; });
        workerRes.on('end', () => {
            res.status(workerRes.statusCode).send(JSON.parse(data));
        });
    }).on('error', (err) => {
        res.status(502).json({ error: 'Failed to communicate with secure analytics node' });
    });
});

// Proxy Route to securely fetch compiled aggregations dashboard
app.get('/api/telemetry/analytics', (req, res) => {
    http.get('http://analytics-processor:8000/api/telemetry/analytics', (workerRes) => {
        let data = '';
        workerRes.on('data', (chunk) => { data += chunk; });
        workerRes.on('end', () => {
            res.status(workerRes.statusCode).send(JSON.parse(data));
        });
    }).on('error', (err) => {
        res.status(502).json({ error: 'Failed to compile real-time fleet analytics aggregates' });
    });
});


app.listen(3000, () => console.log('Secure Node Ingestion Server live on port 3000'));
