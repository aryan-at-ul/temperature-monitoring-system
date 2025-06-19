-- =============================================================================
-- Temperature Monitoring System - Database Initialization Script
-- =============================================================================
-- This script will:
-- 1. Create a dedicated user and database.
-- 2. Define the schema for all tables, including relationships.
-- 3. Set up automated monthly partitioning for temperature readings.
-- 4. Create helpful views for data analysis.
-- 5. Grant appropriate permissions to the application user.
-- 6. Seed the database with essential starting data.
-- =============================================================================

-- ==> IMPORTANT: Run the following section as a superuser (e.g., 'postgres')
-- You might need to connect to the default 'postgres' database to run this part.

-- -- 1. User and Database Creation --
-- CREATE ROLE tm_user WITH LOGIN PASSWORD 'a_strong_password_here';
-- CREATE DATABASE temperature_db WITH OWNER tm_user;
-- COMMENT ON DATABASE temperature_db IS 'Database for the Temperature Monitoring System';

-- ==> IMPORTANT: Now, connect to the 'temperature_db' as the 'postgres' user
-- to run the rest of this script. (\c temperature_db)

BEGIN;

-- -- 2. Extensions --
-- Enable UUID generation functions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -- 3. Schema Definition --

-- Table: system_config (Key-value store for application settings)
CREATE TABLE IF NOT EXISTS public.system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB,
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.system_config IS 'Stores global configuration for the application.';

-- Table: customers
CREATE TABLE IF NOT EXISTS public.customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_code VARCHAR(16) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    data_sharing_method VARCHAR(16) NOT NULL,
    data_frequency_seconds INTEGER NOT NULL,
    data_source_url VARCHAR(2048),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.customers IS 'Stores information about each customer.';

-- Table: facilities
CREATE TABLE IF NOT EXISTS public.facilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES public.customers(id) ON DELETE CASCADE,
    facility_code VARCHAR(64),
    name VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.facilities IS 'Stores information about customer facilities or warehouses.';

-- Table: storage_units
CREATE TABLE IF NOT EXISTS public.storage_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    facility_id UUID NOT NULL REFERENCES public.facilities(id) ON DELETE CASCADE,
    unit_code VARCHAR(64),
    name VARCHAR(255),
    size_value NUMERIC,
    size_unit VARCHAR(16),
    set_temperature NUMERIC,
    temperature_unit VARCHAR(8),
    equipment_type VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.storage_units IS 'Represents individual temperature-controlled units within a facility.';

-- Table: customer_tokens (For API authentication)
CREATE TABLE IF NOT EXISTS public.customer_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES public.customers(id) ON DELETE CASCADE,
    token_hash VARCHAR(256) NOT NULL UNIQUE,
    token_name VARCHAR(255) NOT NULL,
    permissions JSONB,
    accessible_units JSONB,
    rate_limit_per_hour INTEGER,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.customer_tokens IS 'Stores API access tokens for customers.';

-- Table: ingestion_logs
CREATE TABLE IF NOT EXISTS public.ingestion_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES public.customers(id) ON DELETE SET NULL,
    ingestion_type VARCHAR(16) NOT NULL, -- 'api', 'csv'
    status VARCHAR(16) NOT NULL, -- 'success', 'failure', 'partial'
    records_processed INTEGER DEFAULT 0,
    records_succeeded INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    source_url VARCHAR(2048),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.ingestion_logs IS 'Logs each data ingestion attempt for traceability.';


-- -- 4. Partitioned Table for Time-Series Data --
-- This is the main "hot" table for recent data. It is partitioned by month.
CREATE TABLE IF NOT EXISTS public.temperature_readings (
    id BIGSERIAL NOT NULL,
    customer_id UUID NOT NULL,
    facility_id UUID NOT NULL,
    storage_unit_id UUID NOT NULL,
    temperature REAL NOT NULL,
    temperature_unit VARCHAR(8) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(255),
    quality_score REAL,
    equipment_status VARCHAR(64) DEFAULT 'normal',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Define the primary key to include the partition key for efficiency
    PRIMARY KEY (id, recorded_at)
) PARTITION BY RANGE (recorded_at);

