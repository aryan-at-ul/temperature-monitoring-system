import random
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from datetime import datetime
from dataclasses import dataclass



from .profile_templates import (
    CustomerTemplate, FacilityTemplate, UnitTemplate, 
    DataSharingMethod, TemperatureUnit, SizeUnit, EquipmentReliability,
    CUSTOMER_TEMPLATES, DataQualityProfile
)

@dataclass
class GeneratedUnit:
    id: str
    name: Optional[str]
    size: int
    size_unit: str
    set_temperature: float
    temperature_unit: str
    data_frequency: int  # seconds
    data_quality: Dict[str, Any]
    facility_id: str

@dataclass
class GeneratedFacility:
    id: str
    name: Optional[str]
    city: Optional[str]
    country: str
    units: List[GeneratedUnit]
    customer_id: str

@dataclass
class GeneratedCustomer:
    id: str
    name: str
    data_sharing_method: str
    facilities: List[GeneratedFacility]
    data_config: Dict[str, Any]
    data_quality: Dict[str, Any]

class CustomerGenerator:
    def __init__(self):
        self.generated_customers = {}
    
    def generate_customer(self, 
                         customer_id: str,
                         template_name: str = None,
                         custom_template: CustomerTemplate = None) -> GeneratedCustomer:
        """Generate a customer from a template"""
        
        if custom_template:
            template = custom_template
        elif template_name and template_name in CUSTOMER_TEMPLATES:
            template = CUSTOMER_TEMPLATES[template_name]
        else:
            # Random template if none specified
            template = random.choice(list(CUSTOMER_TEMPLATES.values()))
        
        # Generate customer name
        customer_name = template.name_pattern.format(id=customer_id)
        
        # Generate facilities
        facilities_count = random.randint(*template.facilities_count_range)
        facilities = []
        
        for i in range(facilities_count):
            facility_id = f"facility_{customer_id}_{i+1}"
            facility = self._generate_facility(facility_id, customer_id, template.facility_template)
            facilities.append(facility)
        
        # Generate data sharing configuration
        data_config = self._generate_data_config(template)
        
        # Convert global data quality to serializable format
        global_data_quality = self._convert_data_quality_to_dict(template.global_data_quality)
        
        customer = GeneratedCustomer(
            id=customer_id,
            name=customer_name,
            data_sharing_method=template.data_sharing_method.value,
            facilities=facilities,
            data_config=data_config,
            data_quality=global_data_quality
        )
        
        self.generated_customers[customer_id] = customer
        return customer
    
    def _convert_data_quality_to_dict(self, data_quality: DataQualityProfile) -> Dict[str, Any]:
        """Convert DataQualityProfile to serializable dictionary"""
        quality_dict = asdict(data_quality)
        
        # Convert enum to string value
        if hasattr(data_quality.equipment_reliability, 'value'):
            quality_dict['equipment_reliability'] = data_quality.equipment_reliability.value
        else:
            quality_dict['equipment_reliability'] = str(data_quality.equipment_reliability)
        
        return quality_dict
    
    def _generate_facility(self, 
                          facility_id: str, 
                          customer_id: str,
                          template: FacilityTemplate) -> GeneratedFacility:
        """Generate a facility from template"""
        
        # Generate facility name (might be null)
        if template.name_pattern and random.random() > template.unit_template.data_quality.null_name_probability:
            facility_name = template.name_pattern.format(id=facility_id.split('_')[-1])
        else:
            facility_name = None
        
        # Select location
        location = random.choice(template.location_pool)
        city = location["city"]
        country = location["country"]
        
        # Apply null location probability
        if random.random() < template.unit_template.data_quality.null_location_probability:
            city = None
        
        # Generate units
        units_count = random.randint(*template.units_count_range)
        units = []
        
        for i in range(units_count):
            unit_id = f"unit_{customer_id}_{facility_id.split('_')[-1]}_{i+1}"
            unit = self._generate_unit(unit_id, facility_id, template.unit_template)
            units.append(unit)
        
        return GeneratedFacility(
            id=facility_id,
            name=facility_name,
            city=city,
            country=country,
            units=units,
            customer_id=customer_id
        )
    
    def _generate_unit(self,
                      unit_id: str,
                      facility_id: str, 
                      template: UnitTemplate) -> GeneratedUnit:
        """Generate a storage unit from template"""
        
        # Generate unit name (might be null)
        if template.name_pattern and random.random() > template.data_quality.null_name_probability:
            unit_name = template.name_pattern.format(id=unit_id.split('_')[-1])
        else:
            unit_name = None
        
        # Generate size
        size = random.randint(*template.size_range)
        
        # Generate set temperature
        set_temperature = random.uniform(*template.temperature_range)
        
        # Generate data frequency
        data_frequency = random.randint(*template.data_frequency_range)
        
        # Convert data quality to dictionary with string values
        data_quality_dict = asdict(template.data_quality)
        # Convert enum to string value
        data_quality_dict['equipment_reliability'] = template.data_quality.equipment_reliability.value
        
        return GeneratedUnit(
            id=unit_id,
            name=unit_name,
            size=size,
            size_unit=template.size_unit.value,
            set_temperature=round(set_temperature, 1),
            temperature_unit=template.temperature_unit.value,
            data_frequency=data_frequency,
            data_quality=data_quality_dict,
            facility_id=facility_id
        )
    
    def _generate_data_config(self, template: CustomerTemplate) -> Dict[str, Any]:
        """Generate data sharing configuration"""
        
        config = {
            "data_sharing_method": template.data_sharing_method.value
        }
        
        if template.data_sharing_method == DataSharingMethod.CSV:
            config.update({
                "csv_download_frequency_hours": random.randint(*template.csv_download_frequency_hours),
                "csv_update_frequency_minutes": random.randint(*template.csv_update_frequency_minutes)
            })
        elif template.data_sharing_method == DataSharingMethod.API:
            config.update({
                "api_polling_frequency_minutes": random.randint(*template.api_polling_frequency_minutes)
            })
        
        return config
    
    def generate_multiple_customers(self, 
                                   count: int,
                                   template_distribution: Dict[str, float] = None) -> List[GeneratedCustomer]:
        """Generate multiple customers with specified template distribution"""
        
        if template_distribution is None:
            # Default distribution
            template_distribution = {
                "pharmaceutical": 0.1,
                "food_storage": 0.4,
                "small_business": 0.3,
                "industrial": 0.2
            }
        
        customers = []
        
        for i in range(count):
            customer_id = chr(65 + i) if i < 26 else f"CUST_{i+1}"  # A, B, C... then CUST_27, etc.
            
            # Select template based on distribution
            template_name = random.choices(
                list(template_distribution.keys()),
                weights=list(template_distribution.values())
            )[0]
            
            customer = self.generate_customer(customer_id, template_name)
            customers.append(customer)
        
        return customers
    
    def generate_assignment_customer(self, customer_id: str) -> GeneratedCustomer:
        """Generate exact assignment customers A or B"""
        
        if customer_id == 'A':
            # Customer A exact specifications
            facility = GeneratedFacility(
                id="facility_a_1",
                name=None,  # null as per assignment
                city=None,  # null as per assignment
                country="England",
                units=[
                    GeneratedUnit(
                        id="unit_a_1",
                        name=None,  # null as per assignment
                        size=930,
                        size_unit="sqm",
                        set_temperature=-20,
                        temperature_unit="C",
                        data_frequency=300,  # 5 minutes
                        data_quality={
                            'null_reading_probability': 0.001,
                            'null_name_probability': 1.0,  # Always null
                            'null_location_probability': 1.0,  # Always null
                            'sensor_drift_factor': 1.0,
                            'equipment_reliability': 'medium',  # String value
                            'timestamp_jitter_seconds': 0
                        },
                        facility_id="facility_a_1"
                    )
                ],
                customer_id="A"
            )
            
            customer = GeneratedCustomer(
                id="A",
                name="Customer A",
                data_sharing_method="csv",
                facilities=[facility],
                data_config={
                    "data_sharing_method": "csv",
                    "csv_download_frequency_hours": 24,
                    "csv_update_frequency_minutes": 5
                },
                data_quality={
                    'null_reading_probability': 0.001,
                    'null_name_probability': 1.0,
                    'null_location_probability': 1.0,
                    'equipment_reliability': 'medium'  # String value
                }
            )
            
        elif customer_id == 'B':
            # Customer B exact specifications
            units = [
                GeneratedUnit(
                    id="unit_b_1",
                    name="Deep Freeze 1",
                    size=50000,
                    size_unit="sqft",
                    set_temperature=0,
                    temperature_unit="F",
                    data_frequency=900,  # 15 minutes
                    data_quality={
                        'null_reading_probability': 0.0005,
                        'null_name_probability': 0.0,
                        'null_location_probability': 0.0,
                        'sensor_drift_factor': 1.0,
                        'equipment_reliability': 'high',  # String value
                        'timestamp_jitter_seconds': 0
                    },
                    facility_id="facility_b_1"
                ),
                GeneratedUnit(
                    id="unit_b_2", 
                    name="Chilled Room 1",
                    size=10000,
                    size_unit="sqft",
                    set_temperature=0,
                    temperature_unit="F",
                    data_frequency=900,
                    data_quality={
                        'null_reading_probability': 0.0005,
                        'null_name_probability': 0.0,
                        'null_location_probability': 0.0,
                        'sensor_drift_factor': 1.0,
                        'equipment_reliability': 'high',  # String value
                        'timestamp_jitter_seconds': 0
                    },
                    facility_id="facility_b_1"
                ),
                GeneratedUnit(
                    id="unit_b_3",
                    name="Chilled Room 2", 
                    size=5000,
                    size_unit="sqft",
                    set_temperature=45,
                    temperature_unit="F",
                    data_frequency=900,
                    data_quality={
                        'null_reading_probability': 0.0005,
                        'null_name_probability': 0.0,
                        'null_location_probability': 0.0,
                        'sensor_drift_factor': 1.0,
                        'equipment_reliability': 'high',  # String value
                        'timestamp_jitter_seconds': 0
                    },
                    facility_id="facility_b_1"
                )
            ]
            
            facility = GeneratedFacility(
                id="facility_b_1",
                name=None,  # Assignment doesn't specify facility name
                city="Manchester",
                country="England", 
                units=units,
                customer_id="B"
            )
            
            customer = GeneratedCustomer(
                id="B",
                name="Customer B",
                data_sharing_method="api",
                facilities=[facility],
                data_config={
                    "data_sharing_method": "api",
                    "api_polling_frequency_minutes": 15
                },
                data_quality={
                    'null_reading_probability': 0.0005,
                    'null_name_probability': 0.0,
                    'null_location_probability': 0.0,
                    'equipment_reliability': 'high'  # String value
                }
            )
        
        else:
            raise ValueError(f"Assignment customer '{customer_id}' not supported. Use 'A' or 'B'.")
        
        self.generated_customers[customer_id] = customer
        return customer
    
    def get_customer(self, customer_id: str) -> Optional[GeneratedCustomer]:
        """Get a generated customer by ID"""
        return self.generated_customers.get(customer_id)
    
    def list_customers(self) -> List[str]:
        """List all generated customer IDs"""
        return list(self.generated_customers.keys())
    
    def export_to_yaml(self, filepath: str):
        """Export generated customers to YAML configuration"""
        import yaml
        
        def serialize_value(obj):
            """Recursively serialize objects to make them YAML-safe"""
            if hasattr(obj, 'value'):  # Handle enum objects
                return obj.value
            elif isinstance(obj, dict):
                return {key: serialize_value(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [serialize_value(item) for item in obj]
            else:
                return obj
        
        export_data = {
            "customers": {}
        }
        
        for customer_id, customer in self.generated_customers.items():
            customer_data = {
                "name": customer.name,
                "data_sharing_method": customer.data_sharing_method,
                "data_config": serialize_value(customer.data_config),
                "data_quality": serialize_value(customer.data_quality),
                "facilities": []
            }
            
            for facility in customer.facilities:
                facility_data = {
                    "id": facility.id,
                    "name": facility.name,
                    "city": facility.city,
                    "country": facility.country,
                    "units": []
                }
                
                for unit in facility.units:
                    unit_data = {
                        "id": unit.id,
                        "name": unit.name,
                        "size": unit.size,
                        "size_unit": unit.size_unit,
                        "set_temperature": unit.set_temperature,
                        "temperature_unit": unit.temperature_unit,
                        "data_frequency": unit.data_frequency,
                        "data_quality": serialize_value(unit.data_quality)
                    }
                    facility_data["units"].append(unit_data)
                
                customer_data["facilities"].append(facility_data)
            
            export_data["customers"][customer_id] = customer_data
        
        # Use safe YAML dumping with no Python object references
        with open(filepath, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False, indent=2, allow_unicode=True)
        
        print(f"✅ Exported {len(self.generated_customers)} customers to {filepath}")


def reconstruct_customer_from_config(customer_id: str, config_data: dict) -> GeneratedCustomer:
    """Reconstruct a complete GeneratedCustomer object from YAML configuration data."""
    
    facilities = []
    for fac_data in config_data.get('facilities', []):
        units = []
        for unit_data in fac_data.get('units', []):
            unit = GeneratedUnit(
                id=unit_data['id'],
                name=unit_data['name'],
                size=unit_data['size'],
                size_unit=unit_data['size_unit'],
                set_temperature=unit_data['set_temperature'],
                temperature_unit=unit_data['temperature_unit'],
                data_frequency=unit_data['data_frequency'],
                data_quality=unit_data['data_quality'],
                facility_id=fac_data['id']
            )
            units.append(unit)
        
        facility = GeneratedFacility(
            id=fac_data['id'],
            name=fac_data['name'],
            city=fac_data['city'],
            country=fac_data['country'],
            units=units,
            customer_id=customer_id
        )
        facilities.append(facility)
    
    return GeneratedCustomer(
        id=customer_id,
        name=config_data['name'],
        data_sharing_method=config_data['data_sharing_method'],
        facilities=facilities,
        data_config=config_data.get('data_config', {}),
        data_quality=config_data.get('data_quality', {})
    )