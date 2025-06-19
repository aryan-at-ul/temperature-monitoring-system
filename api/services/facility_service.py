# api/services/facility_service.py
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import logging
from database.connection import db

logger = logging.getLogger(__name__)

class FacilityService:
    @classmethod
    async def get_facilities(cls, customer_id: UUID, limit: int = 100, offset: int = 0):
        """
        Get facilities for a customer.
        """
        # Build the query
        sql_query = """
            SELECT * 
            FROM facilities
            WHERE customer_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        # Execute the query
        facilities = await db.fetch(sql_query, str(customer_id), limit, offset)
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as count
            FROM facilities
            WHERE customer_id = $1
        """
        count_result = await db.fetchrow(count_query, str(customer_id))
        total = count_result['count'] if count_result else 0
        
        return facilities, total
    
    @classmethod
    async def get_facility(cls, facility_id: UUID, customer_id: UUID):
        """
        Get a specific facility.
        """
        query = """
            SELECT * 
            FROM facilities
            WHERE id = $1 AND customer_id = $2
        """
        
        facility = await db.fetchrow(query, str(facility_id), str(customer_id))
        return facility
    
    @classmethod
    async def get_storage_units(cls, facility_id: UUID, customer_id: UUID, limit: int = 100, offset: int = 0):
        """
        Get storage units for a facility.
        """
        # First, verify the facility belongs to the customer
        facility_query = """
            SELECT id FROM facilities WHERE id = $1 AND customer_id = $2
        """
        facility = await db.fetchrow(facility_query, str(facility_id), str(customer_id))
        
        if not facility:
            return None, 0
        
        # Get storage units
        sql_query = """
            SELECT su.*, 
                (
                    SELECT tr.temperature 
                    FROM temperature_readings tr 
                    WHERE tr.storage_unit_id = su.id 
                    ORDER BY tr.recorded_at DESC 
                    LIMIT 1
                ) as current_temperature,
                (
                    SELECT tr.temperature_unit 
                    FROM temperature_readings tr 
                    WHERE tr.storage_unit_id = su.id 
                    ORDER BY tr.recorded_at DESC 
                    LIMIT 1
                ) as current_temperature_unit,
                (
                    SELECT tr.equipment_status 
                    FROM temperature_readings tr 
                    WHERE tr.storage_unit_id = su.id 
                    ORDER BY tr.recorded_at DESC 
                    LIMIT 1
                ) as temperature_status,
                (
                    SELECT tr.recorded_at 
                    FROM temperature_readings tr 
                    WHERE tr.storage_unit_id = su.id 
                    ORDER BY tr.recorded_at DESC 
                    LIMIT 1
                ) as last_reading_time
            FROM storage_units su
            WHERE su.facility_id = $1
            ORDER BY su.created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        # Execute the query
        units = await db.fetch(sql_query, str(facility_id), limit, offset)
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as count
            FROM storage_units
            WHERE facility_id = $1
        """
        count_result = await db.fetchrow(count_query, str(facility_id))
        total = count_result['count'] if count_result else 0
        
        return units, total
    
    @classmethod
    async def get_facility_with_units(cls, facility_id: UUID, customer_id: UUID):
        """
        Get a facility with all its storage units and temperature statistics.
        """
        # Get the facility
        facility = await cls.get_facility(facility_id, customer_id)
        
        if not facility:
            return None
        
        # Get all storage units for the facility
        units, _ = await cls.get_storage_units(facility_id, customer_id, limit=1000, offset=0)
        
        # Get temperature statistics for the facility
        stats_query = """
            SELECT 
                AVG(temperature) as avg_temperature,
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature
            FROM temperature_readings
            WHERE facility_id = $1
        """
        stats = await db.fetchrow(stats_query, str(facility_id))
        
        # Combine the results
        result = dict(facility)
        result['units'] = units if units else []
        result['unit_count'] = len(units) if units else 0
        result['average_temperature'] = stats['avg_temperature'] if stats else None
        result['min_temperature'] = stats['min_temperature'] if stats else None
        result['max_temperature'] = stats['max_temperature'] if stats else None
        
        return result
    
    @classmethod
    async def create_facility(cls, facility_data):
        """
        Create a new facility.
        """
        insert_query = """
            INSERT INTO facilities (
                customer_id, facility_code, name, city, country, 
                latitude, longitude, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            RETURNING *
        """
        
        result = await db.fetchrow(
            insert_query,
            str(facility_data.customer_id),
            facility_data.facility_code,
            facility_data.name,
            facility_data.city,
            facility_data.country,
            facility_data.latitude,
            facility_data.longitude
        )
        
        return result
    
    @classmethod
    async def update_facility(cls, facility_id: UUID, customer_id: UUID, facility_data):
        """
        Update a facility.
        """
        # Build the query dynamically based on the provided fields
        update_fields = []
        params = []
        
        if facility_data.name is not None:
            update_fields.append(f"name = ${len(params) + 1}")
            params.append(facility_data.name)
            
        if facility_data.city is not None:
            update_fields.append(f"city = ${len(params) + 1}")
            params.append(facility_data.city)
            
        if facility_data.country is not None:
            update_fields.append(f"country = ${len(params) + 1}")
            params.append(facility_data.country)
            
        if facility_data.latitude is not None:
            update_fields.append(f"latitude = ${len(params) + 1}")
            params.append(facility_data.latitude)
            
        if facility_data.longitude is not None:
            update_fields.append(f"longitude = ${len(params) + 1}")
            params.append(facility_data.longitude)
        
        # If no fields to update, return the current facility
        if not update_fields:
            return await cls.get_facility(facility_id, customer_id)
        
        # Add facility_id and customer_id to params
        params.extend([str(facility_id), str(customer_id)])
        
        update_query = f"""
            UPDATE facilities
            SET {", ".join(update_fields)}
            WHERE id = ${len(params) - 1} AND customer_id = ${len(params)}
            RETURNING *
        """
        
        result = await db.fetchrow(update_query, *params)
        return result
    
    @classmethod
    async def create_storage_unit(cls, unit_data):
        """
        Create a new storage unit.
        """
        # First, verify the facility exists
        facility_query = "SELECT id FROM facilities WHERE id = $1"
        facility = await db.fetchrow(facility_query, str(unit_data.facility_id))
        
        if not facility:
            raise ValueError("Facility not found")
        
        insert_query = """
            INSERT INTO storage_units (
                facility_id, unit_code, name, size_value, size_unit,
                set_temperature, temperature_unit, equipment_type, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            RETURNING *
        """
        
        result = await db.fetchrow(
            insert_query,
            str(unit_data.facility_id),
            unit_data.unit_code,
            unit_data.name,
            unit_data.size_value,
            unit_data.size_unit,
            unit_data.set_temperature,
            unit_data.temperature_unit,
            unit_data.equipment_type
        )
        
        return result
    
    @classmethod
    async def update_storage_unit(cls, unit_id: UUID, customer_id: UUID, unit_data):
        """
        Update a storage unit.
        """
        # First, verify the unit belongs to the customer
        verify_query = """
            SELECT su.id
            FROM storage_units su
            JOIN facilities f ON su.facility_id = f.id
            WHERE su.id = $1 AND f.customer_id = $2
        """
        unit = await db.fetchrow(verify_query, str(unit_id), str(customer_id))
        
        if not unit:
            return None
        
        # Build the query dynamically based on the provided fields
        update_fields = []
        params = []
        
        if unit_data.name is not None:
            update_fields.append(f"name = ${len(params) + 1}")
            params.append(unit_data.name)
            
        if unit_data.size_value is not None:
            update_fields.append(f"size_value = ${len(params) + 1}")
            params.append(unit_data.size_value)
            
        if unit_data.size_unit is not None:
            update_fields.append(f"size_unit = ${len(params) + 1}")
            params.append(unit_data.size_unit)
            
        if unit_data.set_temperature is not None:
            update_fields.append(f"set_temperature = ${len(params) + 1}")
            params.append(unit_data.set_temperature)
            
        if unit_data.temperature_unit is not None:
            update_fields.append(f"temperature_unit = ${len(params) + 1}")
            params.append(unit_data.temperature_unit)
            
        if unit_data.equipment_type is not None:
            update_fields.append(f"equipment_type = ${len(params) + 1}")
            params.append(unit_data.equipment_type)
        
        # If no fields to update, return the current unit
        if not update_fields:
            get_query = "SELECT * FROM storage_units WHERE id = $1"
            return await db.fetchrow(get_query, str(unit_id))
        
        # Add unit_id to params
        params.append(str(unit_id))
        
        update_query = f"""
            UPDATE storage_units
            SET {", ".join(update_fields)}
            WHERE id = ${len(params)}
            RETURNING *
        """
        
        result = await db.fetchrow(update_query, *params)
        return result