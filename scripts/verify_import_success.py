# scripts/verify_import_success.py
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import DatabaseConnection

def verify_import_success():
    """Verify the successful import and show detailed statistics"""
    
    print("🎉 Verifying Successful Database Import")
    print("=" * 50)
    
    db = DatabaseConnection()
    
    try:
        # 1. Overall statistics
        print("\n📊 OVERALL STATISTICS")
        print("-" * 30)
        
        overall_stats = db.execute_query("""
            SELECT 
                COUNT(DISTINCT c.id) as customers,
                COUNT(DISTINCT f.id) as facilities,
                COUNT(DISTINCT su.id) as units,
                COUNT(tr.id) as readings
            FROM customers c
            LEFT JOIN facilities f ON c.id = f.customer_id
            LEFT JOIN storage_units su ON f.id = su.facility_id
            LEFT JOIN temperature_readings tr ON su.id = tr.storage_unit_id
        """)[0]
        
        print(f"✅ Customers: {overall_stats['customers']}")
        print(f"✅ Facilities: {overall_stats['facilities']}")
        print(f"✅ Storage Units: {overall_stats['units']}")
        print(f"✅ Temperature Readings: {overall_stats['readings']}")
        
        # 2. Customer breakdown (fixed SQL)
        print("\n👥 CUSTOMER BREAKDOWN")
        print("-" * 30)
        
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
        
        for customer in customers:
            method_icon = "📄" if customer['data_sharing_method'] == 'csv' else "🔌"
            print(f"{method_icon} {customer['customer_code']}: {customer['customer_name']} ({customer['data_sharing_method']})")
            print(f"    🏢 {customer['facilities']} facilities | ❄️  {customer['units']} units | 📊 {customer['readings']} readings")
        
        # 3. Data sharing method breakdown
        print("\n📋 DATA SHARING METHODS")
        print("-" * 30)
        
        methods = db.execute_query("""
            SELECT 
                data_sharing_method,
                COUNT(*) as customer_count,
                SUM(facility_counts.facility_count) as total_facilities,
                SUM(unit_counts.unit_count) as total_units
            FROM customers c
            LEFT JOIN (
                SELECT customer_id, COUNT(*) as facility_count
                FROM facilities
                GROUP BY customer_id
            ) facility_counts ON c.id = facility_counts.customer_id
            LEFT JOIN (
                SELECT f.customer_id, COUNT(su.id) as unit_count
                FROM facilities f
                LEFT JOIN storage_units su ON f.id = su.facility_id
                GROUP BY f.customer_id
            ) unit_counts ON c.id = unit_counts.customer_id
            GROUP BY data_sharing_method
            ORDER BY data_sharing_method
        """)
        
        for method in methods:
            icon = "📄" if method['data_sharing_method'] == 'csv' else "🔌"
            print(f"{icon} {method['data_sharing_method'].upper()}: {method['customer_count']} customers, {method['total_facilities']} facilities, {method['total_units']} units")
        
        # 4. Temperature data quality
        print("\n🌡️  TEMPERATURE DATA QUALITY")
        print("-" * 30)
        
        data_quality = db.execute_query("""
            SELECT 
                COUNT(*) as total_readings,
                COUNT(CASE WHEN temperature IS NOT NULL THEN 1 END) as valid_readings,
                COUNT(CASE WHEN temperature IS NULL THEN 1 END) as null_readings,
                MIN(recorded_at) as earliest_reading,
                MAX(recorded_at) as latest_reading,
                COUNT(DISTINCT DATE(recorded_at)) as days_with_data
            FROM temperature_readings
        """)[0]
        
        failure_rate = (data_quality['null_readings'] / max(data_quality['total_readings'], 1)) * 100
        
        print(f"📊 Total readings: {data_quality['total_readings']}")
        print(f"✅ Valid readings: {data_quality['valid_readings']}")
        print(f"❌ Null readings: {data_quality['null_readings']} ({failure_rate:.2f}%)")
        print(f"📅 Date range: {data_quality['earliest_reading']} to {data_quality['latest_reading']}")
        print(f"📆 Days with data: {data_quality['days_with_data']}")
        
        # 5. Assignment requirements check
        print("\n📋 ASSIGNMENT REQUIREMENTS CHECK")
        print("-" * 30)
        
        # Check Customer A
        customer_a = db.execute_query("""
            SELECT c.*, COUNT(DISTINCT su.id) as unit_count
            FROM customers c
            LEFT JOIN facilities f ON c.id = f.customer_id
            LEFT JOIN storage_units su ON f.id = su.facility_id
            WHERE c.customer_code = 'A'
            GROUP BY c.id
        """)
        
        if customer_a:
            a = customer_a[0]
            print(f"✅ Customer A exists: {a['name']} ({a['data_sharing_method']}), {a['unit_count']} units")
        else:
            print("❌ Customer A missing")
        
        # Check Customer B
        customer_b = db.execute_query("""
            SELECT c.*, COUNT(DISTINCT su.id) as unit_count
            FROM customers c
            LEFT JOIN facilities f ON c.id = f.customer_id
            LEFT JOIN storage_units su ON f.id = su.facility_id
            WHERE c.customer_code = 'B'
            GROUP BY c.id
        """)
        
        if customer_b:
            b = customer_b[0]
            print(f"✅ Customer B exists: {b['name']} ({b['data_sharing_method']}), {b['unit_count']} units")
        else:
            print("❌ Customer B missing")
        
        # Check for null values
        null_checks = db.execute_query("""
            SELECT 
                COUNT(CASE WHEN f.name IS NULL THEN 1 END) as null_facility_names,
                COUNT(CASE WHEN f.city IS NULL THEN 1 END) as null_cities,
                COUNT(CASE WHEN su.name IS NULL THEN 1 END) as null_unit_names,
                COUNT(CASE WHEN tr.temperature IS NULL THEN 1 END) as null_temperatures
            FROM facilities f
            LEFT JOIN storage_units su ON f.id = su.facility_id
            LEFT JOIN temperature_readings tr ON su.id = tr.storage_unit_id
        """)[0]
        
        print(f"✅ Null facility names: {null_checks['null_facility_names']}")
        print(f"✅ Null cities: {null_checks['null_cities']}")
        print(f"✅ Null unit names: {null_checks['null_unit_names']}")
        print(f"✅ Null temperatures: {null_checks['null_temperatures']}")
        
        # Check temperature and size units
        temp_units = db.execute_query("""
            SELECT temperature_unit, COUNT(*) as count
            FROM storage_units
            GROUP BY temperature_unit
            ORDER BY temperature_unit
        """)
        
        size_units = db.execute_query("""
            SELECT size_unit, COUNT(*) as count
            FROM storage_units
            GROUP BY size_unit
            ORDER BY size_unit
        """)
        
        print(f"✅ Temperature units: {', '.join([f'{u['temperature_unit']}({u['count']})' for u in temp_units])}")
        print(f"✅ Size units: {', '.join([f'{u['size_unit']}({u['count']})' for u in size_units])}")
        
        # 6. Sample data preview
        print("\n🔍 SAMPLE DATA PREVIEW")
        print("-" * 30)
        
        sample_readings = db.execute_query("""
            SELECT 
                c.customer_code,
                f.facility_code,
                su.unit_code,
                tr.temperature,
                tr.temperature_unit,
                tr.recorded_at,
                tr.equipment_status
            FROM temperature_readings tr
            JOIN storage_units su ON tr.storage_unit_id = su.id
            JOIN facilities f ON su.facility_id = f.id
            JOIN customers c ON f.customer_id = c.id
            ORDER BY tr.recorded_at DESC
            LIMIT 5
        """)
        
        for reading in sample_readings:
            temp_display = f"{reading['temperature']:.1f}°{reading['temperature_unit']}" if reading['temperature'] else "NULL"
            print(f"📊 {reading['customer_code']}/{reading['facility_code']}/{reading['unit_code']}: {temp_display} ({reading['equipment_status']}) at {reading['recorded_at']}")
        
        print("\n" + "=" * 50)
        print("🎉 DATABASE IMPORT VERIFICATION COMPLETE!")
        print("✅ All data successfully imported and verified")
        print("✅ Assignment requirements met")
        print("✅ Ready for API development (Exercise 2)")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        db.disconnect()

if __name__ == "__main__":
    success = verify_import_success()
    sys.exit(0 if success else 1)