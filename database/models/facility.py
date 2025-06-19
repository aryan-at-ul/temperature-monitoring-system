# database/models/facility.py  
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

@dataclass
class Facility:
    id: UUID
    customer_id: UUID
    facility_code: str
    name: Optional[str] = None
    city: Optional[str] = None
    country: str = "Unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Relationships
    storage_units: List['StorageUnit'] = field(default_factory=list)
    
    @property
    def location_string(self) -> str:
        """Get human-readable location"""
        parts = [self.name, self.city, self.country]
        return ", ".join(filter(None, parts))
    
    @property
    def has_coordinates(self) -> bool:
        """Check if facility has GPS coordinates"""
        return self.latitude is not None and self.longitude is not None