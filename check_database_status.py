#!/usr/bin/env python3
"""
Script to check the current state of the database tables
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta

from database.connection import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


async def check_database_status():
    """Check the current state of the database tables"""
    try:
        # Connect to the database
        await db.connect()
        
        # Count records in each table
        tables = [
            "customers", 
            "customer_tokens", 
            "facilities", 
            "storage_units", 
            "temperature_readings", 
            "ingestion_logs",
            "system_config"
        ]
        
        print("\n=== Database Status ===\n")
        
        for table in tables:
            count_query = f"SELECT COUNT(*) FROM public.{table}"
            count = await db.fetchval(count_query)
            print(f"{table}: {count} records")
        
        # Get recent temperature readings
        print("\n=== Recent Temperature Readings ===\n")
        recent_query = """
            SELECT 
                c.customer_code,
                f.facility_code,
                s.unit_code,
                tr.temperature,
                tr.temperature_unit,
                tr.recorded_at,
                tr.created_at
            FROM 
                public.temperature_readings tr
                JOIN public.customers c ON tr.customer_id = c.id
                JOIN public.facilities f ON tr.facility_id = f.id
                JOIN public.storage_units s ON tr.storage_unit_id = s.id
            ORDER BY 
                tr.created_at DESC
            LIMIT 5
        """
        recent = await db.fetch(recent_query)
        
        for row in recent:
            print(f"Customer: {row['customer_code']}, "
                  f"Facility: {row['facility_code']}, "
                  f"Unit: {row['unit_code']}, "
                  f"Temp: {row['temperature']}{row['temperature_unit']}, "
                  f"Recorded: {row['recorded_at']}, "
                  f"Ingested: {row['created_at']}")
        
        # Get recent ingestion logs
        print("\n=== Recent Ingestion Logs ===\n")
        logs_query = """
            SELECT 
                c.customer_code,
                il.ingestion_type,
                il.status,
                il.records_processed,
                il.records_succeeded,
                il.records_failed,
                il.start_time,
                il.end_time
            FROM 
                public.ingestion_logs il
                JOIN public.customers c ON il.customer_id = c.id
            ORDER BY 
                il.start_time DESC
            LIMIT 5
        """
        logs = await db.fetch(logs_query)
        
        for row in logs:
            duration = row['end_time'] - row['start_time'] if row['end_time'] else None
            duration_ms = duration.total_seconds() * 1000 if duration else 0
            
            print(f"Customer: {row['customer_code']}, "
                  f"Type: {row['ingestion_type']}, "
                  f"Status: {row['status']}, "
                  f"Processed: {row['records_processed']} "
                  f"(Success: {row['records_succeeded']}, Failed: {row['records_failed']}), "
                  f"Duration: {duration_ms:.2f}ms")
        
    except Exception as e:
        logger.error(f"Error checking database status: {e}", exc_info=True)
        
    finally:
        # Close database connection
        await db.close()
        

if __name__ == "__main__":
    print(f"--- Checking Database Status ---")
    asyncio.run(check_database_status())
