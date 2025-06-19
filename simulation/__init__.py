# # simulation/__init__.py
# """
# Temperature Monitoring System - Simulation Module

# This module provides comprehensive simulation capabilities for generating
# realistic temperature monitoring data from various customer types.
# """

# # Import order matters - start with base classes
# from .profile_templates import (
#     CustomerTemplate,
#     FacilityTemplate, 
#     UnitTemplate,
#     DataQualityProfile,
#     DataSharingMethod,
#     TemperatureUnit,
#     SizeUnit,
#     EquipmentReliability,
#     CUSTOMER_TEMPLATES
# )

# from .customer_generator import (
#     CustomerGenerator, 
#     GeneratedCustomer, 
#     GeneratedFacility, 
#     GeneratedUnit
# )

# from .enhanced_data_generator import (
#     EnhancedTemperatureGenerator,
#     TemperatureReading,
#     generate_customer_data
# )

# from .csv_generator import CSVGenerator

# from .api_simulator import (
#     CustomerAPISimulator,
#     MultiCustomerAPIManager,
#     start_single_api_server,
#     start_multiple_api_servers
# )

# __version__ = "1.0.0"
# __author__ = "Temperature Monitoring Team"

# # Main simulation functions for easy import
# __all__ = [
#     # Core classes
#     'CustomerGenerator',
#     'EnhancedTemperatureGenerator', 
#     'CSVGenerator',
#     'CustomerAPISimulator',
#     'MultiCustomerAPIManager',
    
#     # Data classes
#     'GeneratedCustomer',
#     'GeneratedFacility', 
#     'GeneratedUnit',
#     'TemperatureReading',
#     'CustomerTemplate',
#     'FacilityTemplate',
#     'UnitTemplate', 
#     'DataQualityProfile',
    
#     # Enums
#     'DataSharingMethod',
#     'TemperatureUnit', 
#     'SizeUnit',
#     'EquipmentReliability',
    
#     # Functions
#     'generate_customer_data',
#     'start_single_api_server',
#     'start_multiple_api_servers',
    
#     # Constants
#     'CUSTOMER_TEMPLATES',
# ]

# # Module-level convenience functions
# def quick_generate_customer(customer_id: str, template_name: str = 'food_storage') -> GeneratedCustomer:
#     """Quick function to generate a single customer"""
#     generator = CustomerGenerator()
#     return generator.generate_customer(customer_id, template_name)

# def quick_generate_data(customer_id: str, template_name: str = 'food_storage', hours: int = 24):
#     """Quick function to generate customer and data"""
#     customer = quick_generate_customer(customer_id, template_name)
#     return generate_customer_data(customer, hours)

# def get_assignment_customers():
#     """Get the exact customers A and B from the assignment"""
#     generator = CustomerGenerator()
    
#     # Generate Customer A (exact assignment specs)
#     customer_a = generator.generate_assignment_customer('A')
    
#     # Generate Customer B (exact assignment specs)  
#     customer_b = generator.generate_assignment_customer('B')
    
#     return {'A': customer_a, 'B': customer_b}


# simulation/__init__.py
"""
Temperature Monitoring System - Simulation Module

This module provides comprehensive simulation capabilities for generating
realistic temperature monitoring data from various customer types.
"""

# Import order matters - start with base classes
from .profile_templates import (
    CustomerTemplate,
    FacilityTemplate, 
    UnitTemplate,
    DataQualityProfile,
    DataSharingMethod,
    TemperatureUnit,
    SizeUnit,
    EquipmentReliability,
    CUSTOMER_TEMPLATES
)

from .customer_generator import (
    CustomerGenerator, 
    GeneratedCustomer, 
    GeneratedFacility, 
    GeneratedUnit
)

from .enhanced_data_generator import (
    EnhancedTemperatureGenerator,
    TemperatureReading,
    generate_customer_data
)

# --- Existing imports (unchanged) ---
from .csv_generator import CSVGenerator

from .api_simulator import (
    CustomerAPISimulator,
    MultiCustomerAPIManager,
    start_single_api_server,
    start_multiple_api_servers
)

# --- NEW import for the unified service manager ---
from .manager import SimulationManager


__version__ = "1.0.0"
__author__ = "Temperature Monitoring Team"

# Main simulation functions for easy import
__all__ = [
    # --- Existing core classes (unchanged) ---
    'CustomerGenerator',
    'EnhancedTemperatureGenerator', 
    'CSVGenerator',
    'CustomerAPISimulator',
    'MultiCustomerAPIManager',
    
    # --- NEW class for the unified service ---
    'SimulationManager',

    # --- Existing data classes (unchanged) ---
    'GeneratedCustomer',
    'GeneratedFacility', 
    'GeneratedUnit',
    'TemperatureReading',
    'CustomerTemplate',
    'FacilityTemplate',
    'UnitTemplate', 
    'DataQualityProfile',
    
    # --- Existing Enums (unchanged) ---
    'DataSharingMethod',
    'TemperatureUnit', 
    'SizeUnit',
    'EquipmentReliability',
    
    # --- Existing functions (unchanged) ---
    'generate_customer_data',
    'start_single_api_server',
    'start_multiple_api_servers',
    
    # --- Existing constants (unchanged) ---
    'CUSTOMER_TEMPLATES',
]

# --- Existing Module-level convenience functions (unchanged) ---
def quick_generate_customer(customer_id: str, template_name: str = 'food_storage') -> GeneratedCustomer:
    """Quick function to generate a single customer"""
    generator = CustomerGenerator()
    return generator.generate_customer(customer_id, template_name)

def quick_generate_data(customer_id: str, template_name: str = 'food_storage', hours: int = 24):
    """Quick function to generate customer and data"""
    customer = quick_generate_customer(customer_id, template_name)
    return generate_customer_data(customer, hours)

def get_assignment_customers():
    """Get the exact customers A and B from the assignment"""
    generator = CustomerGenerator()
    
    # Generate Customer A (exact assignment specs)
    customer_a = generator.generate_assignment_customer('A')
    
    # Generate Customer B (exact assignment specs)  
    customer_b = generator.generate_assignment_customer('B')
    
    return {'A': customer_a, 'B': customer_b}