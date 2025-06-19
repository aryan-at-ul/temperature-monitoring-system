-- -- database/schema.sql
-- -- Temperature Monitoring System Database Schema
-- -- Designed to handle diverse customer data with different units and null values

-- -- Extension for UUID generation
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -- ================================
-- -- CUSTOMER MANAGEMENT TABLES
-- -- ================================

-- -- Customers table
-- CREATE TABLE customers (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     customer_code VARCHAR(10) UNIQUE NOT NULL, -- 'A', 'B', etc.
--     name VARCHAR(255) NOT NULL,
--     data_sharing_method VARCHAR(20) NOT NULL CHECK (data_sharing_method IN ('csv', 'api', 'webhook')),
--     data_frequency_seconds INTEGER DEFAULT 300,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     is_active BOOLEAN DEFAULT TRUE
-- );

-- -- Facilities table  
-- CREATE TABLE facilities (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
--     facility_code VARCHAR(50) NOT NULL, -- For customer reference
--     name VARCHAR(255), -- Can be NULL
--     city VARCHAR(100), -- Can be NULL  
--     country VARCHAR(100) NOT NULL,
--     latitude DECIMAL(10, 8), -- For future geographic features
--     longitude DECIMAL(11, 8),
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     UNIQUE(customer_id, facility_code)
-- );

-- -- Storage units table
-- CREATE TABLE storage_units (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     facility_id UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
--     unit_code VARCHAR(50) NOT NULL, -- For customer reference
--     name VARCHAR(255), -- Can be NULL (like Customer A)
--     size_value DECIMAL(12, 2) NOT NULL,
--     size_unit VARCHAR(10) NOT NULL CHECK (size_unit IN ('sqm', 'sqft', 'm2', 'ft2')),
--     set_temperature DECIMAL(8, 2) NOT NULL,
--     temperature_unit VARCHAR(5) NOT NULL CHECK (temperature_unit IN ('C', 'F', 'K')),
--     equipment_type VARCHAR(50) DEFAULT 'freezer',
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     UNIQUE(facility_id, unit_code)
-- );

-- -- ================================
-- -- TIME SERIES DATA TABLES  
-- -- ================================

