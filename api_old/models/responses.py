from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Generic, TypeVar, Union
from datetime import datetime

T = TypeVar('T')

class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = "error"
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Success response model"""
    status: str = "success"
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model"""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class HealthStatus(BaseModel):
    """Health status model"""
    status: str
    version: str
    timestamp: datetime
    database: str
    rabbitmq: str
    uptime_seconds: int


class MetricsResponse(BaseModel):
    """Metrics response model"""
    total_customers: int
    total_facilities: int
    total_storage_units: int
    total_readings: int
    readings_today: int
    readings_this_week: int
    readings_this_month: int
    latest_reading_time: Optional[datetime] = None
    customers_by_sharing_method: Dict[str, int]
    readings_by_status: Dict[str, int]