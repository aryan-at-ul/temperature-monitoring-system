# api/models/customer.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class CustomerBase(BaseModel):
    customer_code: str
    name: str
    data_sharing_method: str
    data_frequency_seconds: int
    api_url: Optional[str] = None
    is_active: bool = True

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    data_sharing_method: Optional[str] = None
    data_frequency_seconds: Optional[int] = None
    api_url: Optional[str] = None
    is_active: Optional[bool] = None

class CustomerProfile(CustomerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class CustomerToken(BaseModel):
    id: UUID
    token_name: str
    permissions: List[str]
    rate_limit_per_hour: int
    accessible_units: Dict = {}
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime
    is_active: bool

class TokenCreate(BaseModel):
    token_name: str
    permissions: List[str]
    rate_limit_per_hour: int = 1000
    accessible_units: Dict = {}
    expires_at: Optional[datetime] = None

class CustomerDetail(CustomerProfile):
    """Detailed customer information with metrics"""
    facility_count: int
    unit_count: int
    active_readings_count: int
    last_reading_time: Optional[datetime] = None