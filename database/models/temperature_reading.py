# database/models/temperature_reading.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass
class TemperatureReading:
    id: UUID
    customer_id: UUID
    facility_id: UUID
    storage_unit_id: UUID
    temperature: Optional[float] = None  # Can be None for equipment failure
    temperature_unit: str = 'C'
    recorded_at: datetime = field(default_factory=datetime.utcnow)
    sensor_id: Optional[str] = None
    quality_score: float = 1.0
    equipment_status: str = 'normal'  # 'normal', 'failure', 'maintenance'
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        valid_temp_units = {'C', 'F', 'K'}
        valid_statuses = {'normal', 'failure', 'maintenance', 'warning'}
        
        if self.temperature_unit not in valid_temp_units:
            raise ValueError(f"Invalid temperature unit: {self.temperature_unit}")
        if self.equipment_status not in valid_statuses:
            raise ValueError(f"Invalid equipment status: {self.equipment_status}")
        if not (0 <= self.quality_score <= 1):
            raise ValueError(f"Quality score must be between 0 and 1: {self.quality_score}")
    
    @property
    def is_equipment_failure(self) -> bool:
        """Check if this reading indicates equipment failure"""
        return self.temperature is None or self.equipment_status == 'failure'
    
    @property
    def temperature_display(self) -> str:
        """Get formatted temperature display"""
        if self.temperature is None:
            return "N/A (Equipment Failure)"
        return f"{self.temperature:.1f}°{self.temperature_unit}"
    
    def convert_temperature_to_celsius(self) -> Optional[float]:
        """Convert temperature to Celsius"""
        if self.temperature is None:
            return None
        
        if self.temperature_unit == 'C':
            return self.temperature
        elif self.temperature_unit == 'F':
            return (self.temperature - 32) * 5.0/9.0
        elif self.temperature_unit == 'K':
            return self.temperature - 273.15
        return self.temperature
