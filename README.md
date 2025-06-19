# Temperature Monitoring System

This repository was created for the **Gyre Energy Backend Interview Exercise** (June 2025). It is a complete **proof-of-concept (PoC)** demonstrating a scalable backend system for collecting and serving temperature data from multiple customers.

## Architecture Overview

![System architecture diagram](./architecture.png)

The system is designed with a modular microservices architecture where each component can be run as an independent service:

- **Customer Simulation Service**: Mock customer endpoints providing temperature data via API/CSV
- **Data Ingestion Service**: Scheduled data collection and processing via RabbitMQ queues
- **REST API Service**: FastAPI backend with authentication and comprehensive endpoints
- **Web Dashboard Service**: Flask-based visualization and monitoring interface
- **Database Layer**: PostgreSQL with proper schema design for temperature readings

This modular design allows for horizontal scaling, independent deployment, and service isolation in production environments.

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, Flask
- **Database**: PostgreSQL 12+
- **Message Queue**: RabbitMQ 3.8+
- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **CLI Tools**: Python Click

## Prerequisites (Ubuntu)

### System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install RabbitMQ (latest version)
sudo apt install curl gnupg apt-transport-https
curl -1sLf "https://keys.openpgp.org/vks/v1/by-fingerprint/0A9AF2115F4687BD29803A206B73A36E6026DFCA" | sudo gpg --dearmor | sudo tee /usr/share/keyrings/com.rabbitmq.team.gpg > /dev/null

# Add RabbitMQ repository
sudo tee /etc/apt/sources.list.d/rabbitmq.list <<EOF
deb [signed-by=/usr/share/keyrings/com.rabbitmq.team.gpg] https://ppa1.novemberain.com/rabbitmq/rabbitmq-server/deb/ubuntu $(lsb_release -cs) main
EOF

sudo apt update
sudo apt install rabbitmq-server

# Start and enable services
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
```

## Installation

### 1. Clone and Setup Python Environment
```bash
git clone https://github.com/aryan-at-ul/temperature-monitoring-system.git
cd temperature-monitoring-system

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration
```bash
# Switch to postgres user and create database
sudo -u postgres psql

# In PostgreSQL shell:
CREATE USER tm_user WITH PASSWORD 'tm_pass';
CREATE DATABASE temperature_db OWNER tm_user;
GRANT ALL PRIVILEGES ON DATABASE temperature_db TO tm_user;
\q

# Initialize database schema (from scaratch, would recommend setting up using db dump)
PGPASSWORD=tm_pass psql -U tm_user -h localhost -d temperature_db -f database/schema.sql

# Load sample data (To replicate exact Dev env)
PGPASSWORD=tm_pass psql -U tm_user -h localhost -d temperature_db -f temperature_db_dump.sql
```

### 3. Environment Configuration
Create `.env` file in project root:
```env
DATABASE_URL=postgresql://tm_user:tm_pass@localhost:5432/temperature_db
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
API_HOST=0.0.0.0
API_PORT=8000
```

## Running the System

The system requires four separate terminal sessions. Each service runs independently:

### Terminal 1: Customer Simulation Service
```bash
source venv/bin/activate
python run_simulation_service.py
```

**Expected Output:**
```
Each customer is running on a dedicated port. The ingestion service will call these endpoints.
  -> (API) Pharma Corp A (A) is starting on http://localhost:8001
  -> (CSV) Local Business B (B) is starting on http://localhost:8002
  -> (API) Industrial Corp C (C) is starting on http://localhost:8003
  ...
```

### Terminal 2: Data Ingestion Service
```bash
source venv/bin/activate
python run_ingestion_service.py
```

**Expected Output:**
```
--- Starting Data Ingestion Service ---
2025-06-19 12:15:28,743 - INFO - Scheduled api ingestion for customer A every 60 seconds
2025-06-19 12:15:28,743 - INFO - Scheduled csv ingestion for customer B every 300 seconds
2025-06-19 12:15:28,804 - INFO - Successfully collected 63 readings from A
```

### Terminal 3: REST API Service
```bash
source venv/bin/activate
python -m api.main
```

**Expected Output:**
```
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
2025-06-19 12:16:08,660 - INFO - Database connected successfully
INFO: Application startup complete.
```

API Documentation: http://localhost:8000/docs

### Terminal 4: Web Dashboard
```bash
source venv/bin/activate
python dashboard/app.py
```

