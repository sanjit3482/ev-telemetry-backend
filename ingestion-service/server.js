const express = require('express');
const { Pool } = require('pg');
const http = require('http');
const app = express();
app.use(express.json());

// Establish resilient PostgreSQL connection pooling
const pgPool = new Pool({
    host: 'postgres-db',
    port: 5432,
    user: 'postgres_admin',
    password: 'secure_password_2026',
    database: 'ev_fleet_db',
    max: 10, // Max clients in pool
    idleTimeoutMillis: 30000
});

app.post('/api/telemetry', async (req, res) => {
    const { vehicle_id } = req.body;
    
    try {
        // 1. Audit boundary-layer access rights via PostgreSQL
        const authCheck = await pgPool.query(
            'SELECT is_active FROM authorized_vehicles WHERE vehicle_id = \$1', 
            [vehicle_id]
        );

        if (authCheck.rows.length === 0 || !authCheck.rows[0].is_active) {
            return res.status(401).json({ status: 'denied', message: 'Unauthorized Vehicle ID detected' });
        }

        // 2. Forward payload downstream and WAIT for processing confirmation
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
            timeout: 5000 // 5-second hard safety timeout threshold
        };

        const forwardRequest = http.request(options, (workerRes) => {
            let data = '';
            workerRes.on('data', (chunk) => { data += chunk; });
            workerRes.on('end', () => {
                if (workerRes.statusCode === 200 || workerRes.statusCode === 201) {
                    // Propagate verified transactional success back to client
                    return res.status(200).json({
                        status: 'success',
                        message: 'Data successfully processed and stored in NoSQL persistence layer'
                    });
                } else {
                    // Downstream reported a failure (e.g. database error) - do not fake success
                    return res.status(502).json({
                        status: 'error',
                        message: `Downstream processor rejected telemetry: Status ${workerRes.statusCode}`
                    });
                }
            });
        });

        forwardRequest.on('error', (err) => {
            console.error('Pipeline Cascade Error:', err.message);
            return res.status(503).json({ 
                status: 'error', 
                message: 'Downstream processing service unavailable' 
            });
        });

        forwardRequest.on('timeout', () => {
            forwardRequest.destroy();
            return res.status(504).json({ 
                status: 'error', 
                message: 'Downstream processing timed out' 
            });
        });

        forwardRequest.write(payloadString);
        forwardRequest.end();

    } catch (err) {
        console.error('Gateway internal error:', err);
        return res.status(500).json({ error: 'Internal gateway pipeline processing failure' });
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
