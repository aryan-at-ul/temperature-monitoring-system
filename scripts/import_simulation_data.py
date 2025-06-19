# scripts/import_simulation_data.py (Updated JSON import section)
#!/usr/bin/env python3
import os
import csv
import yaml
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import DatabaseConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimulationDataImporter:
    """Import simulated data into the database"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.customers_created = 0
        self.facilities_created = 0
        self.units_created = 0
        self.readings_imported = 0
        self.errors = 0
        
    def import_customers_from_yaml(self, yaml_path: str):
        """Import customer profiles from YAML - handles your specific structure"""
        if not os.path.exists(yaml_path):
            print(f"⚠️  Customer YAML not found: {yaml_path}")
            return
        
        print(f"📋 Importing customers from {yaml_path}")
        
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Handle the nested structure: customers -> {A: {...}, B: {...}}
        customers_dict = data.get('customers', {})
        print(f"Found {len(customers_dict)} customers to import: {list(customers_dict.keys())}")
        
        for customer_code, customer_data in customers_dict.items():
            try:
                print(f"🔄 Processing customer {customer_code}...")
                self._import_customer_hierarchy(customer_code, customer_data)
                self.customers_created += 1
                print(f"✅ Imported customer {customer_code}")
                
            except Exception as e:
                print(f"❌ Failed to import customer {customer_code}: {e}")
                logger.exception(f"Detailed error for customer {customer_code}")
                self.errors += 1
    
    def _import_customer_hierarchy(self, customer_code, customer_data):
        """Import customer, facilities, and units from your YAML structure"""
        
      
        customer_name = f"Customer {customer_code}"
        data_method = customer_data.get('data_sharing_method', 'csv')
        
     
        data_config = customer_data.get('data_config', {})
        frequency_minutes = data_config.get('api_polling_frequency_minutes', 5)
        frequency_seconds = frequency_minutes * 60
        
        print(f"  📊 Customer: {customer_code} - Method: {data_method} - Frequency: {frequency_seconds}s")
        
       
        customer_query = """
        INSERT INTO customers (customer_code, name, data_sharing_method, data_frequency_seconds)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (customer_code) DO UPDATE SET
            name = EXCLUDED.name,
            data_sharing_method = EXCLUDED.data_sharing_method,
            data_frequency_seconds = EXCLUDED.data_frequency_seconds
        RETURNING id
        """
        
        result = self.db.execute_query(customer_query, (
            customer_code,
            customer_name,
            data_method,
            frequency_seconds
        ))
        
        customer_id = result[0]['id']
        

        facilities = customer_data.get('facilities', [])
        print(f"  🏢 Found {len(facilities)} facilities")
        
        for facility_data in facilities:
            self._import_facility(customer_id, facility_data)
    
    def _import_facility(self, customer_id, facility_data):
        """Import facility and its storage units from your structure"""
        
        facility_code = facility_data.get('id')  # Your YAML uses 'id' field
        facility_name = facility_data.get('name')
        city = facility_data.get('city')
        country = facility_data.get('country', 'Unknown')
        
        print(f"    🏭 Facility: {facility_code} - {facility_name} ({city}, {country})")
        
        facility_query = """
        INSERT INTO facilities (customer_id, facility_code, name, city, country)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (customer_id, facility_code) DO UPDATE SET
            name = EXCLUDED.name,
            city = EXCLUDED.city,
            country = EXCLUDED.country
        RETURNING id
        """
        
        result = self.db.execute_query(facility_query, (
            customer_id,
            facility_code,
            facility_name,
            city,
            country
        ))
        
        facility_db_id = result[0]['id']
        self.facilities_created += 1
        

        units = facility_data.get('units', [])
        print(f"      ❄️  Found {len(units)} storage units")
        
        for unit_data in units:
            self._import_storage_unit(facility_db_id, unit_data)
    
    def _import_storage_unit(self, facility_id, unit_data):
        """Import storage unit from your structure"""
        
        unit_code = unit_data.get('id')
        unit_name = unit_data.get('name')  # Can be None
        size_value = unit_data.get('size', 50.0)
        size_unit = unit_data.get('size_unit', 'sqm')
        set_temperature = unit_data.get('set_temperature', -18.0)
        temp_unit = unit_data.get('temperature_unit', 'C')
        equipment_type = unit_data.get('equipment_type', 'freezer')
        
        print(f"        📦 Unit: {unit_code} - {unit_name or 'Unnamed'} ({size_value} {size_unit}, target: {set_temperature}°{temp_unit})")
        
        unit_query = """
        INSERT INTO storage_units (facility_id, unit_code, name, size_value, size_unit, 
                                 set_temperature, temperature_unit, equipment_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (facility_id, unit_code) DO UPDATE SET
            name = EXCLUDED.name,
            size_value = EXCLUDED.size_value,
            size_unit = EXCLUDED.size_unit,
            set_temperature = EXCLUDED.set_temperature,
            temperature_unit = EXCLUDED.temperature_unit,
            equipment_type = EXCLUDED.equipment_type
        RETURNING id
        """
        
        self.db.execute_query(unit_query, (
            facility_id,
            unit_code,
            unit_name,
            float(size_value),
            size_unit,
            float(set_temperature),
            temp_unit,
            equipment_type
        ))
        
        self.units_created += 1
    
    def import_csv_files(self, csv_dir: str):
        """Import CSV files from directory"""
        if not os.path.exists(csv_dir):
            print(f"⚠️  CSV directory not found: {csv_dir}")
            return
        
        csv_files = list(Path(csv_dir).glob("*.csv"))
        print(f"📄 Found {len(csv_files)} CSV files to import")
        
        for csv_file in csv_files:
            try:
                self._import_csv_file(str(csv_file))
                print(f"✅ Imported CSV: {csv_file.name}")
            except Exception as e:
                print(f"❌ Failed to import {csv_file.name}: {e}")
                logger.exception(f"Detailed error for {csv_file.name}")
                self.errors += 1
    
    def import_json_files(self, json_dir: str):
        """Import JSON files from directory (for API customers)"""
        if not os.path.exists(json_dir):
            print(f"⚠️  JSON directory not found: {json_dir}")
            return
        
        json_files = list(Path(json_dir).glob("*.json"))
        if not json_files:
            print(f"📄 No JSON files found in {json_dir}")
            return
            
        print(f"📄 Found {len(json_files)} JSON files to import")
        
        for json_file in json_files:
            try:
                self._import_json_file(str(json_file))
                print(f"✅ Imported JSON: {json_file.name}")
            except Exception as e:
                print(f"❌ Failed to import {json_file.name}: {e}")
                logger.exception(f"Detailed error for {json_file.name}")
                self.errors += 1
    
    def _import_json_file(self, json_path: str):
        """Import single JSON file (API customer format)"""
        print(f"  🔍 Processing JSON file: {json_path}")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
       
        readings = []
        
        if 'readings' in data:
 
            readings = data['readings']
        elif isinstance(data, list):
 
            readings = data
        else:
            print(f"  ⚠️  Unknown JSON structure in {json_path}")
            return
        
        print(f"  📊 Found {len(readings)} readings in JSON file")
        
        batch = []
        for reading in readings:
            reading_data = self._parse_json_reading(reading)
            if reading_data:
                batch.append(reading_data)
            
  
            if len(batch) >= 500:
                self._insert_temperature_batch(batch)
                batch = []

        if batch:
            self._insert_temperature_batch(batch)
    
    def _parse_json_reading(self, reading):
        """Parse JSON reading to database format"""
        try:
            
            timestamp_str = reading.get('timestamp', '')
            if not timestamp_str:
                return None
            
          
            if timestamp_str.endswith('Z'):
                recorded_at = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif '+' in timestamp_str or timestamp_str.endswith('UTC'):
                recorded_at = datetime.fromisoformat(timestamp_str.replace('UTC', '+00:00'))
            else:
                recorded_at = datetime.fromisoformat(timestamp_str)
                if recorded_at.tzinfo is None:
                    recorded_at = recorded_at.replace(tzinfo=timezone.utc)
            
         
            temperature = reading.get('temperature')
            if temperature is not None:
                temperature = float(temperature)
            
            return {
                'customer_code': reading.get('customer_id', ''),
                'facility_code': reading.get('facility_id', ''),
                'unit_code': reading.get('unit_id', ''),
                'temperature': temperature,
                'temperature_unit': reading.get('temperature_unit', 'C'),
                'recorded_at': recorded_at,
                'sensor_id': reading.get('sensor_id'),
                'equipment_status': 'failure' if temperature is None else 'normal'
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse JSON reading: {e}")
            return None
    
    def _import_csv_file(self, csv_path: str):
        """Import single CSV file"""
        batch = []
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    reading_data = self._parse_csv_row(row)
                    if reading_data:
                        batch.append(reading_data)
                    
                    # Process in batches of 500
                    if len(batch) >= 500:
                        self._insert_temperature_batch(batch)
                        batch = []
                        
                except Exception as e:
                    logger.warning(f"Error parsing row {row_num} in {csv_path}: {e}")
        

        if batch:
            self._insert_temperature_batch(batch)
    
    def _parse_csv_row(self, row):
        """Parse CSV row to temperature reading data"""
        try:
      
            timestamp_str = row.get('timestamp', '')
            if not timestamp_str:
                return None
            
     
            try:
                if 'T' in timestamp_str:
                    recorded_at = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    recorded_at = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    recorded_at = recorded_at.replace(tzinfo=timezone.utc)
            except ValueError:
                logger.warning(f"Invalid timestamp: {timestamp_str}")
                return None
            
          
            temperature = None
            temp_str = row.get('temperature', '').strip()
            if temp_str and temp_str.lower() not in ['null', 'none', '', 'nan']:
                try:
                    temperature = float(temp_str)
                except ValueError:
                    temperature = None
            
            return {
                'customer_code': row.get('customer_id', ''),
                'facility_code': row.get('facility_id', ''),
                'unit_code': row.get('unit_id', ''),
                'temperature': temperature,
                'temperature_unit': row.get('degrees', row.get('temperature_unit', 'C')),
                'recorded_at': recorded_at,
                'sensor_id': row.get('sensor_id'),
                'equipment_status': 'failure' if temperature is None else 'normal'
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse row: {e}")
            return None
    
    def _insert_temperature_batch(self, batch):
        """Insert batch of temperature readings"""
        if not batch:
            return

        resolved_batch = []
        for reading in batch:
            ids = self._resolve_ids(reading)
            if ids:
                resolved_batch.append({
                    **reading,
                    **ids
                })
        
        if not resolved_batch:
            return
      
        insert_query = """
        INSERT INTO temperature_readings 
        (customer_id, facility_id, storage_unit_id, temperature, temperature_unit, 
         recorded_at, sensor_id, equipment_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        with self.db.connection.cursor() as cursor:
            for reading in resolved_batch:
                cursor.execute(insert_query, (
                    reading['customer_id'],
                    reading['facility_id'],
                    reading['storage_unit_id'],
                    reading['temperature'],
                    reading['temperature_unit'],
                    reading['recorded_at'],
                    reading.get('sensor_id'),
                    reading['equipment_status']
                ))
            
            self.db.connection.commit()
            self.readings_imported += len(resolved_batch)
    
    def _resolve_ids(self, reading):
        """Resolve customer/facility/unit codes to database IDs"""
        query = """
        SELECT c.id as customer_id, f.id as facility_id, su.id as storage_unit_id
        FROM customers c
        JOIN facilities f ON c.id = f.customer_id
        JOIN storage_units su ON f.id = su.facility_id
        WHERE c.customer_code = %s 
        AND f.facility_code = %s 
        AND su.unit_code = %s
        """
        
        result = self.db.execute_query(query, (
            reading['customer_code'],
            reading['facility_code'],
            reading['unit_code']
        ))
        
        if not result:
            return None
        
        return {
            'customer_id': result[0]['customer_id'],
            'facility_id': result[0]['facility_id'],
            'storage_unit_id': result[0]['storage_unit_id']
        }

def main():
    """Main import function"""
    print("📊 Importing Simulation Data to Database")
    print("=" * 45)
    
    try:
      
        db = DatabaseConnection()
        db.execute_query("SELECT 1")
        print("✅ Database connection successful")
        
    
        importer = SimulationDataImporter(db)

        customer_yaml = "simulation/config/generated_customers.yaml"
        if os.path.exists(customer_yaml):
            importer.import_customers_from_yaml(customer_yaml)
        else:
            print(f"⚠️  No customer YAML found at {customer_yaml}")
            print("Run: python -m simulation.cli generate-customers --count 5")
        
        
        csv_dirs = ["data/csv_files", "data/assignment/csv_files"]
        for csv_dir in csv_dirs:
            if os.path.exists(csv_dir):
                print(f"\n📄 Importing CSV files from {csv_dir}")
                importer.import_csv_files(csv_dir)
        
 
        json_dirs = [
            "data/assignment",
            "data/generated", 
            "data/api_data",
            "data" 
        ]
        for json_dir in json_dirs:
            if os.path.exists(json_dir):
                print(f"\n📋 Importing JSON files from {json_dir}")
                importer.import_json_files(json_dir)
   
        print(f"\n🔍 Searching for additional JSON files...")
        for root, dirs, files in os.walk("data"):
            for file in files:
                if file.endswith('.json') and 'customer_' in file:
                    json_path = os.path.join(root, file)
                    print(f"  📋 Found: {json_path}")
                    try:
                        importer._import_json_file(json_path)
                        print(f"  ✅ Imported: {file}")
                    except Exception as e:
                        print(f"  ❌ Failed: {file} - {e}")
                        importer.errors += 1
        
      
        print("\n" + "=" * 45)
        print("📊 IMPORT RESULTS")
        print("=" * 45)
        print(f"Customers created: {importer.customers_created}")
        print(f"Facilities created: {importer.facilities_created}")
        print(f"Storage units created: {importer.units_created}")
        print(f"Temperature readings: {importer.readings_imported}")
        print(f"Errors: {importer.errors}")
        
        if importer.errors > 0:
            print(f"⚠️  {importer.errors} errors occurred during import")
        else:
            print("✅ Import completed successfully!")
        

        result = db.execute_query("""
            SELECT 
                COUNT(DISTINCT c.id) as customers,
                COUNT(DISTINCT f.id) as facilities,
                COUNT(DISTINCT su.id) as units,
                COUNT(tr.id) as readings
            FROM customers c
            LEFT JOIN facilities f ON c.id = f.customer_id
            LEFT JOIN storage_units su ON f.id = su.facility_id
            LEFT JOIN temperature_readings tr ON su.id = tr.storage_unit_id
        """)
        
        if result:
            r = result[0]
            print(f"\n📊 DATABASE SUMMARY:")
            print(f"Total customers: {r['customers']}")
            print(f"Total facilities: {r['facilities']}")
            print(f"Total units: {r['units']}")
            print(f"Total readings: {r['readings']}")
        
     
        customers = db.execute_query("""
            SELECT 
                c.customer_code, 
                c.name as customer_name, 
                c.data_sharing_method,
                COUNT(DISTINCT f.id) as facilities,
                COUNT(DISTINCT su.id) as units,
                COUNT(tr.id) as readings
            FROM customers c
            LEFT JOIN facilities f ON c.id = f.customer_id
            LEFT JOIN storage_units su ON f.id = su.facility_id
            LEFT JOIN temperature_readings tr ON su.id = tr.storage_unit_id
            GROUP BY c.id, c.customer_code, c.name, c.data_sharing_method
            ORDER BY c.customer_code
        """)
        
        if customers:
            print(f"\n👥 CUSTOMER DETAILS:")
            for customer in customers:
                method_icon = "📄" if customer['data_sharing_method'] == 'csv' else "🔌"
                print(f"  {method_icon} {customer['customer_code']}: {customer['customer_name']} ({customer['data_sharing_method']}) - {customer['facilities']} facilities, {customer['units']} units, {customer['readings']} readings")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        logger.exception("Detailed import error")
        raise
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()