**Expected Output:**
```
* Running on http://127.0.0.1:5000
* Debug mode: on
```

Dashboard: http://localhost:5000

## Usage Examples

### API Authentication
Sample customer token for testing:
```bash
curl -H "Authorization: Bearer read_A_65_token_2025" \
     http://localhost:8000/api/v1/temperature/latest
```

### Dashboard Login
- Username: `A`
- Token: `read_A_65_token_2025`
- Type: `read`

### CLI Management Tools
```bash
# List customer templates
python -m simulation.cli list-templates

# Check system status
python check_database_status.py

# Generate test data
python -m simulation.cli generate-data --customer-id TEST --template pharmaceutical --hours 4
```

## Testing

### Automated API Testing
```bash
python -m api.tests.test_all_endpoints
```

**Expected Output:**
```
======= RUNNING API ENDPOINT TESTS =======
Customer: B, Token Type: read

====== TESTING HEALTH ENDPOINTS ======
✅ Status code: 200 - GET http://localhost:8000/health
✅ Status code: 200 - GET http://localhost:8000/ping

====== TESTING TEMPERATURE ENDPOINTS FOR B (read) ======
✅ Status code: 200 - GET http://localhost:8000/api/v1/temperature
✅ Status code: 200 - GET http://localhost:8000/api/v1/temperature/latest
✅ Status code: 200 - GET http://localhost:8000/api/v1/facilities

======= TESTS COMPLETED IN 0.42 SECONDS =======
```

### System Health Check
```bash
python check_database_status.py
```

**Expected Output:**
```
=== Database Status ===
customers: 10 records
temperature_readings: 96579 records
facilities: 21 records
storage_units: 94 records

=== Recent Temperature Readings ===
Customer: F, Facility: facility_F_1, Unit: unit_F_1_2, Temp: 1.39F
Customer: F, Facility: facility_F_1, Unit: unit_F_1_3, Temp: -8.10F
```

## Key API Endpoints

- `GET /health` - System health check
- `GET /api/v1/temperature/latest` - Latest temperature readings
- `GET /api/v1/facilities` - Customer facilities
- `GET /api/v1/temperature/stats` - Temperature statistics
- `GET /api/v1/admin/customers` - All customers (admin only)

Complete API documentation available at `/docs` when API server is running. Ofline docs present in swagger_docs/index_offline.html (open in browser)


## Testing

The project includes comprehensive unit tests, integration tests, and test coverage reporting to ensure code quality and reliability.

### Prerequisites

Install the required testing dependencies:

```bash
pip install pytest pytest-asyncio pytest-mock aioresponses
```

```bash
# Test each module separately
pytest tests/unit/simulation/ -v
pytest tests/unit/database/ -v
pytest tests/unit/api/test_services/ -v
pytest tests/unit/api/test_endpoints/ -v
pytest tests/test_integration_basic.py -v
pytest tests/ -v

```

Test with coverage
```bash
pytest tests/ --cov=simulation --cov=database --cov=api --cov-report=term-missing --cov-report=html -v
```
then check : htmlcov/index.html


## Troubleshooting

### Service Status Checks
```bash
# PostgreSQL
sudo systemctl status postgresql

# RabbitMQ
sudo systemctl status rabbitmq-server

# Test database connection
PGPASSWORD=tm_pass psql -U tm_user -h localhost -d temperature_db -c "SELECT 1;"
```

<!-- ### Common Issues
- **Port conflicts**: Ensure ports 8000-8010, 5000, 5432, 5672 are available
- **Database connection errors**: Verify PostgreSQL is running and credentials are correct
- **Module import errors**: Ensure virtual environment is activated
- **RabbitMQ connection issues**: Check service status and restart if needed -->

### Logs and Debugging
- API logs: Check terminal running `python -m api.main`
- Ingestion logs: Check terminal running `python run_ingestion_service.py`
- Database logs: `sudo journalctl -u postgresql`
- RabbitMQ logs: `sudo journalctl -u rabbitmq-server`

## Development Notes

This proof-of-concept demonstrates key backend patterns including:
- Modular service design with independent components
- Queue-based data processing pipeline
- Basic API authentication with tokens
- Test suite for endpoint validation
- Command-line tools for data management
- Simple monitoring and status checking

Each Python module can be run as a separate process, showing how the system could be adapted for distributed deployment if needed.