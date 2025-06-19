# database/models/storage_unit.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass
class StorageUnit:
    id: UUID
    facility_id: UUID
    unit_code: str
    name: Optional[str] = None
    size_value: float = 0.0
    size_unit: str = 'sqm'  # 'sqm', 'sqft', 'm2', 'ft2'
    set_temperature: float = -18.0
    temperature_unit: str = 'C'  # 'C', 'F', 'K'
    equipment_type: str = 'freezer'
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        # Validate units
        valid_size_units = {'sqm', 'sqft', 'm2', 'ft2'}
        valid_temp_units = {'C', 'F', 'K'}
        
        if self.size_unit not in valid_size_units:
            raise ValueError(f"Invalid size unit: {self.size_unit}")
        if self.temperature_unit not in valid_temp_units:
            raise ValueError(f"Invalid temperature unit: {self.temperature_unit}")
    
    @property
    def display_name(self) -> str:
        """Get display name for the unit"""
        return self.name or f"Unit {self.unit_code}"
    
    @property
    def size_display(self) -> str:
        """Get formatted size with units"""
        return f"{self.size_value:.1f} {self.size_unit}"
    
    @property
    def target_temp_display(self) -> str:
        """Get formatted target temperature"""
        return f"{self.set_temperature:.1f}°{self.temperature_unit}"
    
    def convert_size_to_sqm(self) -> float:
        """Convert size to square meters"""
        if self.size_unit in ['sqm', 'm2']:
            return self.size_value
        elif self.size_unit in ['sqft', 'ft2']:
            return self.size_value * 0.092903
        return self.size_value
    
    def convert_temperature_to_celsius(self) -> float:
        """Convert set temperature to Celsius"""
        if self.temperature_unit == 'C':
            return self.set_temperature
        elif self.temperature_unit == 'F':
            return (self.set_temperature - 32) * 5.0/9.0
        elif self.temperature_unit == 'K':
            return self.set_temperature - 273.15
        return self.set_temperature