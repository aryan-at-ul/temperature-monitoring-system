# scripts/test_database_queries.py
#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import DatabaseConnection
from database.repositories.customer_repository import CustomerRepository
from database.repositories.temperature_repository import TemperatureRepository

def test_database_operations():
    """Test database operations with sample queries"""
    
    print("🧪 Testing Database Operations")
    print("=" * 40)
    
    db = DatabaseConnection()
    customer_repo = CustomerRepository(db)
    temp_repo = TemperatureRepository(db)
    
    try:
        # Test 1: Get all customers
        print("\n1️⃣ Testing customer queries...")
        customers = customer_repo.get_all_customers()
        print(f"Found {len(customers)} customers:")
        for customer in customers:
            print(f"  📋 {customer.customer_code}: {customer.name} ({customer.data_sharing_method})")
        
        if not customers:
            print("ℹ️  No customers found. Run import script first.")
            return
        
        # Test 2: Get customer with facilities
        test_customer_code = customers[0].customer_code
        print(f"\n2️⃣ Testing detailed customer query for '{test_customer_code}'...")
        detailed_customer = customer_repo.get_customer_with_facilities(test_customer_code)
        
        if detailed_customer:
            print(f"Customer: {detailed_customer.name}")
            print(f"Facilities: {len(detailed_customer.facilities)}")
            total_units = sum(len(f.storage_units) for f in detailed_customer.facilities)
            print(f"Total storage units: {total_units}")
            
            # Show facility details
            for facility in detailed_customer.facilities:
                print(f"  🏢 {facility.facility_code}: {facility.name or 'Unnamed'}")
                print(f"     Location: {facility.location_string}")
                print(f"     Units: {len(facility.storage_units)}")
                
                for unit in facility.storage_units[:3]:  # Show first 3 units
                    print(f"       ❄️  {unit.unit_code}: {unit.display_name}")
                    print(f"          Target: {unit.target_temp_display}, Size: {unit.size_display}")
                
                if len(facility.storage_units) > 3:
                    print(f"       ... and {len(facility.storage_units) - 3} more units")
        
        # Test 3: Temperature readings
        print(f"\n3️⃣ Testing temperature readings for '{test_customer_code}'...")
        recent_readings = temp_repo.get_latest_readings_by_customer(test_customer_code, limit=10)
        print(f"Found {len(recent_readings)} recent readings:")
        
        for reading in recent_readings[:5]:  # Show first 5
            print(f"  🌡️  {reading.recorded_at}: {reading.temperature_display}")
            print(f"      Status: {reading.equipment_status}, Quality: {reading.quality_score}")
        
        if len(recent_readings) > 5:
            print(f"  ... and {len(recent_readings) - 5} more readings")
        
        # Test 4: Equipment failures
        print(f"\n4️⃣ Testing equipment failure detection...")
        failures = temp_repo.get_equipment_failures(customer_code=test_customer_code, hours=24)
        print(f"Found {len(failures)} equipment failures in last 24 hours:")
        
        for failure in failures[:3]:  # Show first 3
            print(f"  ⚠️  {failure['occurred_at']}: {failure['customer_code']}/{failure['unit_code']}")
            print(f"      Status: {failure['status']}")
        
        if len(failures) > 3:
            print(f"  ... and {len(failures) - 3} more failures")
        
        # Test 5: Statistics
        print(f"\n5️⃣ Testing temperature statistics...")
        stats = temp_repo.get_temperature_statistics(test_customer_code, hours=24)
        
        if stats:
            print(f"Statistics for {test_customer_code} (last 24 hours):")
            print(f"  📊 Total readings: {stats['total_readings']}")
            print(f"  ✅ Valid readings: {stats['valid_readings']}")
            print(f"  ❌ Failed readings: {stats['failed_readings']}")
            print(f"  📈 Failure rate: {stats['failure_rate']:.1f}%")
            print(f"  🌡️  Avg temperature: {stats['avg_temperature_celsius']:.1f}°C" if stats['avg_temperature_celsius'] else "N/A")
            print(f"  📉 Min temperature: {stats['min_temperature_celsius']:.1f}°C" if stats['min_temperature_celsius'] else "N/A")
            print(f"  📈 Max temperature: {stats['max_temperature_celsius']:.1f}°C" if stats['max_temperature_celsius'] else "N/A")
            print(f"  🏠 Active units: {stats['active_units']}")
        
        # Test 6: Direct SQL queries
        print(f"\n6️⃣ Testing direct SQL queries...")
        
        # Latest readings view
        latest_view = db.execute_query("""
            SELECT customer_code, unit_code, temperature, temperature_unit, recorded_at
            FROM latest_temperature_readings 
            LIMIT 5
        """)
        
        print(f"Latest readings view ({len(latest_view)} samples):")
        for row in latest_view:
            temp_display = f"{row['temperature']:.1f}°{row['temperature_unit']}" if row['temperature'] else "N/A"
            print(f"  📋 {row['customer_code']}/{row['unit_code']}: {temp_display} at {row['recorded_at']}")
        
        # Customer summary view
        summary_view = db.execute_query("SELECT * FROM customer_summary")
        print(f"\nCustomer summary view:")
        for row in summary_view:
            print(f"  📊 {row['customer_code']}: {row['facility_count']} facilities, {row['unit_count']} units, {row['total_readings']} readings")
        
        print("\n" + "=" * 40)
        print("✅ All database tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        raise
    finally:
        db.disconnect()

if __name__ == "__main__":
    test_database_operations()