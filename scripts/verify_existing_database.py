# scripts/verify_existing_database.py
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import DatabaseConnection, test_connection

def verify_existing_database():
    """Verify existing database setup"""
    
    print("🔍 Verifying Existing Temperature Database")
    print("=" * 45)
    
    # 1. Test connection
    print("\n1️⃣ Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed!")
        return False
    
    print("✅ Database connection successful!")
    
    db = DatabaseConnection()
    
    try:
        # 2. Check existing tables
        print("\n2️⃣ Checking existing tables...")
        tables = db.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        table_names = [row['table_name'] for row in tables]
        expected_tables = [
            'customers', 'facilities', 'storage_units', 
            'temperature_readings', 'customer_tokens', 
            'ingestion_logs', 'system_config'
        ]
        
        print(f"Found {len(table_names)} tables:")
        for table in table_names:
            if table.startswith('temperature_readings_history'):
                continue  # Skip partition tables for cleaner output
            status = "✅" if table in expected_tables else "📋"
            print(f"  {status} {table}")
        
        # Count partition tables
        partition_count = len([t for t in table_names if t.startswith('temperature_readings_history')])
        if partition_count > 0:
            print(f"  📅 {partition_count} history partitions")
        
        # 3. Check views
        print("\n3️⃣ Checking views...")
        views = db.execute_query("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        view_names = [row['table_name'] for row in views]
        expected_views = ['latest_temperature_readings', 'customer_summary']
        
        for view in expected_views:
            status = "✅" if view in view_names else "❌"
            print(f"  {status} {view}")
        
        # 4. Check data
        print("\n4️⃣ Checking existing data...")
        
        # Count existing records
        customer_count = db.execute_query("SELECT COUNT(*) as count FROM customers")[0]['count']
        facility_count = db.execute_query("SELECT COUNT(*) as count FROM facilities")[0]['count']
        unit_count = db.execute_query("SELECT COUNT(*) as count FROM storage_units")[0]['count']
        reading_count = db.execute_query("SELECT COUNT(*) as count FROM temperature_readings")[0]['count']
        
        print(f"📊 Current data:")
        print(f"  👥 Customers: {customer_count}")
        print(f"  🏢 Facilities: {facility_count}")
        print(f"  ❄️  Storage Units: {unit_count}")
        print(f"  🌡️  Temperature Readings: {reading_count}")
        
        # 5. Test functions if they exist
        print("\n5️⃣ Testing database functions...")
        try:
            # Test temperature conversion function
            result = db.execute_query("SELECT convert_temperature(32, 'F', 'C') as temp")
            if result:
                celsius_temp = float(result[0]['temp'])
                print(f"  ✅ Temperature conversion: 32°F = {celsius_temp:.1f}°C")
            else:
                print("  ❓ Temperature conversion function not found")
        except Exception as e:
            print(f"  ❓ Temperature conversion function not available: {e}")
        
        try:
            # Test area conversion function
            result = db.execute_query("SELECT convert_area(10.764, 'sqft', 'sqm') as area")
            if result:
                sqm_area = float(result[0]['area'])
                print(f"  ✅ Area conversion: 10.764 sqft = {sqm_area:.1f} sqm")
            else:
                print("  ❓ Area conversion function not found")
        except Exception as e:
            print(f"  ❓ Area conversion function not available: {e}")
        
        # 6. Summary
        print("\n" + "=" * 45)
        print("📋 VERIFICATION SUMMARY")
        print("=" * 45)
        
        required_tables_exist = all(table in table_names for table in expected_tables)
        required_views_exist = all(view in view_names for view in expected_views)
        
        if required_tables_exist:
            print("✅ All required tables exist")
        else:
            missing = set(expected_tables) - set(table_names)
            print(f"❌ Missing tables: {missing}")
        
        if required_views_exist:
            print("✅ All required views exist")
        else:
            missing = set(expected_views) - set(view_names)
            print(f"❌ Missing views: {missing}")
        
        if customer_count > 0:
            print("✅ Database has customer data")
        else:
            print("ℹ️  No customer data found - ready for import")
        
        if required_tables_exist and required_views_exist:
            print("\n🎉 Database is ready for data import!")
            print("\nNext steps:")
            print("1. Generate simulation data: python -m simulation.cli generate-customers --count 5")
            print("2. Import data: python scripts/import_simulation_data.py")
            return True
        else:
            print("\n⚠️  Database needs schema updates")
            return False
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        db.disconnect()

if __name__ == "__main__":
    success = verify_existing_database()
    sys.exit(0 if success else 1)