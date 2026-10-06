const express = require('express');
const { Pool } = require('pg');
// Import the HTTP module so Node can talk to our Python service container
const http = require('http'); 
const app = express();
app.use(express.json());

const pgPool = new Pool({
    host: 'postgres-db',
    port: 5432,
    user: 'postgres_admin',
    password: 'secure_password_2026',
    database: 'ev_fleet_db'
});

app.post('/api/telemetry', async (req, res) => {
    const { vehicle_id, speed_kmh, battery_percentage, battery_temp_celsius } = req.body;
    
    try {
        // 1. Audit safety credentials via PostgreSQL relational database
        const authCheck = await pgPool.query(
            'SELECT is_active FROM authorized_vehicles WHERE vehicle_id = $1', 
            [vehicle_id]
        );

        if (authCheck.rows.length === 0 || !authCheck.rows[0].is_active) {
            return res.status(401).json({ status: 'denied', message: 'Unauthorized Vehicle ID detected' });
        }

        // 2. FORWARD VALID DATA PACKET DOWNSTREAM TO PYTHON WORKER PROCESSOR
        const payloadString = JSON.stringify(req.body);
        
        const options = {
            host: 'analytics-processor', // Targets the Python container service domain
            port: 8000,
            path: '/worker/process',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payloadString)
            }
        };

        const workerReq = http.request(options, (workerRes) => {
            let data = '';
            workerRes.on('data', (chunk) => { data += chunk; });
            workerRes.on('end', () => {
                // Respond to the simulator once the backend ecosystem has logged it
                res.status(202).json({ 
                    status: 'accepted', 
                    message: 'Vehicle verified, packet processed and stored successfully' 
                });
            });
        });

        workerReq.on('error', (err) => {
            console.error('Worker pipeline connection error:', err.message);
            res.status(500).json({ error: 'Data pipeline processing failed downstream' });
        });

        workerReq.write(payloadString);
        workerReq.end();

    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Internal gateway pipeline processing failure' });
    }
});

app.listen(3000, () => console.log('🚀 Node Ingestion Server live on port 3000'));
