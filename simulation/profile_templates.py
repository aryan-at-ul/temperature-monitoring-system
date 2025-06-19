# simulation/profile_templates.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import random
import uuid

class DataSharingMethod(Enum):
    CSV = "csv"
    API = "api"
    WEBHOOK = "webhook"

class TemperatureUnit(Enum):
    CELSIUS = "C"
    FAHRENHEIT = "F"

class SizeUnit(Enum):
    SQM = "sqm"
    SQFT = "sqft"

class EquipmentReliability(Enum):
    HIGH = "high"          # 99.5% uptime, rare null readings
    MEDIUM = "medium"      # 97% uptime, occasional null readings  
    LOW = "low"            # 93% uptime, frequent null readings
    FAULTY = "faulty"      # 85% uptime, many null readings

@dataclass
class DataQualityProfile:
    """Defines data quality characteristics for a customer/unit"""
    null_reading_probability: float = 0.001  # Probability of null temperature
    null_name_probability: float = 0.0       # Probability of null unit/facility names
    null_location_probability: float = 0.0   # Probability of null city/location
    sensor_drift_factor: float = 1.0         # Sensor accuracy (1.0 = perfect)
    equipment_reliability: EquipmentReliability = EquipmentReliability.HIGH
    timestamp_jitter_seconds: int = 0        # Random timestamp offset

@dataclass
class UnitTemplate:
    """Template for generating storage units"""
    name_pattern: Optional[str] = None        # e.g., "Freezer {id}", None for null names
    size_range: tuple = (500, 5000)          # Size range (will be converted based on unit)
    size_unit: SizeUnit = SizeUnit.SQM
    temperature_range: tuple = (-25, 50)     # Temperature range for set point
    temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS
    data_frequency_range: tuple = (60, 900)  # Data frequency range in seconds
    data_quality: DataQualityProfile = field(default_factory=DataQualityProfile)

@dataclass 
class FacilityTemplate:
    """Template for generating facilities"""
    name_pattern: Optional[str] = None        # e.g., "Warehouse {id}", None for null names
    location_pool: List[Dict[str, str]] = field(default_factory=lambda: [
        {"city": "Manchester", "country": "England"},
        {"city": "Birmingham", "country": "England"},
        {"city": "London", "country": "England"},
        {"city": None, "country": "England"},  # Some with null cities
    ])
    units_count_range: tuple = (1, 5)        # Number of units per facility
    unit_template: UnitTemplate = field(default_factory=UnitTemplate)

@dataclass
class CustomerTemplate:
    """Template for generating customers"""
    name_pattern: str = "Customer {id}"
    data_sharing_method: DataSharingMethod = DataSharingMethod.CSV
    facilities_count_range: tuple = (1, 3)
    facility_template: FacilityTemplate = field(default_factory=FacilityTemplate)
    
    # Data sharing specific settings
    csv_download_frequency_hours: tuple = (12, 48)    # How often CSV is downloaded
    csv_update_frequency_minutes: tuple = (5, 15)     # How often data is updated
    api_polling_frequency_minutes: tuple = (5, 30)    # API polling frequency
    
    # Global data quality for this customer
    global_data_quality: DataQualityProfile = field(default_factory=DataQualityProfile)

