# Temperature Monitoring System

A temperature monitoring system that simulates customer data, ingests it through a pipeline, and provides APIs and a dashboard for visualization. Built as a proof-of-concept with multiple services that can run independently.


## 🏗️ System Architecture
![System architecture diagram](./architecture.png)

> *Fig 1. End-to-end data flow from customer simulation through ingestion, queue, database, and API layers.*


## ✨ Features

- **Customer Simulation**: Multiple mock customers with API and CSV data sources
- **Data Ingestion Pipeline**: Scheduled collection and processing via RabbitMQ
- **RESTful API**: FastAPI with authentication and comprehensive endpoints
- **Web Dashboard**: Flask-based visualization interface
- **CLI Management**: Command-line tools for customer and data management
- **Database Tools**: Status checking and data cleanup utilities

## 🛠️ Technology Stack

- **Backend**: Python, FastAPI, Flask
- **Database**: PostgreSQL
- **Message Queue**: RabbitMQ
- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **CLI**: Python Click

## 🚀 Setup and Running

### Prerequisites
- Python 3.10+
- PostgreSQL
- RabbitMQ

### Installation
```bash
git clone https://github.com/aryan-at-ul/temperature-monitoring-system.git
cd temperature-monitoring-system
pip install -r requirements.txt
```

### FOR EXACT REPLICATION 
```
psql -U postgres -h localhost -c "CREATE USER tm_user WITH PASSWORD 'tm_pass';"
psql -U postgres -h localhost -c "CREATE DATABASE temperature_db OWNER tm_user;"

PGPASSWORD=tm_pass psql -U tm_user -h localhost -d temperature_db -f temperature_db_dump.sql
```
This created the exact replica of the Database used for dev and testing


### Database Setup
```bash
psql -U postgres -d temperature_db -f database/schema.sql
```

## 🎮 Running the System

The system requires **4 separate terminal windows**:

### Terminal 1: Customer Simulation Service
```bash
python run_simulation_service.py
```
This starts mock customer servers that simulate real customer API endpoints and CSV download services.

**Output:**
```
Each customer is running on a dedicated port. The ingestion service will call these endpoints.
  -> (API) Pharma Corp A (A) is starting on http://localhost:8001
  -> (CSV) Local Business B (B) is starting on http://localhost:8002
  -> (API) Industrial Corp C (C) is starting on http://localhost:8003
  -> (API) Industrial Corp D (D) is starting on http://localhost:8004
  -> (CSV) Food Storage Ltd E (E) is starting on http://localhost:8005
  -> (API) Industrial Corp F (F) is starting on http://localhost:8006
  -> (CSV) Food Storage Ltd G (G) is starting on http://localhost:8007
  -> (CSV) Food Storage Ltd H (H) is starting on http://localhost:8008
  -> (CSV) Food Storage Ltd I (I) is starting on http://localhost:8009
  -> (CSV) Local Business J (J) is starting on http://localhost:8010
```

### Terminal 2: Data Ingestion Service
```bash
python run_ingestion_service.py
```
**Output:**
```
--- Starting Data Ingestion Service ---
2025-06-19 12:15:28,743 - INFO - Scheduled api ingestion for customer A every 60 seconds
2025-06-19 12:15:28,743 - INFO - Scheduled csv ingestion for customer B every 300 seconds
2025-06-19 12:15:28,804 - INFO - Successfully collected 63 readings from A
2025-06-19 12:15:28,806 - INFO - Successfully collected 44 readings from C
2025-06-19 12:15:28,868 - INFO - Inserted 100 temperature readings into database
```

### Terminal 3: Backend API Server
```bash
python -m api.main
```
**Output:**
```
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
2025-06-19 12:16:08,660 - INFO - Database connected successfully
INFO: Application startup complete.
```

### Terminal 4: Dashboard
```bash
python dashboard/app.py
```
**Output:**
```
* Running on http://127.0.0.1:5000
* Running on http://10.150.8.54:5000
* Debug mode: on
```

## 📸 Dashboard Screenshots

### 🔹 Customer Landing Page

![Customer Landing](./customer_landing.png)

> *Figure 2. Landing view showing a summary of all customers and their statuses.*

### 🔹 Facility & Unit Overview

![Customer Facilities](./customer_facilities.png)

