#!/usr/bin/env python3
import asyncio
import argparse
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


async def clean_temperature_readings(delete_all=False):
    """
    Clean the temperature_readings table
    
    Args:
        delete_all: If True, delete all records. Otherwise, keep records older than 1 hour.
    """
    try:
        
        await db.connect()
        
        if delete_all:
            
            query = "DELETE FROM public.temperature_readings"
            result = await db.execute(query)
            
            
            count = int(result.split(" ")[1]) if result else 0
            
            logger.info(f"Deleted all {count} records from temperature_readings table")
        else:
            
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            query = "DELETE FROM public.temperature_readings WHERE created_at > $1"
            result = await db.execute(query, cutoff_time)
            
            
            count = int(result.split(" ")[1]) if result else 0
            
            logger.info(f"Deleted {count} records newer than {cutoff_time} from temperature_readings table")
            
     
        count_query = "SELECT COUNT(*) FROM public.temperature_readings"
        remaining = await db.fetchval(count_query)
        
        logger.info(f"Remaining records in temperature_readings table: {remaining}")
        
    except Exception as e:
        logger.error(f"Error cleaning temperature_readings table: {e}", exc_info=True)
        
    finally:
  
        await db.close()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean the temperature_readings table for testing")
    parser.add_argument("--all", action="store_true", help="Delete all records (default is to keep records older than 1 hour)")
    
    args = parser.parse_args()
    
    print(f"--- Cleaning Temperature Readings Table ---")
    if args.all:
        print("Mode: Delete ALL records")
    else:
        print("Mode: Delete records newer than 1 hour")
    print("")
    
    asyncio.run(clean_temperature_readings(args.all))
