# database/repositories/customer_repository.py
from typing import List, Optional
from uuid import UUID
from database.connection import DatabaseConnection
from database.models import Customer, Facility, StorageUnit

class CustomerRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def create_customer(self, customer: Customer) -> Customer:
        """Create a new customer"""
        query = """
        INSERT INTO customers (customer_code, name, data_sharing_method, data_frequency_seconds)
        VALUES (%s, %s, %s, %s)
        RETURNING id, created_at, updated_at
        """
        result = self.db.execute_query(query, (
            customer.customer_code,
            customer.name,
            customer.data_sharing_method,
            customer.data_frequency_seconds
        ))
        
        customer.id = result[0]['id']
        customer.created_at = result[0]['created_at']
        customer.updated_at = result[0]['updated_at']
        return customer
    
    def get_customer_by_code(self, customer_code: str) -> Optional[Customer]:
        """Get customer by code"""
        query = """
        SELECT id, customer_code, name, data_sharing_method, data_frequency_seconds,
               created_at, updated_at, is_active
        FROM customers 
        WHERE customer_code = %s AND is_active = TRUE
        """
        result = self.db.execute_query(query, (customer_code,))
        
        if not result:
            return None
        
        row = result[0]
        return Customer(
            id=row['id'],
            customer_code=row['customer_code'],
            name=row['name'],
            data_sharing_method=row['data_sharing_method'],
            data_frequency_seconds=row['data_frequency_seconds'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_active=row['is_active']
        )
    
    def get_all_customers(self) -> List[Customer]:
        """Get all active customers"""
        query = """
        SELECT id, customer_code, name, data_sharing_method, data_frequency_seconds,
               created_at, updated_at, is_active
        FROM customers 
        WHERE is_active = TRUE
        ORDER BY customer_code
        """
        results = self.db.execute_query(query)
        
        customers = []
        for row in results:
            customer = Customer(
                id=row['id'],
                customer_code=row['customer_code'],
                name=row['name'],
                data_sharing_method=row['data_sharing_method'],
                data_frequency_seconds=row['data_frequency_seconds'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                is_active=row['is_active']
            )
            customers.append(customer)
        
        return customers
    
    def get_customer_with_facilities(self, customer_code: str) -> Optional[Customer]:
        """Get customer with all facilities and units"""
        customer = self.get_customer_by_code(customer_code)
        if not customer:
            return None
        
        # Get facilities
        facilities_query = """
        SELECT id, facility_code, name, city, country, latitude, longitude, created_at
        FROM facilities 
        WHERE customer_id = %s
        ORDER BY facility_code
        """
        facility_results = self.db.execute_query(facilities_query, (customer.id,))
        
        facilities = []
        for fac_row in facility_results:
            facility = Facility(
                id=fac_row['id'],
                customer_id=customer.id,
                facility_code=fac_row['facility_code'],
                name=fac_row['name'],
                city=fac_row['city'],
                country=fac_row['country'],
                latitude=fac_row['latitude'],
                longitude=fac_row['longitude'],
                created_at=fac_row['created_at']
            )
            
            # Get storage units for this facility
            units_query = """
            SELECT id, unit_code, name, size_value, size_unit, set_temperature, 
                   temperature_unit, equipment_type, created_at
            FROM storage_units 
            WHERE facility_id = %s
            ORDER BY unit_code
            """
            unit_results = self.db.execute_query(units_query, (facility.id,))
            
            units = []
            for unit_row in unit_results:
                unit = StorageUnit(
                    id=unit_row['id'],
                    facility_id=facility.id,
                    unit_code=unit_row['unit_code'],
                    name=unit_row['name'],
                    size_value=float(unit_row['size_value']),
                    size_unit=unit_row['size_unit'],
                    set_temperature=float(unit_row['set_temperature']),
                    temperature_unit=unit_row['temperature_unit'],
                    equipment_type=unit_row['equipment_type'],
                    created_at=unit_row['created_at']
                )
                units.append(unit)
            
            facility.storage_units = units
            facilities.append(facility)
        
        customer.facilities = facilities
        return customer