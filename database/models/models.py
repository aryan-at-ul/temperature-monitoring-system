from datetime import datetime
import uuid
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_code: str
    name: str
    data_sharing_method: str
    data_frequency_seconds: int
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    api_url: Optional[str] = None  # Added for API URL


class CustomerToken(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    token_hash: str
    token_name: str
    permissions: List[str]
    accessible_units: Dict[str, Any] = {}
    rate_limit_per_hour: int = 1000
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class Facility(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    facility_code: str
    name: Optional[str] = ""
    city: Optional[str] = ""
    country: Optional[str] = ""
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.now)


class StorageUnit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    facility_id: str
    unit_code: str
    name: Optional[str] = ""
    size_value: Optional[float] = None
    size_unit: Optional[str] = None
    set_temperature: Optional[float] = None
    temperature_unit: Optional[str] = None
    equipment_type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class TemperatureReading(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    facility_id: str
    storage_unit_id: str
    temperature: float
    temperature_unit: str
    recorded_at: datetime
    sensor_id: Optional[str] = None
    quality_score: Optional[float] = None
    equipment_status: Optional[str] = "normal"
    created_at: datetime = Field(default_factory=datetime.now)


class SystemConfig(BaseModel):
    key: str
    value: Any
    description: str
    updated_at: datetime = Field(default_factory=datetime.now)


class IngestionLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    ingestion_type: str  # 'api' or 'csv'
    status: str  # 'success', 'failure', 'partial'
    records_processed: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    source_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class DataEvent(BaseModel):
    """Model for the events pushed to the queue"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "temperature_reading"
    customer_id: str
    facility_id: Optional[str] = None
    unit_id: Optional[str] = None
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    processed: bool = False