# Predefined templates for different customer types
CUSTOMER_TEMPLATES = {
    "pharmaceutical": CustomerTemplate(
        name_pattern="Pharma Corp {id}",
        data_sharing_method=DataSharingMethod.API,
        facilities_count_range=(1, 2),
        facility_template=FacilityTemplate(
            name_pattern="Pharma Facility {id}",
            location_pool=[
                {"city": "London", "country": "England"},
                {"city": "Cambridge", "country": "England"},
                {"city": "Oxford", "country": "England"},
            ],
            units_count_range=(2, 8),
            unit_template=UnitTemplate(
                name_pattern="Ultra-Low Freezer {id}",
                size_range=(50, 500),
                size_unit=SizeUnit.SQM,
                temperature_range=(-80, -60),
                temperature_unit=TemperatureUnit.CELSIUS,
                data_frequency_range=(60, 300),  # High frequency monitoring
                data_quality=DataQualityProfile(
                    null_reading_probability=0.0001,  # Very reliable
                    equipment_reliability=EquipmentReliability.HIGH
                )
            )
        ),
        api_polling_frequency_minutes=(1, 5),
        global_data_quality=DataQualityProfile(equipment_reliability=EquipmentReliability.HIGH)
    ),
    
    "food_storage": CustomerTemplate(
        name_pattern="Food Storage Ltd {id}",
        data_sharing_method=DataSharingMethod.CSV,
        facilities_count_range=(1, 3),
        facility_template=FacilityTemplate(
            name_pattern="Cold Storage {id}",
            location_pool=[
                {"city": "Manchester", "country": "England"},
                {"city": "Birmingham", "country": "England"},
                {"city": None, "country": "England"},  # Some null cities
            ],
            units_count_range=(1, 4),
            unit_template=UnitTemplate(
                name_pattern="Freezer Unit {id}",
                size_range=(1000, 10000),
                size_unit=SizeUnit.SQFT,  # Food industry often uses sqft
                temperature_range=(-25, 5),
                temperature_unit=TemperatureUnit.FAHRENHEIT,  # US-style measurements
                data_frequency_range=(300, 900),
                data_quality=DataQualityProfile(
                    null_reading_probability=0.002,  # Occasional failures
                    equipment_reliability=EquipmentReliability.MEDIUM
                )
            )
        ),
        csv_download_frequency_hours=(24, 24),  # Daily downloads
        csv_update_frequency_minutes=(5, 5),
        global_data_quality=DataQualityProfile(equipment_reliability=EquipmentReliability.MEDIUM)
    ),
    
    "small_business": CustomerTemplate(
        name_pattern="Local Business {id}",
        data_sharing_method=DataSharingMethod.CSV,
        facilities_count_range=(1, 1),
        facility_template=FacilityTemplate(
            name_pattern=None,  # Often no facility names
            location_pool=[
                {"city": None, "country": "England"},  # Often missing location data
                {"city": "Leeds", "country": "England"},
                {"city": "Sheffield", "country": "England"},
            ],
            units_count_range=(1, 2),
            unit_template=UnitTemplate(
                name_pattern=None,  # Often no unit names
                size_range=(100, 1000),
                size_unit=SizeUnit.SQM,
                temperature_range=(-20, 0),
                temperature_unit=TemperatureUnit.CELSIUS,
                data_frequency_range=(600, 1800),  # Lower frequency
                data_quality=DataQualityProfile(
                    null_reading_probability=0.01,  # More unreliable
                    null_name_probability=0.8,      # Often missing names
                    null_location_probability=0.5,  # Often missing locations
                    equipment_reliability=EquipmentReliability.LOW
                )
            )
        ),
        csv_download_frequency_hours=(24, 72),  # Less frequent downloads
        csv_update_frequency_minutes=(15, 30),
        global_data_quality=DataQualityProfile(
            null_name_probability=0.6,
            null_location_probability=0.4,
            equipment_reliability=EquipmentReliability.LOW
        )
    ),
    
    "industrial": CustomerTemplate(
        name_pattern="Industrial Corp {id}",
        data_sharing_method=DataSharingMethod.API,
        facilities_count_range=(2, 5),
        facility_template=FacilityTemplate(
            name_pattern="Plant {id}",
            location_pool=[
                {"city": "Newcastle", "country": "England"},
                {"city": "Liverpool", "country": "England"},
                {"city": "Glasgow", "country": "Scotland"},
                {"city": "Cardiff", "country": "Wales"},
            ],
            units_count_range=(3, 10),
            unit_template=UnitTemplate(
                name_pattern="Industrial Freezer {id}",
                size_range=(5000, 50000),
                size_unit=SizeUnit.SQFT,
                temperature_range=(-30, 10),
                temperature_unit=TemperatureUnit.FAHRENHEIT,
                data_frequency_range=(300, 600),
                data_quality=DataQualityProfile(
                    null_reading_probability=0.005,  # Some equipment issues
                    equipment_reliability=EquipmentReliability.MEDIUM
                )
            )
        ),
        api_polling_frequency_minutes=(10, 20),
        global_data_quality=DataQualityProfile(equipment_reliability=EquipmentReliability.MEDIUM)
    )
}