-- -- Main temperature readings table (hot data - recent readings)
-- CREATE TABLE temperature_readings (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     customer_id UUID NOT NULL REFERENCES customers(id),
--     facility_id UUID NOT NULL REFERENCES facilities(id),
--     storage_unit_id UUID NOT NULL REFERENCES storage_units(id),
--     temperature DECIMAL(8, 2), -- Can be NULL for equipment failures
--     temperature_unit VARCHAR(5) NOT NULL,
--     recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
--     sensor_id VARCHAR(100),
--     quality_score DECIMAL(3, 2) DEFAULT 1.0 CHECK (quality_score >= 0 AND quality_score <= 1),
--     equipment_status VARCHAR(20) DEFAULT 'normal',
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- -- Partitioned table for historical data (warm data)
-- CREATE TABLE temperature_readings_history (
--     id UUID DEFAULT uuid_generate_v4(),
--     customer_id UUID NOT NULL REFERENCES customers(id),
--     facility_id UUID NOT NULL REFERENCES facilities(id),
--     storage_unit_id UUID NOT NULL REFERENCES storage_units(id),
--     temperature DECIMAL(8, 2),
--     temperature_unit VARCHAR(5) NOT NULL,
--     recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
--     sensor_id VARCHAR(100),
--     quality_score DECIMAL(3, 2) DEFAULT 1.0 CHECK (quality_score >= 0 AND quality_score <= 1),
--     equipment_status VARCHAR(20) DEFAULT 'normal',
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     PRIMARY KEY (id, recorded_at)  -- ✅ required for range partitioning
-- ) PARTITION BY RANGE (recorded_at);



-- -- Create monthly partitions for the last year and next year
-- DO $$
-- DECLARE
--     start_date DATE;
--     end_date DATE;
--     partition_name TEXT;
-- BEGIN
--     -- Create partitions for last 12 months and next 12 months
--     FOR i IN -12..12 LOOP
--         start_date := DATE_TRUNC('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
--         end_date := start_date + '1 month'::INTERVAL;
--         partition_name := 'temperature_readings_history_' || TO_CHAR(start_date, 'YYYY_MM');
        
--         EXECUTE FORMAT('CREATE TABLE IF NOT EXISTS %I PARTITION OF temperature_readings_history
--                        FOR VALUES FROM (%L) TO (%L)', 
--                        partition_name, start_date, end_date);
--     END LOOP;
-- END $$;

-- -- ================================
-- -- AUTHENTICATION & AUTHORIZATION
-- -- ================================

-- -- Customer API tokens
-- CREATE TABLE customer_tokens (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
--     token_hash VARCHAR(255) NOT NULL UNIQUE,
--     token_name VARCHAR(100),
--     permissions JSONB DEFAULT '["read"]'::jsonb,
--     accessible_units UUID[] DEFAULT '{}', -- Array of unit IDs
--     rate_limit_per_hour INTEGER DEFAULT 1000,
--     expires_at TIMESTAMP WITH TIME ZONE,
--     last_used_at TIMESTAMP WITH TIME ZONE,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     is_active BOOLEAN DEFAULT TRUE
-- );

-- -- ================================
-- -- METADATA & CONFIGURATION
-- -- ================================

-- -- Data ingestion logs
-- CREATE TABLE ingestion_logs (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     customer_id UUID NOT NULL REFERENCES customers(id),
--     source_type VARCHAR(20) NOT NULL, -- 'csv', 'api', 'webhook'
--     source_reference VARCHAR(255), -- filename, api endpoint, etc.
--     records_processed INTEGER DEFAULT 0,
--     records_success INTEGER DEFAULT 0,
--     records_failed INTEGER DEFAULT 0,
--     error_details JSONB,
--     started_at TIMESTAMP WITH TIME ZONE NOT NULL,
--     completed_at TIMESTAMP WITH TIME ZONE,
--     status VARCHAR(20) DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed'))
-- );

-- -- System configuration
-- CREATE TABLE system_config (
--     key VARCHAR(100) PRIMARY KEY,
--     value JSONB NOT NULL,
--     description TEXT,
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- -- ================================
-- -- INDEXES FOR PERFORMANCE
-- -- ================================

-- -- Primary indexes for temperature readings
-- CREATE INDEX idx_temp_readings_customer_unit_time ON temperature_readings 
--     (customer_id, storage_unit_id, recorded_at DESC);

-- CREATE INDEX idx_temp_readings_recorded_at ON temperature_readings (recorded_at DESC);

-- CREATE INDEX idx_temp_readings_customer_time ON temperature_readings 
--     (customer_id, recorded_at DESC);

-- -- Indexes for lookups
-- CREATE INDEX idx_facilities_customer ON facilities (customer_id);
-- CREATE INDEX idx_storage_units_facility ON storage_units (facility_id);
-- CREATE INDEX idx_customer_tokens_customer ON customer_tokens (customer_id);
-- CREATE INDEX idx_customer_tokens_hash ON customer_tokens (token_hash) WHERE is_active = TRUE;

-- -- ================================
-- -- VIEWS FOR COMMON QUERIES
-- -- ================================

-- -- Latest temperature readings per unit
-- CREATE VIEW latest_temperature_readings AS
-- SELECT DISTINCT ON (storage_unit_id)
--     tr.storage_unit_id,
--     tr.customer_id,
--     tr.facility_id,
--     tr.temperature,
--     tr.temperature_unit,
--     tr.recorded_at,
--     tr.sensor_id,
--     tr.quality_score,
--     tr.equipment_status,
--     c.customer_code,
--     c.name as customer_name,
--     f.name as facility_name,
--     f.city,
--     f.country,
--     su.name as unit_name,
--     su.unit_code,
--     su.set_temperature,
--     su.size_value,
--     su.size_unit
-- FROM temperature_readings tr
-- JOIN customers c ON tr.customer_id = c.id
-- JOIN facilities f ON tr.facility_id = f.id  
-- JOIN storage_units su ON tr.storage_unit_id = su.id
-- WHERE c.is_active = TRUE
-- ORDER BY storage_unit_id, recorded_at DESC;

-- -- Customer summary view
-- CREATE VIEW customer_summary AS
-- SELECT 
--     c.id,
--     c.customer_code,
--     c.name,
--     c.data_sharing_method,
--     COUNT(DISTINCT f.id) as facility_count,
--     COUNT(DISTINCT su.id) as unit_count,
--     COUNT(DISTINCT tr.id) as total_readings,
--     MAX(tr.recorded_at) as last_reading_at
-- FROM customers c
-- LEFT JOIN facilities f ON c.id = f.customer_id
-- LEFT JOIN storage_units su ON f.id = su.facility_id
-- LEFT JOIN temperature_readings tr ON su.id = tr.storage_unit_id
-- WHERE c.is_active = TRUE
-- GROUP BY c.id, c.customer_code, c.name, c.data_sharing_method;

-- -- ================================
-- -- FUNCTIONS FOR DATA MANAGEMENT
-- -- ================================

-- -- Function to convert temperatures between units
-- CREATE OR REPLACE FUNCTION convert_temperature(
--     temp_value DECIMAL(8,2),
--     from_unit VARCHAR(5),
--     to_unit VARCHAR(5)
-- ) RETURNS DECIMAL(8,2) AS $$
-- BEGIN
--     IF from_unit = to_unit THEN
--         RETURN temp_value;
--     END IF;
    
--     -- Convert to Celsius first
--     CASE from_unit
--         WHEN 'F' THEN temp_value := (temp_value - 32) * 5.0/9.0;
--         WHEN 'K' THEN temp_value := temp_value - 273.15;
--         -- 'C' stays as is
--     END CASE;
    
--     -- Convert from Celsius to target unit
--     CASE to_unit
--         WHEN 'F' THEN RETURN temp_value * 9.0/5.0 + 32;
--         WHEN 'K' THEN RETURN temp_value + 273.15;
--         WHEN 'C' THEN RETURN temp_value;
--     END CASE;
    
--     RETURN temp_value;
-- END;
-- $$ LANGUAGE plpgsql IMMUTABLE;

-- -- Function to convert area between units
-- CREATE OR REPLACE FUNCTION convert_area(
--     area_value DECIMAL(12,2),
--     from_unit VARCHAR(10),
--     to_unit VARCHAR(10)
-- ) RETURNS DECIMAL(12,2) AS $$
-- BEGIN
--     IF from_unit = to_unit THEN
--         RETURN area_value;
--     END IF;
    
--     -- Convert to square meters first
--     CASE from_unit
--         WHEN 'sqft', 'ft2' THEN area_value := area_value * 0.092903;
--         -- 'sqm', 'm2' stays as is
--     END CASE;
    
--     -- Convert from square meters to target unit
--     CASE to_unit
--         WHEN 'sqft', 'ft2' THEN RETURN area_value / 0.092903;
--         WHEN 'sqm', 'm2' THEN RETURN area_value;
--     END CASE;
    
--     RETURN area_value;
-- END;
-- $$ LANGUAGE plpgsql IMMUTABLE;

-- -- ================================
-- -- TRIGGERS FOR MAINTENANCE
-- -- ================================

-- -- Update timestamp trigger
-- CREATE OR REPLACE FUNCTION update_updated_at_column()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     NEW.updated_at = CURRENT_TIMESTAMP;
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;

-- CREATE TRIGGER update_customers_updated_at 
--     BEFORE UPDATE ON customers
--     FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- -- Data archival trigger (move old data to history table)
-- CREATE OR REPLACE FUNCTION archive_old_temperature_data()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     -- Move data older than 30 days to history table
--     INSERT INTO temperature_readings_history 
--     SELECT * FROM temperature_readings 
--     WHERE recorded_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
--     DELETE FROM temperature_readings 
--     WHERE recorded_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
--     RETURN NULL;
-- END;
-- $$ LANGUAGE plpgsql;

-- -- ================================
-- -- SAMPLE DATA INSERT
-- -- ================================

-- -- Insert assignment customers A and B
-- INSERT INTO customers (customer_code, name, data_sharing_method, data_frequency_seconds) VALUES
-- ('A', 'Customer A', 'csv', 300),
-- ('B', 'Customer B', 'api', 900);

-- -- Insert sample configuration
-- INSERT INTO system_config (key, value, description) VALUES
-- ('data_retention_days', '2555', 'Number of days to retain temperature data'),
-- ('max_temperature_deviation', '{"warning": 2, "critical": 5}', 'Temperature deviation thresholds'),
-- ('supported_temp_units', '["C", "F", "K"]', 'Supported temperature units'),
-- ('supported_size_units', '["sqm", "sqft", "m2", "ft2"]', 'Supported area units');

-- -- Add comments for documentation
-- COMMENT ON TABLE customers IS 'Customer profiles and data sharing configuration';
-- COMMENT ON TABLE facilities IS 'Customer facilities (warehouses, plants, etc.)';
-- COMMENT ON TABLE storage_units IS 'Individual temperature-monitored storage units';
-- COMMENT ON TABLE temperature_readings IS 'Recent temperature readings (hot data)';
-- COMMENT ON TABLE temperature_readings_history IS 'Historical temperature readings (warm data)';
-- COMMENT ON TABLE customer_tokens IS 'API authentication tokens for customers';
-- COMMENT ON TABLE ingestion_logs IS 'Data ingestion processing logs';

-- COMMENT ON COLUMN storage_units.name IS 'Can be NULL - some customers do not name their units';
-- COMMENT ON COLUMN facilities.city IS 'Can be NULL - some customers do not provide location';
-- COMMENT ON COLUMN temperature_readings.temperature IS 'Can be NULL - represents equipment failure/sensor malfunction';


-- database/schema.sql (Updated with fixed functions)
-- Temperature Monitoring System Database Schema
-- Designed to handle diverse customer data with different units and null values

-- Extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================
-- CUSTOMER MANAGEMENT TABLES
-- ================================

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_code VARCHAR(10) UNIQUE NOT NULL, -- 'A', 'B', etc.
    name VARCHAR(255) NOT NULL,
    data_sharing_method VARCHAR(20) NOT NULL CHECK (data_sharing_method IN ('csv', 'api', 'webhook')),
    data_frequency_seconds INTEGER DEFAULT 300,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Facilities table  
CREATE TABLE IF NOT EXISTS facilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    facility_code VARCHAR(50) NOT NULL, -- For customer reference
    name VARCHAR(255), -- Can be NULL
    city VARCHAR(100), -- Can be NULL  
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8), -- For future geographic features
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, facility_code)
);

