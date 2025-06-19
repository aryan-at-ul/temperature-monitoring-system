# api/models/requests.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TemperatureUnit(str, Enum):
    CELSIUS = "C"
    FAHRENHEIT = "F"
    KELVIN = "K"

class TimeRange(BaseModel):
    start_time: datetime = Field(..., description="Start time for data range")
    end_time: datetime = Field(..., description="End time for data range")
    
    @validator('end_time')
    def end_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class TemperatureQuery(BaseModel):
    customer_id: Optional[str] = Field(None, description="Customer identifier")
    facility_id: Optional[str] = Field(None, description="Facility identifier")
    unit_id: Optional[str] = Field(None, description="Storage unit identifier")
    time_range: Optional[TimeRange] = Field(None, description="Time range filter")
    temperature_unit: Optional[TemperatureUnit] = Field(None, description="Preferred temperature unit")
    limit: int = Field(100, ge=1, le=10000, description="Maximum number of records")
    offset: int = Field(0, ge=0, description="Number of records to skip")
    include_failures: bool = Field(True, description="Include equipment failure readings")

class TokenRequest(BaseModel):
    customer_id: str = Field(..., description="Customer identifier")
    permissions: List[str] = Field(["read"], description="Token permissions")
    expires_hours: int = Field(24, ge=1, le=8760, description="Token expiration in hours")
