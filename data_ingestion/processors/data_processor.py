import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from database.models.models import DataEvent
from database.repositories.repositories import (
    CustomerRepository, FacilityRepository, StorageUnitRepository
)
from data_ingestion.queue.rabbitmq_client import rabbitmq
from database.connection import db

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process raw data into events for the queue"""

    def __init__(self):
        self.facility_cache = {}  # Cache for facility lookups by code
        self.unit_cache = {}      # Cache for storage unit lookups by code

    async def load_mapping_data(self, customer_id: str):
        """Load facility and storage unit mapping data for a customer"""
        # Get facilities for this customer
        facilities_query = """
            SELECT id, facility_code 
            FROM public.facilities 
            WHERE customer_id = $1
        """
        facilities = await db.fetch(facilities_query, customer_id)
        
        # Build facility code to ID mapping
        self.facility_cache[customer_id] = {
            f['facility_code']: f['id'] for f in facilities
        }
        
        # Get storage units for all facilities
        for facility in facilities:
            facility_id = facility['id']
            
            units_query = """
                SELECT id, unit_code 
                FROM public.storage_units 
                WHERE facility_id = $1
            """
            units = await db.fetch(units_query, facility_id)
            
            # Build unit code to ID mapping
            self.unit_cache[facility_id] = {
                u['unit_code']: u['id'] for u in units
            }
        
        logger.info(f"Loaded mapping data for customer {customer_id}: " 
                   f"{len(self.facility_cache.get(customer_id, {}))} facilities, "
                   f"{sum(len(units) for units in self.unit_cache.values())} storage units")

    async def process_api_readings(self, customer_id: str, readings: List[Dict[str, Any]]) -> int:
        """
        Process API readings into events
        
        Args:
            customer_id: The customer ID
            readings: List of raw readings from the API
            
        Returns:
            Number of events successfully processed and queued
        """
        if not readings:
            return 0
        
        # Load mapping data if not already cached
        if customer_id not in self.facility_cache:
            await self.load_mapping_data(customer_id)
        
        events_processed = 0
        facility_cache = self.facility_cache.get(customer_id, {})
        
        for reading in readings:
            try:
                # Get facility_code and unit_code from the reading
                facility_code = reading.get('facility_id')
                unit_code = reading.get('unit_id')
                
                if not facility_code or not unit_code:
                    logger.warning(f"Skipping reading without facility_id or unit_id: {reading}")
                    continue
                
                # Map facility code to facility ID
                facility_id = facility_cache.get(facility_code)
                if not facility_id:
                    logger.warning(f"Unknown facility code: {facility_code} for customer {customer_id}")
                    continue
                
                # Map unit code to unit ID
                unit_cache = self.unit_cache.get(facility_id, {})
                unit_id = unit_cache.get(unit_code)
                if not unit_id:
                    logger.warning(f"Unknown unit code: {unit_code} in facility {facility_code}")
                    continue
                
                # Create event with proper UUIDs
                event = {
                    'id': str(uuid.uuid4()),
                    'event_type': 'temperature_reading',
                    'customer_id': str(customer_id),
                    'facility_id': str(facility_id),
                    'unit_id': str(unit_id),
                    'data': reading,
                    'timestamp': datetime.now().isoformat(),
                    'processed': False
                }
                
                # Publish to queue
                routing_key = f"temperature.{customer_id}.{facility_id}.{unit_id}"
                await rabbitmq.publish(event, routing_key=routing_key)
                
                events_processed += 1
                
            except Exception as e:
                logger.error(f"Error processing reading: {e}", exc_info=True)
        
        return events_processed

    async def process_csv_readings(self, customer_id: str, readings: List[Dict[str, Any]]) -> int:
        """
        Process CSV readings into events
        
        Args:
            customer_id: The customer ID
            readings: List of raw readings from the CSV
            
        Returns:
            Number of events successfully processed and queued
        """
        if not readings:
            return 0
        
        # Load mapping data if not already cached
        if customer_id not in self.facility_cache:
            await self.load_mapping_data(customer_id)
        
        events_processed = 0
        facility_cache = self.facility_cache.get(customer_id, {})
        
        for reading in readings:
            try:
                # Extract facility and unit information from CSV
                facility_code = reading.get('facility_code') or reading.get('facility_id')
                unit_code = reading.get('unit_code') or reading.get('unit_id')
                
                if not facility_code or not unit_code:
                    logger.warning(f"Skipping CSV reading without facility_code or unit_code: {reading}")
                    continue
                
                # Map facility code to facility ID
                facility_id = facility_cache.get(facility_code)
                if not facility_id:
                    logger.warning(f"Unknown facility code: {facility_code} for customer {customer_id}")
                    continue
                
                # Map unit code to unit ID
                unit_cache = self.unit_cache.get(facility_id, {})
                unit_id = unit_cache.get(unit_code)
                if not unit_id:
                    logger.warning(f"Unknown unit code: {unit_code} in facility {facility_code}")
                    continue
                
                # Create event with proper UUIDs
                event = {
                    'id': str(uuid.uuid4()),
                    'event_type': 'temperature_reading',
                    'customer_id': str(customer_id),
                    'facility_id': str(facility_id),
                    'unit_id': str(unit_id),
                    'data': reading,
                    'timestamp': datetime.now().isoformat(),
                    'processed': False
                }
                
                # Publish to queue
                routing_key = f"temperature.{customer_id}.{facility_id}.{unit_id}"
                await rabbitmq.publish(event, routing_key=routing_key)
                
                events_processed += 1
                
            except Exception as e:
                logger.error(f"Error processing CSV reading: {e}", exc_info=True)
        
        return events_processed

    # def map_temperature_reading(self, event: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Map a data event to a temperature reading structure
        
    #     Args:
    #         event: The data event
            
    #     Returns:
    #         Mapped temperature reading data
    #     """
    #     data = event['data']
        
    #     # Extract timestamp
    #     timestamp_str = data.get('timestamp') or data.get('recorded_at') or data.get('reading_time')
        
    #     # Handle different timestamp formats or provide default
    #     try:
    #         if timestamp_str:
    #             timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    #         else:
    #             timestamp = datetime.now()
    #     except (ValueError, TypeError):
    #         logger.warning(f"Invalid timestamp format: {timestamp_str}, using current time")
    #         timestamp = datetime.now()
        
    #     # Safely convert temperature to float
    #     try:
    #         temp_value = data.get('temperature')
    #         if temp_value is None or temp_value == '':
    #             temperature = 0.0
    #         else:
    #             temperature = float(temp_value)
    #     except (ValueError, TypeError):
    #         logger.warning(f"Invalid temperature value: {data.get('temperature')}, using 0.0")
    #         temperature = 0.0
            
    #     # Safely convert quality score to float
    #     try:
    #         quality_score_value = data.get('quality_score')
    #         if quality_score_value is None or quality_score_value == '':
    #             quality_score = 1.0
    #         else:
    #             quality_score = float(quality_score_value)
    #     except (ValueError, TypeError):
    #         logger.warning(f"Invalid quality score value: {data.get('quality_score')}, using 1.0")
    #         quality_score = 1.0
        
    #     # Map to temperature reading structure
    #     reading = {
    #         'id': str(uuid.uuid4()),
    #         'customer_id': event['customer_id'],
    #         'facility_id': event['facility_id'],
    #         'storage_unit_id': event['unit_id'],
    #         'temperature': temperature,
    #         'temperature_unit': data.get('temperature_unit', 'C'),
    #         'recorded_at': timestamp,
    #         'sensor_id': data.get('sensor_id', ''),
    #         'quality_score': quality_score,
    #         'equipment_status': data.get('equipment_status', 'normal'),
    #         'created_at': datetime.now()
    #     }
        
    #     return reading

    def map_temperature_reading(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a data event to a temperature reading structure
        
        Args:
            event: The data event
            
        Returns:
            Mapped temperature reading data
        """
        data = event['data']
        
        # Extract timestamp
        timestamp_str = data.get('timestamp') or data.get('recorded_at') or data.get('reading_time')
        
        # Handle different timestamp formats or provide default
        try:
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
        except (ValueError, TypeError):
            logger.warning(f"Invalid timestamp format: {timestamp_str}, using current time")
            timestamp = datetime.now()
        
        # Safely convert temperature to float
        try:
            temp_value = data.get('temperature')
            if temp_value is None or temp_value == '':
                temperature = 0.0
            else:
                temperature = float(temp_value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid temperature value: {data.get('temperature')}, using 0.0")
            temperature = 0.0
            
        # Safely convert quality score to INTEGER, not float
        try:
            quality_score_value = data.get('quality_score')
            if quality_score_value is None or quality_score_value == '':
                quality_score = 1  # Integer, not 1.0
            else:
                # Convert to integer, not float
                quality_score = int(float(quality_score_value))  # Convert to float first if it's a string, then to int
        except (ValueError, TypeError):
            logger.warning(f"Invalid quality score value: {data.get('quality_score')}, using 1")
            quality_score = 1  # Integer, not 1.0
        
        # Map to temperature reading structure
        reading = {
            'id': str(uuid.uuid4()),
            'customer_id': event['customer_id'],
            'facility_id': event['facility_id'],
            'storage_unit_id': event['unit_id'],
            'temperature': temperature,
            'temperature_unit': data.get('temperature_unit', 'C'),
            'recorded_at': timestamp,
            'sensor_id': data.get('sensor_id', ''),
            'quality_score': quality_score,  # This will now be an integer
            'equipment_status': data.get('equipment_status', 'normal'),
            'created_at': datetime.now()
        }
        
        return reading