> *Figure 3. Facility overview for a selected customer, listing all connected storage units and readings.*

![Customer Facilities (Alt)](./customer_facilities2.png)

> *Figure 4. Alternate layout for facility and temperature unit breakdown.*

### 🔹 Unit Detail View

![Unit View](./units.png)

> *Figure 5. Detailed view of temperature readings for individual units, including analytics and trends.*


## 🧪 Mock Customer Setup

The customer ingestion process is slightly manual in this prototype. The `customers` table expects an active `api_url` to start the ingestion. To simulate this:

* Mock customers are created using **predefined templates** via the CLI.
* After creation, I manually updated their `api_url` entries (e.g., pointing to a local API or CSV endpoint).
* The ingestion module then uses this URL to fetch data (either JSON or CSV) and convert it into events for insertion into the queue.

Each customer follows one of two formats:
* **API-based**: Provides live JSON responses at `/temperature/current`
* **CSV-based**: Serves downloadable files at `/data/download.csv`

These mock endpoints are critical for simulating real-world ingestion and are used by the pipeline to test the end-to-end flow.

### 🗂️ `public.customers` (Simplified)

| Code | Name | Method | Frequency (s) | URL |
|------|------|--------|---------------|-----|
| A | Customer A | API | 60 | http://localhost:8001/temperature/current |
| B | Customer B | CSV | 300 | http://localhost:8002/data/download.csv |
| C | Customer C | API | 660 | http://localhost:8003/temperature/current |
| D | Customer D | API | 840 | http://localhost:8004/temperature/current |
| E | Customer E | CSV | 300 | http://localhost:8005/data/download.csv |
| F | Customer F | API | 660 | http://localhost:8006/temperature/current |
| G | Customer G | CSV | 300 | http://localhost:8007/data/download.csv |
| H | Customer H | CSV | 300 | http://localhost:8008/data/download.csv |
| I | Customer I | CSV | 300 | http://localhost:8009/data/download.csv |
| J | Customer J | CSV | 300 | http://localhost:8010/data/download.csv |

## 🎮 CLI Tools

The CLI is used to mock customer profiles and generate realistic customer API responses (CSV or JSON format):

### List Available Customer Templates
```bash
python -m simulation.cli list-templates
```
**Output:**
```
📋 Available customer templates:

🏷️  pharmaceutical
   📡 Data method: api
   🏭 Facilities: 1-2
   🌡️  Units per facility: 2-8
   📊 Temperature unit: C
   📏 Size unit: sqm
   🔧 Reliability: high (null readings: 0.01%)

🏷️  food_storage
   📡 Data method: csv
   🏭 Facilities: 1-3
   🌡️  Units per facility: 1-4
   📊 Temperature unit: F
   📏 Size unit: sqft
   🔧 Reliability: medium (null readings: 0.20%)

🏷️  small_business
   📡 Data method: csv
   🏭 Facilities: 1-1
   🌡️  Units per facility: 1-2
   📊 Temperature unit: C
   📏 Size unit: sqm
   🔧 Reliability: low (null readings: 1.00%)

🏷️  industrial
   📡 Data method: api
   🏭 Facilities: 2-5
   🌡️  Units per facility: 3-10
   📊 Temperature unit: F
   📏 Size unit: sqft
   🔧 Reliability: medium (null readings: 0.50%)
```

### View Generated Customers
```bash
python -m simulation.cli show-customers
```
**Sample Output:**
```
📊 A: Pharma Corp A
   📡 Data method: api
   🌡️  Total units: 9
   🏭 Pharma Facility 1 (Oxford, England)
      🌡️  Ultra-Low Freezer 1: -74.2°C, 328 sqm, every 229s
      🌡️  Ultra-Low Freezer 2: -78.4°C, 303 sqm, every 201s
   🏭 Pharma Facility 2 (London, England)
      🌡️  Ultra-Low Freezer 1: -67.5°C, 235 sqm, every 226s

📊 B: Local Business B
   📡 Data method: csv
   🌡️  Total units: 2
   🏭 [Unnamed] (Sheffield, England)
      🌡️  [Unnamed]: -3.2°C, 864 sqm, every 826s
```

