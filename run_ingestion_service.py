#!/usr/bin/env python3
"""
Script to run the data ingestion service
"""
import asyncio
import logging
import sys
from data_ingestion.main import main as ingestion_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

if __name__ == "__main__":
    print("--- Starting Data Ingestion Service ---")
    print("This service will periodically collect data from customer endpoints")
    print("and process it into the database.")
    print("")
    print("Press Ctrl+C to stop the service.")
    print("")
    
    try:
        asyncio.run(ingestion_main())
    except KeyboardInterrupt:
        print("\n--- Stopping Data Ingestion Service ---")