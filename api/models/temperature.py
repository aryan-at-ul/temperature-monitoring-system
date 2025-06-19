# api/models/temperature.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from fastapi import Query

class TemperatureQuery(BaseModel):
    limit: int = 100
    offset: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    equipment_status: Optional[str] = None
    quality_score: Optional[float] = None # Also good practice to change this here
    sensor_id: Optional[str] = None
    
    class Config:
        # Allow populating from query parameters
        extra = "allow"

class TemperatureReadingBase(BaseModel):
    storage_unit_id: UUID
    temperature: float
    temperature_unit: str
    recorded_at: datetime
    sensor_id: str
    
    quality_score: float = 1.0 
    
    equipment_status: str = "normal"  # normal, warning, error

class TemperatureReadingCreate(TemperatureReadingBase):
    pass

class TemperatureReadingDetail(TemperatureReadingBase):
    id: UUID # Should be BIGINT or int in a real-world high-throughput system, but UUID is fine for this project.
    customer_id: UUID
    facility_id: UUID
    created_at: datetime
    
    # Extra fields from joins
    facility_name: Optional[str] = None
    unit_name: Optional[str] = None

class TemperatureStats(BaseModel):
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    avg_temperature: Optional[float] = None
    reading_count: int = 0
    normal_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    unit_count: int = 0
    temperature_unit: Optional[str] = None

class TemperatureAggregation(BaseModel):
    group_by: List[str]  # hour, day, week, month, facility, unit, sensor
    aggregations: List[str]  # avg, min, max, count
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    facility_id: Optional[UUID] = None
    storage_unit_id: Optional[UUID] = None

class AggregationResult(BaseModel):
    group_key: Dict[str, Any]
    metrics: Dict[str, Any]