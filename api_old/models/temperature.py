from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid


class TemperatureReadingBase(BaseModel):
    """Base temperature reading model"""
    temperature: float
    temperature_unit: str
    recorded_at: datetime
    sensor_id: Optional[str] = None
    quality_score: Optional[float] = None
    equipment_status: Optional[str] = "normal"


class TemperatureReadingCreate(TemperatureReadingBase):
    """Temperature reading creation model"""
    customer_id: str
    facility_id: str
    storage_unit_id: str


class TemperatureReadingResponse(TemperatureReadingBase):
    """Temperature reading response model"""
    id: str
    customer_id: str
    facility_id: str
    storage_unit_id: str
    created_at: datetime


class TemperatureReadingDetail(TemperatureReadingResponse):
    """Detailed temperature reading response model"""
    facility_code: str
    facility_name: Optional[str] = None
    unit_code: str
    unit_name: Optional[str] = None
    equipment_type: Optional[str] = None
    set_temperature: Optional[float] = None
    temperature_deviation: Optional[float] = None
    city: Optional[str] = None
    country: Optional[str] = None


class TemperatureQuery(BaseModel):
    """Temperature query parameters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    equipment_status: Optional[str] = None
    min_quality_score: Optional[float] = None
    sensor_id: Optional[str] = None
    temperature_unit: Optional[str] = None
    limit: int = 100
    offset: int = 0


class AggregationType(str):
    """Aggregation type enum"""
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    

class TemperatureAggregation(BaseModel):
    """Temperature aggregation parameters"""
    aggregation: str  # "avg", "min", "max", "count"
    group_by: str  # "hour", "day", "week", "month", "facility", "unit", "sensor"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    facility_id: Optional[str] = None
    storage_unit_id: Optional[str] = None
    sensor_id: Optional[str] = None
    equipment_status: Optional[str] = None


class AggregationResult(BaseModel):
    """Temperature aggregation result"""
    group_value: Union[str, datetime]
    value: float


class TemperatureStats(BaseModel):
    """Temperature statistics"""
    count: int
    min_temperature: float
    max_temperature: float
    avg_temperature: float
    std_deviation: Optional[float] = None
    latest_reading: Optional[datetime] = None
    normal_count: int = 0
    warning_count: int = 0
    critical_count: int = 0


class StorageUnitStats(BaseModel):
    """Storage unit statistics"""
    unit_id: str
    unit_code: str
    unit_name: Optional[str] = None
    statistics: TemperatureStats


class FacilityStats(BaseModel):
    """Facility statistics"""
    facility_id: str
    facility_code: str
    facility_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    statistics: TemperatureStats
    units: List[StorageUnitStats] = []


class CustomerStats(BaseModel):
    """Customer statistics"""
    customer_id: str
    customer_code: str
    customer_name: str
    statistics: TemperatureStats
    facilities: List[FacilityStats] = []


class TemperatureAlert(BaseModel):
    """Temperature alert model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    facility_id: str
    storage_unit_id: str
    temperature: float
    temperature_unit: str
    set_temperature: Optional[float] = None
    deviation: float
    threshold: float
    severity: str  # "warning", "critical"
    recorded_at: datetime
    created_at: datetime = Field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    notes: Optional[str] = None


class TemperatureAlertResponse(TemperatureAlert):
    """Temperature alert response model"""
    customer_code: str
    customer_name: str
    facility_code: str
    facility_name: Optional[str] = None
    unit_code: str
    unit_name: Optional[str] = None