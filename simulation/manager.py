# simulation/manager.py
import asyncio
import pandas as pd
from fastapi import FastAPI, Response
from typing import List, Dict, Any
from datetime import datetime
import uvicorn

from .customer_generator import GeneratedCustomer
from .enhanced_data_generator import generate_customer_data

def create_customer_app(customer: GeneratedCustomer) -> FastAPI:
    """
    Factory function to create a FastAPI application for a single customer.
    The endpoints will vary based on the customer's data_sharing_method.
    """
    app = FastAPI(
        title=f"Simulation API for {customer.name}",
        description=f"Simulates on-demand data generation for {customer.name} ({customer.data_sharing_method} method).",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    @app.get("/", summary="Customer Information")
    def get_customer_info():
        """Returns basic information about the simulated customer at this port."""
        return {
            "customer_id": customer.id,
            "customer_name": customer.name,
            "data_sharing_method": customer.data_sharing_method,
            "total_facilities": len(customer.facilities),
            "total_units": sum(len(f.units) for f in customer.facilities),
            "data_endpoint": "/temperature/current" if customer.data_sharing_method == 'api' else "/data/download.csv"
        }

    if customer.data_sharing_method == 'api':
        # --- Endpoints for API-type customers ---
        @app.get("/temperature/current", summary="Get Current Temperature Data (JSON)")
        def get_current_temperatures(hours: float = 0.25):
            """
            Generates and returns the latest temperature readings for all units as JSON.
            The `hours` query parameter defines the lookback period for "current" data.
            """
            print(f"🔗 [API Request] Received request for JSON data from {customer.name} ({customer.id})")
            readings = generate_customer_data(customer, hours=hours) 
            return {
                "customer_id": customer.id,
                "generated_at": datetime.now().isoformat(),
                "reading_count": len(readings),
                "readings": [r.to_dict() for r in readings]
            }

    elif customer.data_sharing_method == 'csv':
        # --- Endpoint for CSV-type customers ---
        @app.get("/data/download.csv", summary="Download Temperature Data (CSV)")
        def download_csv_data(hours: int = 24):
            """
            Generates a CSV file with historical data and returns it for download.
            The `hours` query parameter defines how many hours of data to include.
            """
            print(f"📄 [CSV Request] Received request for CSV file from {customer.name} ({customer.id})")
            readings = generate_customer_data(customer, hours=hours)
            
            if not readings:
                return Response(content="No data generated for the requested period.", status_code=204)
            
            # Convert to DataFrame and then to a CSV string in memory
            df = pd.DataFrame([r.to_dict() for r in readings])
            csv_data = df.to_csv(index=False)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"customer_{customer.id}_data_{timestamp}.csv"
            
            headers = {
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
            
            return Response(content=csv_data, media_type='text/csv', headers=headers)

    return app


class SimulationManager:
    """
    Manages all customer simulations, running each as a dedicated FastAPI server.
    """
    def __init__(self, customers: List[GeneratedCustomer], port_start: int = 8001):
        self.servers = []
        port = port_start
        for customer in customers:
            app = create_customer_app(customer)
            config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
            server = uvicorn.Server(config)
            self.servers.append({
                "customer_id": customer.id,
                "name": customer.name,
                "type": customer.data_sharing_method,
                "port": port,
                "server": server
            })
            port += 1

    async def start(self):
        """Starts all configured simulation servers concurrently."""
        print("--- Starting Simulation Service ---")
        print("Each customer is running on a dedicated port. The ingestion service will call these endpoints.")
        
        server_tasks = []
        for server_info in self.servers:
            print(f"  -> ({server_info['type'].upper()}) {server_info['name']} ({server_info['customer_id']}) is starting on http://localhost:{server_info['port']}")
            server_tasks.append(server_info['server'].serve())
            
        if not server_tasks:
            print("No simulations to run. Exiting.")
            return
            
        print("\n--- Simulation Service is Running ---")
        print("Press CTRL+C to stop all servers gracefully.")
        await asyncio.gather(*server_tasks, return_exceptions=True)

    def stop(self):
        """Stops all running simulation servers."""
        print("\n--- Stopping Simulation Service ---")
        for server_info in self.servers:
            server_info['server'].should_exit = True
        print("--- Simulation Service Stopped ---")