-- Storage units table
CREATE TABLE IF NOT EXISTS storage_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    facility_id UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    unit_code VARCHAR(50) NOT NULL, -- For customer reference
    name VARCHAR(255), -- Can be NULL (like Customer A)
    size_value DECIMAL(12, 2) NOT NULL,
    size_unit VARCHAR(10) NOT NULL CHECK (size_unit IN ('sqm', 'sqft', 'm2', 'ft2')),
    set_temperature DECIMAL(8, 2) NOT NULL,
    temperature_unit VARCHAR(5) NOT NULL CHECK (temperature_unit IN ('C', 'F', 'K')),
    equipment_type VARCHAR(50) DEFAULT 'freezer',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(facility_id, unit_code)
);

-- ================================
-- TIME SERIES DATA TABLES  
-- ================================

-- Main temperature readings table (hot data - recent readings)
CREATE TABLE IF NOT EXISTS temperature_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    facility_id UUID NOT NULL REFERENCES facilities(id),
    storage_unit_id UUID NOT NULL REFERENCES storage_units(id),
    temperature DECIMAL(8, 2), -- Can be NULL for equipment failures
    temperature_unit VARCHAR(5) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sensor_id VARCHAR(100),
    quality_score DECIMAL(3, 2) DEFAULT 1.0 CHECK (quality_score >= 0 AND quality_score <= 1),
    equipment_status VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Partitioned table for historical data (warm data)
