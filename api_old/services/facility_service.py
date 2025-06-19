import logging
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime

from database.connection import db
from api.models.customer import AuthenticatedCustomer
from api.models.facility import (
    FacilityResponse, StorageUnitResponse, FacilityWithUnits,
    CustomerFacilities
)

logger = logging.getLogger(__name__)


class FacilityService:
    """Service for facility-related operations"""
    
    @staticmethod
    async def get_customer_facilities(customer_id: str) -> List[FacilityResponse]:
        """
        Get all facilities for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            List of facilities
        """
        query = """
            SELECT 
                id, customer_id, facility_code, name, city, country,
                latitude, longitude, created_at
            FROM 
                public.facilities
            WHERE 
                customer_id = $1
            ORDER BY 
                facility_code
        """
        
        facilities = await db.fetch(query, customer_id)
        
        return [
            FacilityResponse(
                id=f['id'],
                customer_id=f['customer_id'],
                facility_code=f['facility_code'],
                name=f['name'],
                city=f['city'],
                country=f['country'],
                latitude=f['latitude'],
                longitude=f['longitude'],
                created_at=f['created_at']
            )
            for f in facilities
        ]
        
    @staticmethod
    async def get_facility(facility_id: str) -> Optional[FacilityResponse]:
        """
        Get a facility by ID
        
        Args:
            facility_id: Facility ID
            
        Returns:
            Facility or None if not found
        """
        query = """
            SELECT 
                id, customer_id, facility_code, name, city, country,
                latitude, longitude, created_at
            FROM 
                public.facilities
            WHERE 
                id = $1
        """
        
        facility = await db.fetchrow(query, facility_id)
        
        if not facility:
            return None
            
        return FacilityResponse(
            id=facility['id'],
            customer_id=facility['customer_id'],
            facility_code=facility['facility_code'],
            name=facility['name'],
            city=facility['city'],
            country=facility['country'],
            latitude=facility['latitude'],
            longitude=facility['longitude'],
            created_at=facility['created_at']
        )
        
    @staticmethod
    async def get_storage_units(facility_id: str) -> List[StorageUnitResponse]:
        """
        Get all storage units for a facility
        
        Args:
            facility_id: Facility ID
            
        Returns:
            List of storage units
        """
        query = """
            SELECT 
                id, facility_id, unit_code, name, size_value, size_unit,
                set_temperature, temperature_unit, equipment_type, created_at
            FROM 
                public.storage_units
            WHERE 
                facility_id = $1
            ORDER BY 
                unit_code
        """
        
        units = await db.fetch(query, facility_id)
        
        return [
            StorageUnitResponse(
                id=u['id'],
                facility_id=u['facility_id'],
                unit_code=u['unit_code'],
                name=u['name'],
                size_value=u['size_value'],
                size_unit=u['size_unit'],
                set_temperature=u['set_temperature'],
                temperature_unit=u['temperature_unit'],
                equipment_type=u['equipment_type'],
                created_at=u['created_at']
            )
            for u in units
        ]
        
    @staticmethod
    async def get_storage_unit(unit_id: str) -> Optional[StorageUnitResponse]:
        """
        Get a storage unit by ID
        
        Args:
            unit_id: Storage unit ID
            
        Returns:
            Storage unit or None if not found
        """
        query = """
            SELECT 
                id, facility_id, unit_code, name, size_value, size_unit,
                set_temperature, temperature_unit, equipment_type, created_at
            FROM 
                public.storage_units
            WHERE 
                id = $1
        """
        
        unit = await db.fetchrow(query, unit_id)
        
        if not unit:
            return None
            
        return StorageUnitResponse(
            id=unit['id'],
            facility_id=unit['facility_id'],
            unit_code=unit['unit_code'],
            name=unit['name'],
            size_value=unit['size_value'],
            size_unit=unit['size_unit'],
            set_temperature=unit['set_temperature'],
            temperature_unit=unit['temperature_unit'],
            equipment_type=unit['equipment_type'],
            created_at=unit['created_at']
        )
    
    @staticmethod
    async def get_facility_with_units(facility_id: str) -> Optional[FacilityWithUnits]:
        """
        Get a facility with all its storage units
        
        Args:
            facility_id: Facility ID
            
        Returns:
            Facility with units or None if not found
        """
        facility = await FacilityService.get_facility(facility_id)
        
        if not facility:
            return None
            
        units = await FacilityService.get_storage_units(facility_id)
        
        return FacilityWithUnits(
            **facility.dict(),
            storage_units=units
        )
    
    @staticmethod
    async def get_customer_facilities_with_units(
        customer_id: str
    ) -> Optional[CustomerFacilities]:
        """
        Get all facilities with units for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer facilities with units
        """
        # Get customer info
        customer_query = """
            SELECT id, customer_code, name 
            FROM public.customers 
            WHERE id = $1
        """
        
        customer = await db.fetchrow(customer_query, customer_id)
        
        if not customer:
            return None
            
        # Get facilities
        facilities = await FacilityService.get_customer_facilities(customer_id)
        
        # Get units for each facility
        facilities_with_units = []
        for facility in facilities:
            units = await FacilityService.get_storage_units(facility.id)
            facilities_with_units.append(
                FacilityWithUnits(
                    **facility.dict(),
                    storage_units=units
                )
            )
            
        return CustomerFacilities(
            customer_id=customer['id'],
            customer_code=customer['customer_code'],
            customer_name=customer['name'],
            facilities=facilities_with_units
        )
    
    @staticmethod
    async def create_facility(
        customer_id: str, 
        facility_code: str,
        name: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        latitude: Optional[str] = None,
        longitude: Optional[str] = None
    ) -> FacilityResponse:
        """
        Create a new facility
        
        Args:
            customer_id: Customer ID
            facility_code: Facility code
            name: Facility name
            city: City
            country: Country
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Created facility
        """
        query = """
            INSERT INTO public.facilities 
                (id, customer_id, facility_code, name, city, country, latitude, longitude, created_at)
            VALUES 
                ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING 
                id, customer_id, facility_code, name, city, country, latitude, longitude, created_at
        """
        
        facility_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        facility = await db.fetchrow(
            query, 
            facility_id, customer_id, facility_code, name, city, country, 
            latitude, longitude, created_at
        )
        
        return FacilityResponse(
            id=facility['id'],
            customer_id=facility['customer_id'],
            facility_code=facility['facility_code'],
            name=facility['name'],
            city=facility['city'],
            country=facility['country'],
            latitude=facility['latitude'],
            longitude=facility['longitude'],
            created_at=facility['created_at']
        )
    
    @staticmethod
    async def update_facility(
        facility_id: str,
        name: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        latitude: Optional[str] = None,
        longitude: Optional[str] = None
    ) -> Optional[FacilityResponse]:
        """
        Update a facility
        
        Args:
            facility_id: Facility ID
            name: Facility name
            city: City
            country: Country
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Updated facility or None if not found
        """
        # Check if facility exists
        facility = await FacilityService.get_facility(facility_id)
        
        if not facility:
            return None
            
        # Build update query
        update_fields = []
        params = [facility_id]
        param_index = 2
        
        if name is not None:
            update_fields.append(f"name = ${param_index}")
            params.append(name)
            param_index += 1
            
        if city is not None:
            update_fields.append(f"city = ${param_index}")
            params.append(city)
            param_index += 1
            
        if country is not None:
            update_fields.append(f"country = ${param_index}")
            params.append(country)
            param_index += 1
            
        if latitude is not None:
            update_fields.append(f"latitude = ${param_index}")
            params.append(latitude)
            param_index += 1
            
        if longitude is not None:
            update_fields.append(f"longitude = ${param_index}")
            params.append(longitude)
            param_index += 1
            
        # If no fields to update
        if not update_fields:
            return facility
            
        # Execute update
        query = f"""
            UPDATE public.facilities 
            SET {", ".join(update_fields)}
            WHERE id = $1
            RETURNING 
                id, customer_id, facility_code, name, city, country, latitude, longitude, created_at
        """
        
        updated = await db.fetchrow(query, *params)
        
        return FacilityResponse(
            id=updated['id'],
            customer_id=updated['customer_id'],
            facility_code=updated['facility_code'],
            name=updated['name'],
            city=updated['city'],
            country=updated['country'],
            latitude=updated['latitude'],
            longitude=updated['longitude'],
            created_at=updated['created_at']
        )
    
    @staticmethod
    async def create_storage_unit(
        facility_id: str,
        unit_code: str,
        name: Optional[str] = None,
        size_value: Optional[float] = None,
        size_unit: Optional[str] = None,
        set_temperature: Optional[float] = None,
        temperature_unit: Optional[str] = None,
        equipment_type: Optional[str] = None
    ) -> StorageUnitResponse:
        """
        Create a new storage unit
        
        Args:
            facility_id: Facility ID
            unit_code: Unit code
            name: Unit name
            size_value: Size value
            size_unit: Size unit
            set_temperature: Set temperature
            temperature_unit: Temperature unit
            equipment_type: Equipment type
            
        Returns:
            Created storage unit
        """
        query = """
            INSERT INTO public.storage_units 
                (id, facility_id, unit_code, name, size_value, size_unit, 
                set_temperature, temperature_unit, equipment_type, created_at)
            VALUES 
                ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING 
                id, facility_id, unit_code, name, size_value, size_unit, 
                set_temperature, temperature_unit, equipment_type, created_at
        """
        
        unit_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        unit = await db.fetchrow(
            query, 
            unit_id, facility_id, unit_code, name, size_value, size_unit,
            set_temperature, temperature_unit, equipment_type, created_at
        )
        
        return StorageUnitResponse(
            id=unit['id'],
            facility_id=unit['facility_id'],
            unit_code=unit['unit_code'],
            name=unit['name'],
            size_value=unit['size_value'],
            size_unit=unit['size_unit'],
            set_temperature=unit['set_temperature'],
            temperature_unit=unit['temperature_unit'],
            equipment_type=unit['equipment_type'],
            created_at=unit['created_at']
        )
    
    @staticmethod
    async def update_storage_unit(
        unit_id: str,
        name: Optional[str] = None,
        size_value: Optional[float] = None,
        size_unit: Optional[str] = None,
        set_temperature: Optional[float] = None,
        temperature_unit: Optional[str] = None,
        equipment_type: Optional[str] = None
    ) -> Optional[StorageUnitResponse]:
        """
        Update a storage unit
        
        Args:
            unit_id: Storage unit ID
            name: Unit name
            size_value: Size value
            size_unit: Size unit
            set_temperature: Set temperature
            temperature_unit: Temperature unit
            equipment_type: Equipment type
            
        Returns:
            Updated storage unit or None if not found
        """
        # Check if unit exists
        unit = await FacilityService.get_storage_unit(unit_id)
        
        if not unit:
            return None
            
        # Build update query
        update_fields = []
        params = [unit_id]
        param_index = 2
        
        if name is not None:
            update_fields.append(f"name = ${param_index}")
            params.append(name)
            param_index += 1
            
        if size_value is not None:
            update_fields.append(f"size_value = ${param_index}")
            params.append(size_value)
            param_index += 1
            
        if size_unit is not None:
            update_fields.append(f"size_unit = ${param_index}")
            params.append(size_unit)
            param_index += 1
            
        if set_temperature is not None:
            update_fields.append(f"set_temperature = ${param_index}")
            params.append(set_temperature)
            param_index += 1
            
        if temperature_unit is not None:
            update_fields.append(f"temperature_unit = ${param_index}")
            params.append(temperature_unit)
            param_index += 1
            
        if equipment_type is not None:
            update_fields.append(f"equipment_type = ${param_index}")
            params.append(equipment_type)
            param_index += 1
            
        # If no fields to update
        if not update_fields:
            return unit
            
        # Execute update
        query = f"""
            UPDATE public.storage_units 
            SET {", ".join(update_fields)}
            WHERE id = $1
            RETURNING 
                id, facility_id, unit_code, name, size_value, size_unit, 
                set_temperature, temperature_unit, equipment_type, created_at
        """
        
        updated = await db.fetchrow(query, *params)
        
        return StorageUnitResponse(
            id=updated['id'],
            facility_id=updated['facility_id'],
            unit_code=updated['unit_code'],
            name=updated['name'],
            size_value=updated['size_value'],
            size_unit=updated['size_unit'],
            set_temperature=updated['set_temperature'],
            temperature_unit=updated['temperature_unit'],
            equipment_type=updated['equipment_type'],
            created_at=updated['created_at']
        )