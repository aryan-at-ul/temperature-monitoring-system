
# database/models/auth.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import json

@dataclass
class CustomerToken:
    id: UUID
    customer_id: UUID
    token_hash: str
    token_name: Optional[str] = None
    permissions: List[str] = field(default_factory=lambda: ['read'])
    accessible_units: List[UUID] = field(default_factory=list)
    rate_limit_per_hour: int = 1000
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid for use"""
        return self.is_active and not self.is_expired
    
    def has_permission(self, permission: str) -> bool:
        """Check if token has specific permission"""
        return permission in self.permissions or 'admin' in self.permissions
    
    def can_access_unit(self, unit_id: UUID) -> bool:
        """Check if token can access specific storage unit"""
        # Empty list means access to all units
        return not self.accessible_units or unit_id in self.accessible_units