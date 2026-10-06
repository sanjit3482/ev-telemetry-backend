const express = require('express');
const { Pool } = require('pg');
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
        const authCheck = await pgPool.query(
            'SELECT is_active FROM authorized_vehicles WHERE vehicle_id = $1', 
            [vehicle_id]
        );
        if (authCheck.rows.length === 0 || !authCheck.rows[0].is_active) {
            return res.status(401).json({ status: 'denied', message: 'Unauthorized Vehicle ID detected' });
        }
        res.status(202).json({ status: 'accepted', message: 'Vehicle verified, packet queued' });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Internal gateway pipeline processing failure' });
    }
});

app.listen(3000, () => console.log('🚀 Node Ingestion Server live on port 3000'));