### Generate Assignment Data
```bash
python -m simulation.cli generate-assignment-data --customer both --hours 6
```
**Output:**
```
🏢 Generating Customer A (Assignment specifications)
💾 Generated CSV: customer_A_data_assignment_20250619_123442.csv
   📊 Records: 73
   📁 Path: data/assignment/csv_files/customer_A_data_assignment_20250619_123442.csv

🏢 Generating Customer B (Assignment specifications)
💾 Saved JSON: customer_B_20250619_123442.json
   📊 Generated 75 readings
   🔗 Customer B uses API method - data saved as JSON
```

### Generate Test Data
```bash
python -m simulation.cli generate-data --customer-id TEST --template pharmaceutical --hours 4
```

### Generate CSV Files
```bash
python -m simulation.cli generate-csv --customer-id A --hours 24 --files 3
```

### Validate Assignment
```bash
python -m simulation.cli validate-assignment
```
**Output:**
```
✅ Customer A: Customer A
   Data method: csv
   Facilities: 1
   City: [null] ✓
   Country: England ✓
   Size: 930 sqm ✓
   Set temp: -20°C ✓

✅ Customer B: Customer B
   Data method: api
   Units: 3 ✓
   Unit 1: Deep Freeze 1 ✓ (50000 sqft, 0°F)
   Unit 2: Chilled Room 1 ✓ (10000 sqft, 0°F)
   Unit 3: Chilled Room 2 ✓ (5000 sqft, 45°F)
```

## 🧪 Testing

### API Endpoint Testing
```bash
python -m api.tests.test_all_endpoints
```
**Sample Output:**
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
✅ Status code: 200 - GET http://localhost:8000/api/v1/temperature/stats

======= TESTS COMPLETED IN 0.42 SECONDS =======
```

## 🔧 Debug & Maintenance

### Check Database Status
```bash
python check_database_status.py
```
**Output:**
```
=== Database Status ===
customers: 10 records
customer_tokens: 21 records
facilities: 21 records
storage_units: 94 records
temperature_readings: 96579 records
ingestion_logs: 30 records
system_config: 4 records

=== Recent Temperature Readings ===
Customer: F, Facility: facility_F_1, Unit: unit_F_1_2, Temp: 1.39F, Recorded: 2025-06-18 09:41:58
Customer: F, Facility: facility_F_1, Unit: unit_F_1_3, Temp: -8.10F, Recorded: 2025-06-18 09:42:19

=== Recent Ingestion Logs ===
Customer: J, Type: csv, Status: success, Processed: 98 (Success: 98, Failed: 0), Duration: 88.67ms
Customer: I, Type: csv, Status: success, Processed: 806 (Success: 806, Failed: 0), Duration: 91.86ms
```

### Clean Database
```bash
python clean_temperature_readings.py
```
**Output:**
```
--- Cleaning Temperature Readings Table ---
Mode: Delete records newer than 1 hour
INFO - Deleted 3834 records newer than 2025-06-18 19:41:51
INFO - Remaining records in temperature_readings table: 96579
```

## 📊 API Endpoints

### Health Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/ping` | Ping |
| `GET` | `/system-info` | System information |

### Temperature Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/temperature` | Get temperature readings |
| `POST` | `/api/v1/temperature` | Create a temperature reading |
| `GET` | `/api/v1/temperature/latest` | Get latest temperature readings |
| `GET` | `/api/v1/temperature/facility/{facility_id}` | Get temperature readings for a facility |
| `GET` | `/api/v1/temperature/unit/{unit_id}` | Get temperature readings for a storage unit |
| `GET` | `/api/v1/temperature/stats` | Get temperature statistics |
| `POST` | `/api/v1/temperature/aggregate` | Aggregate temperature data |
| `GET` | `/api/v1/admin/temperature` | [Admin] Get temperature readings for all customers |

### Facilities Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/facilities` | Get facilities |
| `POST` | `/api/v1/facilities` | Create facility |
| `GET` | `/api/v1/facilities/{facility_id}` | Get facility |
| `PUT` | `/api/v1/facilities/{facility_id}` | Update facility |
| `GET` | `/api/v1/facilities/{facility_id}/detailed` | Get facility with units |
| `GET` | `/api/v1/facilities/{facility_id}/units` | Get storage units |
| `POST` | `/api/v1/facilities/{facility_id}/units` | Create storage unit |
| `GET` | `/api/v1/units/{unit_id}` | Get storage unit |
| `PUT` | `/api/v1/units/{unit_id}` | Update storage unit |

