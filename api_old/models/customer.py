from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class CustomerToken(BaseModel):
    """Customer token model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    token_hash: str
    token_name: str
    permissions: List[str]
    accessible_units: Dict[str, Any] = {}
    rate_limit_per_hour: int = 1000
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class AuthenticatedCustomer(BaseModel):
    """Authenticated customer model"""
    customer_id: str
    customer_code: str
    customer_name: str
    permissions: List[str]
    accessible_units: Dict[str, Any] = {}
    token_id: str
    token_name: str


class AdminUser(BaseModel):
    """Admin user model"""
    user_id: str
    username: str
    display_name: str
    token_id: str


class CustomerCreate(BaseModel):
    """Customer creation model"""
    customer_code: str
    name: str
    data_sharing_method: str
    data_frequency_seconds: int
    api_url: Optional[str] = None
    is_active: bool = True


class CustomerUpdate(BaseModel):
    """Customer update model"""
    name: Optional[str] = None
    data_sharing_method: Optional[str] = None
    data_frequency_seconds: Optional[int] = None
    api_url: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    """Customer response model"""
    id: str
    customer_code: str
    name: str
    data_sharing_method: str
    data_frequency_seconds: int
    api_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerTokenCreate(BaseModel):
    """Customer token creation model"""
    token_name: str
    permissions: List[str]
    accessible_units: Dict[str, Any] = {}
    rate_limit_per_hour: int = 1000
    expires_at: Optional[datetime] = None


class CustomerTokenResponse(BaseModel):
    """Customer token response model"""
    id: str
    customer_id: str
    token_name: str
    permissions: List[str]
    accessible_units: Dict[str, Any] = {}
    rate_limit_per_hour: int
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime
    is_active: bool
    token: Optional[str] = None  # Only included when creating a new token


class CustomerTokenUpdate(BaseModel):
    """Customer token update model"""
    token_name: Optional[str] = None
    permissions: Optional[List[str]] = None
    accessible_units: Optional[Dict[str, Any]] = None
    rate_limit_per_hour: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None