CREATE TABLE IF NOT EXISTS temperature_readings_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    facility_id UUID NOT NULL REFERENCES facilities(id),
    storage_unit_id UUID NOT NULL REFERENCES storage_units(id),
    temperature DECIMAL(8, 2),
    temperature_unit VARCHAR(5) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sensor_id VARCHAR(100),
    quality_score DECIMAL(3, 2) DEFAULT 1.0 CHECK (quality_score >= 0 AND quality_score <= 1),
    equipment_status VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (recorded_at);

-- Create monthly partitions for the last year and next year
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    -- Create partitions for last 12 months and next 12 months
    FOR i IN -12..12 LOOP
        start_date := DATE_TRUNC('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
        end_date := start_date + '1 month'::INTERVAL;
        partition_name := 'temperature_readings_history_' || TO_CHAR(start_date, 'YYYY_MM');
        
        EXECUTE FORMAT('CREATE TABLE IF NOT EXISTS %I PARTITION OF temperature_readings_history
                       FOR VALUES FROM (%L) TO (%L)', 
                       partition_name, start_date, end_date);
    END LOOP;
END $$;

-- ================================
-- AUTHENTICATION & AUTHORIZATION
-- ================================

-- Customer API tokens
CREATE TABLE IF NOT EXISTS customer_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    token_name VARCHAR(100),
    permissions JSONB DEFAULT '["read"]'::jsonb,
    accessible_units UUID[] DEFAULT '{}', -- Array of unit IDs
    rate_limit_per_hour INTEGER DEFAULT 1000,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- ================================
-- METADATA & CONFIGURATION
-- ================================

-- Data ingestion logs
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    source_type VARCHAR(20) NOT NULL, -- 'csv', 'api', 'webhook'
    source_reference VARCHAR(255), -- filename, api endpoint, etc.
    records_processed INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_details JSONB,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed'))
);

