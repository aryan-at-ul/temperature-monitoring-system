
# api/services/customer_service.py
from typing import List, Optional
from database.connection import DatabaseConnection
from api.models.responses import Customer, Facility, StorageUnit, TemperatureReading

class CustomerService:
    """Business logic for customer operations"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def get_customer(self, customer_code: str) -> Optional[Customer]:
        """Get customer with facilities and units"""
        
        # Get customer
        customer_query = """
        SELECT id, customer_code, name, data_sharing_method
        FROM customers 
        WHERE customer_code = %s AND is_active = TRUE
        """
        
        customer_result = self.db.execute_query(customer_query, (customer_code,))
        if not customer_result:
            return None
        
        customer_data = customer_result[0]
        
        # Get facilities with units
        facilities_query = """
        SELECT 
            f.id as facility_id,
            f.facility_code,
            f.name as facility_name,
            f.city,
            f.country,
            su.id as unit_id,
            su.unit_code,
            su.name as unit_name,
            su.size_value,
            su.size_unit,
            su.set_temperature,
            su.temperature_unit,
            su.equipment_type
        FROM facilities f
        LEFT JOIN storage_units su ON f.id = su.facility_id
        WHERE f.customer_id = %s
        ORDER BY f.facility_code, su.unit_code
        """
        
        facilities_data = self.db.execute_query(facilities_query, (customer_data['id'],))
        
        # Group by facility
        facilities_dict = {}
        for row in facilities_data:
            facility_id = str(row['facility_id'])
            
            if facility_id not in facilities_dict:
                facilities_dict[facility_id] = {
                    'id': facility_id,
                    'facility_code': row['facility_code'],
                    'name': row['facility_name'],
                    'city': row['city'],
                    'country': row['country'],
                    'storage_units': []
                }
            
            if row['unit_id']:  # If unit exists
                unit = StorageUnit(
                    id=str(row['unit_id']),
                    unit_code=row['unit_code'],
                    name=row['unit_name'],
                    size_value=float(row['size_value']),
                    size_unit=row['size_unit'],
                    set_temperature=float(row['set_temperature']),
                    temperature_unit=row['temperature_unit'],
                    equipment_type=row['equipment_type'],
                    latest_reading=None  # Can be populated separately if needed
                )
                facilities_dict[facility_id]['storage_units'].append(unit)
        
        # Convert to Pydantic models
        facilities = [
            Facility(**facility_data) 
            for facility_data in facilities_dict.values()
        ]
        
        return Customer(
            id=str(customer_data['id']),
            customer_code=customer_data['customer_code'],
            name=customer_data['name'],
            data_sharing_method=customer_data['data_sharing_method'],
            facilities=facilities
        )
    
    def get_customers(self) -> List[Customer]:
        """Get all customers (admin only)"""
        
        customers_query = """
        SELECT customer_code
        FROM customers 
        WHERE is_active = TRUE
        ORDER BY customer_code
        """
        
        customers = self.db.execute_query(customers_query)
        
        return [
            self.get_customer(customer['customer_code']) 
            for customer in customers
        ]