# api/models/facility.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class FacilityBase(BaseModel):
    facility_code: str
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FacilityCreate(FacilityBase):
    customer_id: UUID

class FacilityUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FacilityDetail(FacilityBase):
    id: UUID
    customer_id: UUID
    created_at: datetime

class StorageUnitBase(BaseModel):
    unit_code: str
    name: Optional[str] = None
    size_value: float
    size_unit: str
    set_temperature: float
    temperature_unit: str
    equipment_type: str

class StorageUnitCreate(StorageUnitBase):
    facility_id: UUID

class StorageUnitUpdate(BaseModel):
    name: Optional[str] = None
    size_value: Optional[float] = None
    size_unit: Optional[str] = None
    set_temperature: Optional[float] = None
    temperature_unit: Optional[str] = None
    equipment_type: Optional[str] = None

class StorageUnitDetail(StorageUnitBase):
    id: UUID
    facility_id: UUID
    created_at: datetime
    
    # Additional derived fields
    current_temperature: Optional[float] = None
    current_temperature_unit: Optional[str] = None
    temperature_status: Optional[str] = None  # 'normal', 'warning', 'critical'
    last_reading_time: Optional[datetime] = None

class FacilityWithUnits(FacilityDetail):
    """Facility with its storage units"""
    units: List[StorageUnitDetail] = []
    
    # Additional metrics
    unit_count: int
    average_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None