### Customers Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/customers/profile` | Get customer profile |
| `PUT` | `/api/v1/customers/profile` | Update customer profile |
| `GET` | `/api/v1/customers/tokens` | Get customer tokens |
| `POST` | `/api/v1/customers/tokens` | Create customer token |
| `DELETE` | `/api/v1/customers/tokens/{token_id}` | Revoke customer token |

### Admin Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/admin/customers` | [Admin] Get all customers |
| `POST` | `/api/v1/admin/customers` | [Admin] Create customer |
| `GET` | `/api/v1/admin/customers/{customer_id}` | [Admin] Get customer |
| `PUT` | `/api/v1/admin/customers/{customer_id}` | [Admin] Update customer |
| `GET` | `/api/v1/admin/customers/{customer_id}/tokens` | [Admin] Get customer tokens |
| `POST` | `/api/v1/admin/customers/{customer_id}/tokens` | [Admin] Create customer token |
| `GET` | `/api/v1/admin/facilities` | [Admin] Get all facilities |
| `GET` | `/api/v1/admin/config` | [Admin] Get system configuration |
| `PUT` | `/api/v1/admin/config/{key}` | [Admin] Update system configuration |
| `GET` | `/api/v1/admin/ingestion/logs` | [Admin] Get ingestion logs |

### Analytics Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/analytics/temperature/summary` | Get temperature summary |
| `GET` | `/api/v1/analytics/temperature/trends` | Get temperature trends |
| `GET` | `/api/v1/analytics/alarms/history` | Get alarm history |
| `GET` | `/api/v1/analytics/performance` | Get performance metrics |
| `GET` | `/api/v1/admin/analytics/temperature/summary` | [Admin] Get system-wide temperature summary |

### Authentication
```bash
curl -H "Authorization: Bearer read_B_66_token_2025" \
     http://localhost:8000/api/v1/temperature
```

### API Documentation
- **Online**: Available at `http://localhost:8000/docs` when the API server is running
- **Offline**: Complete documentation provided in `swagger_docs/index_offline.html`

## 📁 Project Structure

```
temperature-monitoring-system/
├── api/                     # FastAPI backend
│   ├── main.py             # API server entry point
│   ├── endpoints/          # API routes
│   └── tests/              # API tests
├── dashboard/              # Flask frontend
│   └── app.py             # Dashboard entry point
├── data_ingestion/         # Data collection pipeline
│   ├── collectors/         # API and CSV collectors
│   ├── processors/         # Data processing
│   └── schedulers/         # Job scheduling
├── simulation/             # Customer simulation
│   ├── cli.py             # Command-line interface
│   └── customers/          # Customer templates
├── database/               # Database layer
│   └── schema.sql          # Database schema
├── scripts/                # Utility scripts
│   ├── check_database_status.py
│   └── clean_temperature_readings.py
└── data/                   # Generated files
    ├── csv_files/
    └── assignment/
```

## 🎯 Customer Types

### API Customers
- **A**: Pharma Corp A (Port 8001) - every 60 seconds
- **C**: Industrial Corp C (Port 8003) - every 660 seconds  
- **D**: Industrial Corp D (Port 8004) - every 840 seconds
- **F**: Industrial Corp F (Port 8006) - every 660 seconds

### CSV Customers
- **B**: Local Business B (Port 8002) - every 300 seconds
- **E**: Food Storage Ltd E (Port 8005) - every 300 seconds
- **G**: Food Storage Ltd G (Port 8007) - every 300 seconds
- **H**: Food Storage Ltd H (Port 8008) - every 300 seconds
- **I**: Food Storage Ltd I (Port 8009) - every 300 seconds
- **J**: Local Business J (Port 8010) - every 300 seconds

---


## 🐞 Open Bugs

- **Quality Score Serialization**: `quality_score` is computed as a float (e.g. `0.91`) but the API expects an integer. Causes `ResponseValidationError`.  
  → **Fix**: Update response model to accept `float` or round the value before return.





This is a proof-of-concept assignment demonstrating a multi-service temperature monitoring system with realistic data simulation and comprehensive API testing.