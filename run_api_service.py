#!/usr/bin/env python3
"""
Script to run the API service
"""
import uvicorn
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

if __name__ == "__main__":
    print("--- Starting Temperature Monitoring API Service ---")
    print("Documentation will be available at: http://localhost:8000/docs")
    print("")
    print("Press Ctrl+C to stop the service.")
    print("")
    
    try:
        uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n--- Stopping API Service ---")