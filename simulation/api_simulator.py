# simulation/api_simulator.py
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random
import threading
import time

from .customer_generator import GeneratedCustomer  # Changed to relative import
from .enhanced_data_generator import EnhancedTemperatureGenerator, TemperatureReading  # Changed to relative import


class CustomerAPISimulator:
    def __init__(self, customer: GeneratedCustomer, port: int = 8001):
        self.customer = customer
        self.port = port
        self.app = FastAPI(
            title=f"{customer.name} Temperature API",
            description=f"Simulated temperature monitoring API for {customer.name}",
            version="1.0.0"
        )
        self.generator = EnhancedTemperatureGenerator()
        self.reading_cache = {}  # Cache recent readings
        self.is_running = False
        self.background_task = None
        
        self.setup_routes()
        self.start_background_data_generation()
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        def root():
            """API information endpoint"""
            return {
                "message": f"Temperature Monitoring API for {self.customer.name}",
                "customer_id": self.customer.id,
                "customer_name": self.customer.name,
                "data_sharing_method": self.customer.data_sharing_method,
                "facilities": len(self.customer.facilities),
                "total_units": sum(len(f.units) for f in self.customer.facilities),
                "api_frequency_minutes": self.customer.data_config.get('api_polling_frequency_minutes', 15),
                "endpoints": {
                    "current_readings": "/temperature/current",
                    "unit_reading": "/temperature/unit/{unit_id}",
                    "historical": "/temperature/historical",
                    "facilities": "/facilities",
                    "health": "/health"
                }
            }
        
        @self.app.get("/health")
        def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "customer": self.customer.id,
                "uptime_hours": self._get_uptime_hours(),
                "cached_readings": len(self.reading_cache)
            }
        
        @self.app.get("/temperature/current")
        def get_current_temperatures():
            """Get current temperature readings for all units"""
            
            readings = []
            current_time = datetime.now()
            
            for facility in self.customer.facilities:
                for unit in facility.units:
                    # Check cache first
                    cache_key = f"{facility.id}_{unit.id}"
                    
                    if cache_key in self.reading_cache:
                        cached_reading = self.reading_cache[cache_key]
                        # Use cached reading if it's recent (within data frequency)
                        cache_age = (current_time - cached_reading.timestamp).total_seconds()
                        if cache_age < unit.data_frequency:
                            readings.append(cached_reading.to_dict())
                            continue
                    
                    # Generate new reading
                    reading = self.generator.generate_reading(
                        self.customer, facility, unit, current_time
                    )
                    self.reading_cache[cache_key] = reading
                    readings.append(reading.to_dict())
            
            return {
                "customer": self.customer.id,
                "customer_name": self.customer.name,
                "timestamp": current_time.isoformat(),
                "readings_count": len(readings),
                "readings": readings
            }
        
        @self.app.get("/temperature/unit/{unit_id}")
        def get_unit_temperature(unit_id: str):
            """Get current temperature for a specific unit (Assignment format)"""
            
            # Find the unit
            target_unit = None
            target_facility = None
            
            for facility in self.customer.facilities:
                for unit in facility.units:
                    if unit.id == unit_id:
                        target_unit = unit
                        target_facility = facility
                        break
                if target_unit:
                    break
            
            if not target_unit:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Storage unit '{unit_id}' not found for customer {self.customer.id}"
                )
            
            # Generate reading
            reading = self.generator.generate_reading(
                self.customer, target_facility, target_unit, datetime.now()
            )
            
            # Return in assignment-specified format
            return {
                "customer": self.customer.id,
                "storage_room": target_unit.name or unit_id,
                "temp": int(reading.temperature) if reading.temperature is not None else None,
                "degrees": reading.temperature_unit
            }
        
        @self.app.get("/temperature/historical")
        def get_historical_temperatures(
            unit_id: Optional[str] = Query(None, description="Specific unit ID"),
            hours: int = Query(24, ge=1, le=168, description="Hours of historical data"),
            limit: int = Query(1000, ge=1, le=10000, description="Maximum number of readings")
        ):
            """Get historical temperature data"""
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            all_readings = []
            
            for facility in self.customer.facilities:
                for unit in facility.units:
                    # Skip if specific unit requested and this isn't it
                    if unit_id and unit.id != unit_id:
                        continue
                    
                    # Generate historical readings
                    current_time = start_time
                    unit_readings = []
                    
                    while current_time <= end_time and len(unit_readings) < limit:
                        reading = self.generator.generate_reading(
                            self.customer, facility, unit, current_time
                        )
                        unit_readings.append(reading.to_dict())
                        current_time += timedelta(seconds=unit.data_frequency)
                    
                    all_readings.extend(unit_readings)
            
            # Sort by timestamp and apply limit
            all_readings.sort(key=lambda x: x['timestamp'], reverse=True)
            all_readings = all_readings[:limit]
            
            return {
                "customer": self.customer.id,
                "unit_id": unit_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "readings_count": len(all_readings),
                "readings": all_readings
            }
        
        @self.app.get("/facilities")
        def get_facilities():
            """Get facility and unit information"""
            
            facilities_data = []
            for facility in self.customer.facilities:
                units_data = []
                for unit in facility.units:
                    units_data.append({
                        "id": unit.id,
                        "name": unit.name,
                        "size": unit.size,
                        "size_unit": unit.size_unit,
                        "set_temperature": unit.set_temperature,
                        "temperature_unit": unit.temperature_unit,
                        "data_frequency": unit.data_frequency,
                        "data_quality": unit.data_quality
                    })
                
                facilities_data.append({
                    "id": facility.id,
                    "name": facility.name,
                    "city": facility.city,
                    "country": facility.country,
                    "units": units_data
                })
            
            return {
                "customer": self.customer.id,
                "customer_name": self.customer.name,
                "facilities": facilities_data
            }
        
        @self.app.post("/temperature/readings")
        def submit_temperature_readings(readings: List[Dict[str, Any]]):
            """Accept temperature readings (for testing reverse data flow)"""
            
            # Validate readings
            valid_readings = []
            for reading in readings:
                if self._validate_reading(reading):
                    valid_readings.append(reading)
            
            return {
                "status": "success",
                "customer": self.customer.id,
                "submitted": len(readings),
                "accepted": len(valid_readings),
                "rejected": len(readings) - len(valid_readings)
            }
        
        @self.app.get("/simulate/fault/{unit_id}")
        def simulate_equipment_fault(unit_id: str, duration_minutes: int = 30):
            """Simulate equipment fault for testing"""
            
            # This would trigger fault simulation in the generator
            # For now, just return success
            return {
                "status": "fault_simulated",
                "unit_id": unit_id,
                "duration_minutes": duration_minutes,
                "message": f"Simulating equipment fault for {duration_minutes} minutes"
            }
    
    def _validate_reading(self, reading: Dict[str, Any]) -> bool:
        """Validate a temperature reading"""
        required_fields = ['customer_id', 'unit_id', 'temperature', 'temperature_unit', 'timestamp']
        return all(field in reading for field in required_fields)
    
    def _get_uptime_hours(self) -> float:
        """Get API uptime in hours"""
        if hasattr(self, 'start_time'):
            return (datetime.now() - self.start_time).total_seconds() / 3600
        return 0.0
    
    def start_background_data_generation(self):
        """Start background task to periodically update cached readings"""
        
        async def update_cache():
            while self.is_running:
                try:
                    current_time = datetime.now()
                    
                    for facility in self.customer.facilities:
                        for unit in facility.units:
                            cache_key = f"{facility.id}_{unit.id}"
                            
                            # Check if we need to update this unit's cache
                            if cache_key in self.reading_cache:
                                last_reading = self.reading_cache[cache_key]
                                time_since_last = (current_time - last_reading.timestamp).total_seconds()
                                
                                if time_since_last >= unit.data_frequency:
                                    # Time to generate new reading
                                    new_reading = self.generator.generate_reading(
                                        self.customer, facility, unit, current_time
                                    )
                                    self.reading_cache[cache_key] = new_reading
                            else:
                                # No cached reading, generate one
                                reading = self.generator.generate_reading(
                                    self.customer, facility, unit, current_time
                                )
                                self.reading_cache[cache_key] = reading
                    
                    # Sleep for a minute before next update
                    await asyncio.sleep(60)
                    
                except Exception as e:
                    print(f"Error in background data generation: {e}")
                    await asyncio.sleep(60)
        
        # Start background task
        self.background_task = asyncio.create_task(update_cache())
    
    async def start_server(self):
        """Start the API server"""
        self.is_running = True
        self.start_time = datetime.now()
        
        print(f"🚀 Starting API server for {self.customer.name}")
        print(f"   🏢 Customer: {self.customer.id}")
        print(f"   🌡️  Units: {sum(len(f.units) for f in self.customer.facilities)}")
        print(f"   🔗 URL: http://localhost:{self.port}")
        print(f"   📡 Update frequency: {self.customer.data_config.get('api_polling_frequency_minutes', 15)} minutes")
        
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def stop(self):
        """Stop the API server"""
        self.is_running = False
        if self.background_task:
            self.background_task.cancel()

