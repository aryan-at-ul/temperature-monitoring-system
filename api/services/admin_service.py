# api/services/admin_service.py
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import logging
import hashlib
import secrets
from datetime import datetime 
from database.connection import db

logger = logging.getLogger(__name__)

class AdminService:
    @classmethod
    async def get_all_customers(cls, limit: int = 100, offset: int = 0):
        """
        Get all customers.
        """
     
        sql_query = """
            SELECT c.*, 
                (SELECT COUNT(*) FROM facilities f WHERE f.customer_id = c.id) as facility_count,
                (
                    SELECT COUNT(*) 
                    FROM storage_units su 
                    JOIN facilities f ON su.facility_id = f.id 
                    WHERE f.customer_id = c.id
                ) as unit_count,
                (SELECT COUNT(*) FROM temperature_readings tr WHERE tr.customer_id = c.id) as reading_count,
                (
                    SELECT MAX(tr.recorded_at) 
                    FROM temperature_readings tr 
                    WHERE tr.customer_id = c.id
                ) as last_reading_time
            FROM customers c
            ORDER BY c.created_at DESC
            LIMIT $1 OFFSET $2
        """
        

        customers = await db.fetch(sql_query, limit, offset)
        
     
        count_query = "SELECT COUNT(*) as count FROM customers"
        count_result = await db.fetchrow(count_query)
        total = count_result['count'] if count_result else 0
        
        return customers, total
    
    @classmethod
    async def get_customer(cls, customer_id: UUID):
        """
        Get a specific customer with detailed metrics.
        """
        query = """
            SELECT c.*, 
                (SELECT COUNT(*) FROM facilities f WHERE f.customer_id = c.id) as facility_count,
                (
                    SELECT COUNT(*) 
                    FROM storage_units su 
                    JOIN facilities f ON su.facility_id = f.id 
                    WHERE f.customer_id = c.id
                ) as unit_count,
                (SELECT COUNT(*) FROM temperature_readings tr WHERE tr.customer_id = c.id) as reading_count,
                (
                    SELECT MAX(tr.recorded_at) 
                    FROM temperature_readings tr 
                    WHERE tr.customer_id = c.id
                ) as last_reading_time
            FROM customers c
            WHERE c.id = $1
        """
        
        customer = await db.fetchrow(query, str(customer_id))
        return customer
    
    @classmethod
    async def create_customer(cls, customer_data):
        """
        Create a new customer.
        """
        insert_query = """
            INSERT INTO customers (
                customer_code, name, data_sharing_method, data_frequency_seconds,
                api_url, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            RETURNING *
        """
        
        result = await db.fetchrow(
            insert_query,
            customer_data.customer_code,
            customer_data.name,
            customer_data.data_sharing_method,
            customer_data.data_frequency_seconds,
            customer_data.api_url,
            customer_data.is_active
        )
        
        return result
    
    @classmethod
    async def update_customer(cls, customer_id: UUID, customer_data):
        """
        Update a customer.
        """

        update_fields = []
        params = []
        
        if customer_data.name is not None:
            update_fields.append(f"name = ${len(params) + 1}")
            params.append(customer_data.name)
            
        if customer_data.data_sharing_method is not None:
            update_fields.append(f"data_sharing_method = ${len(params) + 1}")
            params.append(customer_data.data_sharing_method)
            
        if customer_data.data_frequency_seconds is not None:
            update_fields.append(f"data_frequency_seconds = ${len(params) + 1}")
            params.append(customer_data.data_frequency_seconds)
            
        if customer_data.api_url is not None:
            update_fields.append(f"api_url = ${len(params) + 1}")
            params.append(customer_data.api_url)
            
        if customer_data.is_active is not None:
            update_fields.append(f"is_active = ${len(params) + 1}")
            params.append(customer_data.is_active)
        
  
        update_fields.append(f"updated_at = NOW()")
        params.append(str(customer_id))
        
        update_query = f"""
            UPDATE customers
            SET {", ".join(update_fields)}
            WHERE id = ${len(params)}
            RETURNING *
        """
        
        result = await db.fetchrow(update_query, *params)
        return result
    
    @classmethod
    async def get_all_facilities(cls, limit: int = 100, offset: int = 0, customer_id: Optional[UUID] = None):
        """
        Get all facilities, optionally filtered by customer.
        """
        # Build the query
        sql_query = """
            SELECT f.*, c.customer_code, c.name as customer_name,
                (SELECT COUNT(*) FROM storage_units su WHERE su.facility_id = f.id) as unit_count
            FROM facilities f
            JOIN customers c ON f.customer_id = c.id
        """
        
        params = []
        
        if customer_id:
            sql_query += " WHERE f.customer_id = $1"
            params.append(str(customer_id))
        
        sql_query += " ORDER BY f.created_at DESC LIMIT $2 OFFSET $3"
        params.extend([limit, offset])
        
   
        facilities = await db.fetch(sql_query, *params)
        

        count_query = "SELECT COUNT(*) as count FROM facilities"
        count_params = []
        
        if customer_id:
            count_query += " WHERE customer_id = $1"
            count_params.append(str(customer_id))
        
        count_result = await db.fetchrow(count_query, *count_params)
        total = count_result['count'] if count_result else 0
        
        return facilities, total
    
    @classmethod
    async def get_system_config(cls):
        """
        Get system configuration.
        """
        query = "SELECT * FROM system_config"
        config = await db.fetch(query)
      
        config_dict = {}
        for item in config:
            config_dict[item['key']] = {
                'value': item['value'],
                'description': item['description'],
                'updated_at': item['updated_at']
            }
        
        return config_dict
    
    @classmethod
    async def update_system_config(cls, key: str, value, description: Optional[str] = None):
        """
        Update system configuration.
        """

        check_query = "SELECT key FROM system_config WHERE key = $1"
        existing = await db.fetchrow(check_query, key)
        
        if existing:

            update_query = """
                UPDATE system_config
                SET value = $1, updated_at = NOW()
            """
            params = [value]
            
            if description:
                update_query += ", description = $2"
                params.append(description)
                
            update_query += " WHERE key = $" + str(len(params) + 1) + " RETURNING *"
            params.append(key)
            
            result = await db.fetchrow(update_query, *params)
        else:
            
            insert_query = """
                INSERT INTO system_config (key, value, description, updated_at)
                VALUES ($1, $2, $3, NOW())
                RETURNING *
            """
            result = await db.fetchrow(insert_query, key, value, description or "")
        
        return result
    
    @classmethod
    async def get_ingestion_logs(cls, limit: int = 100, offset: int = 0, 
                                 customer_id: Optional[UUID] = None, 
                                 status: Optional[str] = None,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None):
        """
        Get ingestion logs.
        """
      
        sql_query = """
            SELECT il.*, c.customer_code, c.name as customer_name
            FROM ingestion_logs il
            JOIN customers c ON il.customer_id = c.id
            WHERE 1=1
        """
        
        params = []
        param_count = 1
        
        if customer_id:
            sql_query += f" AND il.customer_id = ${param_count}"
            params.append(str(customer_id))
            param_count += 1
        
        if status:
            sql_query += f" AND il.status = ${param_count}"
            params.append(status)
            param_count += 1
            
        if start_date:
            sql_query += f" AND il.start_time >= ${param_count}"
            params.append(start_date)
            param_count += 1
            
        if end_date:
            sql_query += f" AND il.start_time <= ${param_count}"
            params.append(end_date)
            param_count += 1
        
        sql_query += " ORDER BY il.start_time DESC LIMIT $" + str(param_count) + " OFFSET $" + str(param_count + 1)
        params.extend([limit, offset])
        
    
        logs = await db.fetch(sql_query, *params)
        
        
        count_query = """
            SELECT COUNT(*) as count
            FROM ingestion_logs il
            WHERE 1=1
        """
        
        count_params = []
        param_count = 1
        
        if customer_id:
            count_query += f" AND il.customer_id = ${param_count}"
            count_params.append(str(customer_id))
            param_count += 1
        
        if status:
            count_query += f" AND il.status = ${param_count}"
            count_params.append(status)
            param_count += 1
            
        if start_date:
            count_query += f" AND il.start_time >= ${param_count}"
            count_params.append(start_date)
            param_count += 1
            
        if end_date:
            count_query += f" AND il.start_time <= ${param_count}"
            count_params.append(end_date)
            param_count += 1
        
        count_result = await db.fetchrow(count_query, *count_params)
        total = count_result['count'] if count_result else 0
        
        return logs, total