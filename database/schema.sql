CREATE TABLE IF NOT EXISTS authorized_vehicles (
    vehicle_id VARCHAR(50) PRIMARY KEY,
    owner_name VARCHAR(100) NOT NULL,
    registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO authorized_vehicles (vehicle_id, owner_name, is_active)
VALUES ('EV-TESLA-99', 'Sanjit Kumar', TRUE)
ON CONFLICT (vehicle_id) DO NOTHING;