COMMENT ON TABLE public.temperature_readings IS 'Parent table for storing all temperature readings. Partitioned by month.';

-- Automated Partition Creation Function
-- This function will automatically create a new monthly partition if one doesn't exist
-- when data is inserted. This is much more robust than manual partition creation.
CREATE OR REPLACE FUNCTION create_temperature_partition_if_not_exists()
RETURNS TRIGGER AS $$
DECLARE
    partition_date TEXT;
    partition_name TEXT;
BEGIN
    partition_date := to_char(NEW.recorded_at, 'YYYY_MM');
    partition_name := 'temperature_readings_history_' || partition_date;
    
    -- Check if the partition already exists
    IF NOT EXISTS(SELECT 1 FROM pg_tables WHERE tablename=partition_name) THEN
        -- Create the new partition
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF public.temperature_readings FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            date_trunc('month', NEW.recorded_at),
            date_trunc('month', NEW.recorded_at) + interval '1 month'
        );
        RAISE NOTICE 'Created partition %', partition_name;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to execute the function before an insert
DROP TRIGGER IF EXISTS insert_temperature_trigger ON public.temperature_readings;
CREATE TRIGGER insert_temperature_trigger
    BEFORE INSERT ON public.temperature_readings
    FOR EACH ROW EXECUTE FUNCTION create_temperature_partition_if_not_exists();

-- Create Indexes for performance
CREATE INDEX IF NOT EXISTS idx_temperature_readings_recorded_at ON public.temperature_readings (recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_temperature_readings_unit_id ON public.temperature_readings (storage_unit_id);


-- -- 5. Views --

-- View: latest_temperature_readings
-- Efficiently gets the most recent reading for every storage unit.
CREATE OR REPLACE VIEW public.latest_temperature_readings AS
SELECT DISTINCT ON (r.storage_unit_id)
    r.id,
    r.customer_id,
    r.facility_id,
    r.storage_unit_id,
    r.temperature,
    r.temperature_unit,
    r.recorded_at,
    r.sensor_id,
    r.quality_score
FROM public.temperature_readings r
ORDER BY r.storage_unit_id, r.recorded_at DESC;

-- View: customer_summary
-- Provides a high-level overview of each customer's assets.
CREATE OR REPLACE VIEW public.customer_summary AS
SELECT
    c.id AS customer_id,
    c.name AS customer_name,
    c.data_sharing_method,
    COUNT(DISTINCT f.id) AS facility_count,
    COUNT(DISTINCT u.id) AS unit_count
FROM public.customers c
LEFT JOIN public.facilities f ON c.id = f.customer_id
LEFT JOIN public.storage_units u ON f.id = u.facility_id
GROUP BY c.id, c.name, c.data_sharing_method;


-- -- 6. Permissions --
-- Grant all necessary privileges to the application user 'tm_user'
GRANT CONNECT ON DATABASE temperature_db TO tm_user;
GRANT USAGE ON SCHEMA public TO tm_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tm_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO tm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO tm_user;




-- Seed the system_config table with default values
INSERT INTO public.system_config (key, value, description) VALUES
('data_retention_days', '730', 'Number of days to retain hot temperature data before archiving.')
ON CONFLICT (key) DO NOTHING;

INSERT INTO public.system_config (key, value, description) VALUES
('max_temperature_deviation', '{"warning": 2, "critical": 5}', 'Temperature deviation thresholds in degrees Celsius.')
ON CONFLICT (key) DO NOTHING;

-- Seed the customers table with initial data, for assignemnt purposes
INSERT INTO public.customers (id, customer_code, name, data_sharing_method, data_frequency_seconds) VALUES
('9cd32f83-5dc5-4214-ac24-809889669cea', 'A', 'Customer A', 'api', 60),
('b5f0405b-a4dd-4894-b636-5ca059884e83', 'B', 'Customer B', 'csv', 300)
ON CONFLICT (id) DO NOTHING;

COMMIT;
