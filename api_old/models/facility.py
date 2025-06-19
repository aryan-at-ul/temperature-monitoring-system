from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class FacilityBase(BaseModel):
    """Base facility model"""
    facility_code: str
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None


class FacilityCreate(FacilityBase):
    """Facility creation model"""
    customer_id: str


class FacilityUpdate(BaseModel):
    """Facility update model"""
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None


class FacilityResponse(FacilityBase):
    """Facility response model"""
    id: str
    customer_id: str
    created_at: datetime


class StorageUnitBase(BaseModel):
    """Base storage unit model"""
    unit_code: str
    name: Optional[str] = None
    size_value: Optional[float] = None
    size_unit: Optional[str] = None
    set_temperature: Optional[float] = None
    temperature_unit: Optional[str] = None
    equipment_type: Optional[str] = None


class StorageUnitCreate(StorageUnitBase):
    """Storage unit creation model"""
    facility_id: str


class StorageUnitUpdate(BaseModel):
    """Storage unit update model"""
    name: Optional[str] = None
    size_value: Optional[float] = None
    size_unit: Optional[str] = None
    set_temperature: Optional[float] = None
    temperature_unit: Optional[str] = None
    equipment_type: Optional[str] = None


class StorageUnitResponse(StorageUnitBase):
    """Storage unit response model"""
    id: str
    facility_id: str
    created_at: datetime


class FacilityWithUnits(FacilityResponse):
    """Facility with storage units model"""
    storage_units: List[StorageUnitResponse] = []


class CustomerFacilities(BaseModel):
    """Customer facilities model"""
    customer_id: str
    customer_code: str
    customer_name: str
    facilities: List[FacilityWithUnits] = []