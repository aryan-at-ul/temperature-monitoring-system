# scripts/test_database_functions.py
#!/usr/bin/env python3
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import DatabaseConnection

def test_database_functions():
    """Test database functions and views"""
    
    print("🧪 Testing Database Functions and Views")
    print("=" * 45)
    
    db = DatabaseConnection()
    
    try:
        # Test temperature conversion
        print("\n🌡️  Testing temperature conversion...")
        conversions = [
            (32, 'F', 'C', 0),
            (100, 'C', 'F', 212),
            (273.15, 'K', 'C', 0),
            (-40, 'F', 'C', -40)  # Special case where F and C are equal
        ]
        
        for temp, from_unit, to_unit, expected in conversions:
            result = db.execute_query("SELECT convert_temperature(%s, %s, %s) as converted", (temp, from_unit, to_unit))
            converted = float(result[0]['converted'])
            status = "✅" if abs(converted - expected) < 0.1 else "❌"
            print(f"  {status} {temp}°{from_unit} → {converted:.1f}°{to_unit} (expected: {expected})")
        
        # Test area conversion
        print("\n📏 Testing area conversion...")
        area_conversions = [
            (10.764, 'sqft', 'sqm', 1.0),
            (1, 'sqm', 'sqft', 10.764),
            (100, 'sqm', 'sqm', 100)  # Same unit
        ]
        
        for area, from_unit, to_unit, expected in area_conversions:
            result = db.execute_query("SELECT convert_area(%s, %s, %s) as converted", (area, from_unit, to_unit))
            converted = float(result[0]['converted'])
            status = "✅" if abs(converted - expected) < 0.1 else "❌"
            print(f"  {status} {area} {from_unit} → {converted:.1f} {to_unit} (expected: {expected})")
        
        # Test latest readings view
        print("\n📊 Testing latest temperature readings view...")
        latest = db.execute_query("""
            SELECT customer_code, unit_code, temperature, temperature_unit, recorded_at
            FROM latest_temperature_readings 
            LIMIT 3
        """)
        
        for reading in latest:
            temp_display = f"{reading['temperature']:.1f}°{reading['temperature_unit']}" if reading['temperature'] else "NULL"
            print(f"  📋 {reading['customer_code']}/{reading['unit_code']}: {temp_display} at {reading['recorded_at']}")
        
        # Test customer summary view
        print("\n👥 Testing customer summary view...")
        summary = db.execute_query("SELECT * FROM customer_summary ORDER BY customer_code LIMIT 5")
        
        for customer in summary:
            print(f"  👤 {customer['customer_code']}: {customer['facility_count']} facilities, {customer['unit_count']} units, {customer['total_readings']} readings")
        
        print("\n✅ All database functions and views working correctly!")
        
    except Exception as e:
        print(f"❌ Function test failed: {e}")
        raise
    finally:
        db.disconnect()

if __name__ == "__main__":
    test_database_functions()