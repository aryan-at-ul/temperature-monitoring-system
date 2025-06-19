import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from database.connection import db
from database.models.models import (
    Customer, CustomerToken, Facility, StorageUnit, 
    TemperatureReading, SystemConfig, IngestionLog
)

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common CRUD operations"""
    table_name = None

    @classmethod
    async def get_by_id(cls, id: str) -> Optional[Dict[str, Any]]:
        """Get a record by ID"""
        query = f"SELECT * FROM {cls.table_name} WHERE id = $1"
        return await db.fetchrow(query, id)

    @classmethod
    async def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record"""
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
        values = list(data.values())
        
        query = f"INSERT INTO {cls.table_name} ({columns}) VALUES ({placeholders}) RETURNING *"
        return await db.fetchrow(query, *values)

    @classmethod
    async def update(cls, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by ID"""
        if 'updated_at' not in data:
            data['updated_at'] = datetime.now()
        
        set_clause = ", ".join(f"{key} = ${i+2}" for i, key in enumerate(data.keys()))
        values = list(data.values())
        
        query = f"UPDATE {cls.table_name} SET {set_clause} WHERE id = $1 RETURNING *"
        return await db.fetchrow(query, id, *values)

    @classmethod
    async def delete(cls, id: str) -> bool:
        """Delete a record by ID"""
        query = f"DELETE FROM {cls.table_name} WHERE id = $1"
        result = await db.execute(query, id)
        return 'DELETE' in result


class CustomerRepository(BaseRepository):
    """Repository for Customer table operations"""
    table_name = "public.customers"

    @classmethod
    async def get_all_active(cls) -> List[Dict[str, Any]]:
        """Get all active customers"""
        query = f"SELECT * FROM {cls.table_name} WHERE is_active = true"
        return await db.fetch(query)

    @classmethod
    async def get_by_code(cls, customer_code: str) -> Optional[Dict[str, Any]]:
        """Get a customer by code"""
        query = f"SELECT * FROM {cls.table_name} WHERE customer_code = $1"
        return await db.fetchrow(query, customer_code)
        
    @classmethod
    async def update_api_url(cls, id: str, api_url: str) -> Optional[Dict[str, Any]]:
        """Update the API URL for a customer"""
        query = f"UPDATE {cls.table_name} SET api_url = $2, updated_at = $3 WHERE id = $1 RETURNING *"
        return await db.fetchrow(query, id, api_url, datetime.now())


class CustomerTokenRepository(BaseRepository):
    """Repository for CustomerToken table operations"""
    table_name = "public.customer_tokens"

    @classmethod
    async def get_by_customer_id(cls, customer_id: str) -> List[Dict[str, Any]]:
        """Get all tokens for a customer"""
        query = f"SELECT * FROM {cls.table_name} WHERE customer_id = $1 AND is_active = true"
        return await db.fetch(query, customer_id)


class FacilityRepository(BaseRepository):
    """Repository for Facility table operations"""
    table_name = "public.facilities"

    @classmethod
    async def get_by_customer_id(cls, customer_id: str) -> List[Dict[str, Any]]:
        """Get all facilities for a customer"""
        query = f"SELECT * FROM {cls.table_name} WHERE customer_id = $1"
        return await db.fetch(query, customer_id)

    @classmethod
    async def get_by_facility_code(cls, customer_id: str, facility_code: str) -> Optional[Dict[str, Any]]:
        """Get a facility by code and customer ID"""
        query = f"SELECT * FROM {cls.table_name} WHERE customer_id = $1 AND facility_code = $2"
        return await db.fetchrow(query, customer_id, facility_code)


class StorageUnitRepository(BaseRepository):
    """Repository for StorageUnit table operations"""
    table_name = "public.storage_units"

    @classmethod
    async def get_by_facility_id(cls, facility_id: str) -> List[Dict[str, Any]]:
        """Get all storage units for a facility"""
        query = f"SELECT * FROM {cls.table_name} WHERE facility_id = $1"
        return await db.fetch(query, facility_id)

    @classmethod
    async def get_by_unit_code(cls, facility_id: str, unit_code: str) -> Optional[Dict[str, Any]]:
        """Get a storage unit by code and facility ID"""
        query = f"SELECT * FROM {cls.table_name} WHERE facility_id = $1 AND unit_code = $2"
        return await db.fetchrow(query, facility_id, unit_code)


class TemperatureReadingRepository(BaseRepository):
    """Repository for TemperatureReading table operations"""
    table_name = "public.temperature_readings"

    @classmethod
    async def create_batch(cls, readings: List[Dict[str, Any]]) -> int:
        """Create multiple temperature readings in a batch"""
        if not readings:
            return 0
            
        # Prepare batch insert
        columns = readings[0].keys()
        column_str = ", ".join(columns)
        
        # Build VALUES part with placeholders
        placeholder_rows = []
        values = []
        for i, reading in enumerate(readings):
            placeholders = ", ".join(f"${j + 1 + i * len(columns)}" for j in range(len(columns)))
            placeholder_rows.append(f"({placeholders})")
            values.extend([reading[col] for col in columns])
        
        values_str = ", ".join(placeholder_rows)
        
        # Execute batch insert
        query = f"INSERT INTO {cls.table_name} ({column_str}) VALUES {values_str}"
        result = await db.execute(query, *values)
        
        # Parse count from result string like "INSERT 0 42"
        count = int(result.split(" ")[2]) if result else 0
        return count

    @classmethod
    async def get_recent_by_unit(cls, storage_unit_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent readings for a storage unit"""
        query = f"""
            SELECT * FROM {cls.table_name} 
            WHERE storage_unit_id = $1 
            ORDER BY recorded_at DESC 
            LIMIT $2
        """
        return await db.fetch(query, storage_unit_id, limit)


class SystemConfigRepository(BaseRepository):
    """Repository for SystemConfig table operations"""
    table_name = "public.system_config"

    @classmethod
    async def get_by_key(cls, key: str) -> Optional[Dict[str, Any]]:
        """Get a config value by key"""
        query = f"SELECT * FROM {cls.table_name} WHERE key = $1"
        return await db.fetchrow(query, key)


class IngestionLogRepository(BaseRepository):
    """Repository for IngestionLog table operations"""
    table_name = "public.ingestion_logs"

    @classmethod
    async def get_recent_by_customer(cls, customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent ingestion logs for a customer"""
        query = f"""
            SELECT * FROM {cls.table_name} 
            WHERE customer_id = $1 
            ORDER BY start_time DESC 
            LIMIT $2
        """
        return await db.fetch(query, customer_id, limit)

    @classmethod
    async def create_log(cls, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an ingestion log entry"""
        if 'id' not in log_data:
            log_data['id'] = str(uuid.uuid4())
        if 'created_at' not in log_data:
            log_data['created_at'] = datetime.now()
            
        return await cls.create(log_data)