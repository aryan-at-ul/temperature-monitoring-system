# scripts/setup_database.py
#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import DatabaseConnection, test_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Complete database setup"""
    
    print("🗄️ Temperature Monitoring System - Database Setup")
    print("=" * 55)
    
    # 1. Test connection
    print("\n1️⃣ Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed!")
        print("Make sure PostgreSQL is running and database 'temperature_monitoring' exists.")
        print("Run: createdb temperature_monitoring")
        return False
    
    # 2. Apply schema
    print("\n2️⃣ Applying database schema...")
    try:
        db = DatabaseConnection()
        schema_path = project_root / "database" / "schema.sql"
        
        if not schema_path.exists():
            print(f"❌ Schema file not found: {schema_path}")
            return False
        
        db.execute_script(str(schema_path))
        print("✅ Schema applied successfully")
        
    except Exception as e:
        print(f"❌ Schema application failed: {e}")
        return False
    
    # 3. Verify tables
    print("\n3️⃣ Verifying tables...")
    try:
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
            status = "✅" if table in expected_tables else "❓"
            print(f"  {status} {table}")
        
        missing_tables = set(expected_tables) - set(table_names)
        if missing_tables:
            print(f"⚠️  Missing tables: {missing_tables}")
        
    except Exception as e:
        print(f"❌ Table verification failed: {e}")
        return False
    
    print("\n✅ Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Generate simulation data: python -m simulation.cli generate-customers --count 5")
    print("2. Import data to database: python scripts/import_simulation_data.py")
    
    db.disconnect()
    return True

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)