-- System configuration
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- INDEXES FOR PERFORMANCE
-- ================================

-- Primary indexes for temperature readings
CREATE INDEX IF NOT EXISTS idx_temp_readings_customer_unit_time ON temperature_readings 
    (customer_id, storage_unit_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_temp_readings_recorded_at ON temperature_readings (recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_temp_readings_customer_time ON temperature_readings 
    (customer_id, recorded_at DESC);

-- Indexes for lookups
CREATE INDEX IF NOT EXISTS idx_facilities_customer ON facilities (customer_id);
CREATE INDEX IF NOT EXISTS idx_storage_units_facility ON storage_units (facility_id);
CREATE INDEX IF NOT EXISTS idx_customer_tokens_customer ON customer_tokens (customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_tokens_hash ON customer_tokens (token_hash) WHERE is_active = TRUE;

-- ================================
-- FUNCTIONS FOR DATA MANAGEMENT
-- ================================

-- Function to convert temperatures between units
CREATE OR REPLACE FUNCTION convert_temperature(
    temp_value DECIMAL(8,2),
    from_unit VARCHAR(5),
    to_unit VARCHAR(5)
) RETURNS DECIMAL(8,2) AS $$
BEGIN
    IF temp_value IS NULL THEN
        RETURN NULL;
    END IF;
    
    IF from_unit = to_unit THEN
        RETURN temp_value;
    END IF;
    
    -- Convert to Celsius first
    CASE from_unit
        WHEN 'F' THEN temp_value := (temp_value - 32) * 5.0/9.0;
        WHEN 'K' THEN temp_value := temp_value - 273.15;
        ELSE NULL; -- 'C' stays as is
    END CASE;
    
    -- Convert from Celsius to target unit
    CASE to_unit
        WHEN 'F' THEN RETURN temp_value * 9.0/5.0 + 32;
        WHEN 'K' THEN RETURN temp_value + 273.15;
        ELSE RETURN temp_value; -- 'C' or unknown unit
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to convert area between units
CREATE OR REPLACE FUNCTION convert_area(
    area_value DECIMAL(12,2),
    from_unit VARCHAR(10),
    to_unit VARCHAR(10)
) RETURNS DECIMAL(12,2) AS $$
BEGIN
    IF area_value IS NULL THEN
        RETURN NULL;
    END IF;
    
    IF from_unit = to_unit THEN
        RETURN area_value;
    END IF;
    
    -- Convert to square meters first
    CASE from_unit
        WHEN 'sqft', 'ft2' THEN area_value := area_value * 0.092903;
        ELSE NULL; -- 'sqm', 'm2' stays as is
    END CASE;
    
    -- Convert from square meters to target unit
    CASE to_unit
        WHEN 'sqft', 'ft2' THEN RETURN area_value / 0.092903;
        ELSE RETURN area_value; -- 'sqm', 'm2' or unknown unit
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ================================
-- VIEWS FOR COMMON QUERIES
-- ================================

-- Latest temperature readings per unit
CREATE OR REPLACE VIEW latest_temperature_readings AS
SELECT DISTINCT ON (storage_unit_id)
    tr.storage_unit_id,
    tr.customer_id,
    tr.facility_id,
    tr.temperature,
    tr.temperature_unit,
    tr.recorded_at,
    tr.sensor_id,
    tr.quality_score,
    tr.equipment_status,
    c.customer_code,
    c.name as customer_name,
    f.name as facility_name,
    f.city,
    f.country,
    su.name as unit_name,
    su.unit_code,
    su.set_temperature,
    su.size_value,
    su.size_unit
FROM temperature_readings tr
JOIN customers c ON tr.customer_id = c.id
JOIN facilities f ON tr.facility_id = f.id  
JOIN storage_units su ON tr.storage_unit_id = su.id
WHERE c.is_active = TRUE
ORDER BY storage_unit_id, recorded_at DESC;

-- Customer summary view
CREATE OR REPLACE VIEW customer_summary AS
SELECT 
    c.id,
    c.customer_code,
    c.name,
    c.data_sharing_method,
    COUNT(DISTINCT f.id) as facility_count,
    COUNT(DISTINCT su.id) as unit_count,
    COUNT(DISTINCT tr.id) as total_readings,
    MAX(tr.recorded_at) as last_reading_at
FROM customers c
LEFT JOIN facilities f ON c.id = f.customer_id
LEFT JOIN storage_units su ON f.id = su.facility_id
LEFT JOIN temperature_readings tr ON su.id = tr.storage_unit_id
WHERE c.is_active = TRUE
GROUP BY c.id, c.customer_code, c.name, c.data_sharing_method;

-- ================================
-- TRIGGERS FOR MAINTENANCE
-- ================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_customers_updated_at 
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================
-- SAMPLE DATA INSERT
-- ================================

-- Insert assignment customers A and B
INSERT INTO customers (customer_code, name, data_sharing_method, data_frequency_seconds) VALUES
('A', 'Customer A', 'csv', 300),
('B', 'Customer B', 'api', 900)
ON CONFLICT (customer_code) DO NOTHING;

-- Insert sample configuration
INSERT INTO system_config (key, value, description) VALUES
('data_retention_days', '2555', 'Number of days to retain temperature data'),
('max_temperature_deviation', '{"warning": 2, "critical": 5}', 'Temperature deviation thresholds'),
('supported_temp_units', '["C", "F", "K"]', 'Supported temperature units'),
('supported_size_units', '["sqm", "sqft", "m2", "ft2"]', 'Supported area units')
ON CONFLICT (key) DO NOTHING;

-- Add comments for documentation
COMMENT ON TABLE customers IS 'Customer profiles and data sharing configuration';
COMMENT ON TABLE facilities IS 'Customer facilities (warehouses, plants, etc.)';
COMMENT ON TABLE storage_units IS 'Individual temperature-monitored storage units';
COMMENT ON TABLE temperature_readings IS 'Recent temperature readings (hot data)';
COMMENT ON TABLE temperature_readings_history IS 'Historical temperature readings (warm data)';
COMMENT ON TABLE customer_tokens IS 'API authentication tokens for customers';
COMMENT ON TABLE ingestion_logs IS 'Data ingestion processing logs';

COMMENT ON COLUMN storage_units.name IS 'Can be NULL - some customers do not name their units';
COMMENT ON COLUMN facilities.city IS 'Can be NULL - some customers do not provide location';
COMMENT ON COLUMN temperature_readings.temperature IS 'Can be NULL - represents equipment failure/sensor malfunction';