class MultiCustomerAPIManager:
    """Manage multiple customer API simulators"""
    
    def __init__(self, starting_port: int = 8001):
        self.starting_port = starting_port
        self.simulators = {}
        self.running_servers = []
    
    def add_customer(self, customer: GeneratedCustomer) -> int:
        """Add a customer API simulator"""
        
        if customer.data_sharing_method != 'api':
            raise ValueError(f"Customer {customer.id} does not use API method")
        
        port = self.starting_port + len(self.simulators)
        simulator = CustomerAPISimulator(customer, port)
        self.simulators[customer.id] = simulator
        
        return port
    
    async def start_all_servers(self):
        """Start all customer API servers"""
        
        tasks = []
        for customer_id, simulator in self.simulators.items():
            task = asyncio.create_task(simulator.start_server())
            tasks.append(task)
            self.running_servers.append((customer_id, simulator.port))
        
        print(f"🌐 Started {len(tasks)} API servers:")
        for customer_id, port in self.running_servers:
            print(f"   {customer_id}: http://localhost:{port}")
        
        # Wait for all servers to complete
        await asyncio.gather(*tasks)
    
    def stop_all_servers(self):
        """Stop all API servers"""
        for simulator in self.simulators.values():
            simulator.stop()
        
        self.running_servers.clear()
        print("🛑 All API servers stopped")
    
    def get_server_info(self) -> List[Dict[str, Any]]:
        """Get information about running servers"""
        
        server_info = []
        for customer_id, port in self.running_servers:
            simulator = self.simulators[customer_id]
            server_info.append({
                "customer_id": customer_id,
                "customer_name": simulator.customer.name,
                "port": port,
                "url": f"http://localhost:{port}",
                "facilities": len(simulator.customer.facilities),
                "units": sum(len(f.units) for f in simulator.customer.facilities)
            })
        
        return server_info

# Standalone function for simple API server startup
def start_single_api_server(customer: GeneratedCustomer, port: int = 8001):
    """Start a single API server for a customer"""
    
    async def run_server():
        simulator = CustomerAPISimulator(customer, port)
        await simulator.start_server()
    
    asyncio.run(run_server())

# CLI integration function
def start_multiple_api_servers(customers: List[GeneratedCustomer], starting_port: int = 8001):
    """Start multiple API servers for customers"""
    
    async def run_servers():
        manager = MultiCustomerAPIManager(starting_port)
        
        # Add all API customers
        api_customers = [c for c in customers if c.data_sharing_method == 'api']
        
        for customer in api_customers:
            port = manager.add_customer(customer)
            print(f"📋 Added {customer.name} on port {port}")
        
        if api_customers:
            await manager.start_all_servers()
        else:
            print("❌ No API customers found")
    
    asyncio.run(run_servers())