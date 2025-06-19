# api/services/customer_service.py
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import logging
import hashlib
import secrets
from database.connection import db

from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class CustomerService:
    @classmethod
    async def get_customer_profile(cls, customer_id: UUID):
        """
        Get a customer's profile.
        """
        query = "SELECT * FROM customers WHERE id = $1"
        customer = await db.fetchrow(query, str(customer_id))
        return customer
    
    @classmethod
    async def get_customer_detail(cls, customer_id: UUID):
        """
        Get detailed customer information including metrics.
        """
        # Get the customer
        customer = await cls.get_customer_profile(customer_id)
        
        if not customer:
            return None
        
        # Get facility count
        facility_count_query = """
            SELECT COUNT(*) as count
            FROM facilities
            WHERE customer_id = $1
        """
        facility_count = await db.fetchval(facility_count_query, str(customer_id))
        
        # Get unit count
        unit_count_query = """
            SELECT COUNT(*) as count
            FROM storage_units su
            JOIN facilities f ON su.facility_id = f.id
            WHERE f.customer_id = $1
        """
        unit_count = await db.fetchval(unit_count_query, str(customer_id))
        
        # Get active readings count
        readings_count_query = """
            SELECT COUNT(*) as count
            FROM temperature_readings
            WHERE customer_id = $1
        """
        readings_count = await db.fetchval(readings_count_query, str(customer_id))
        
        # Get last reading time
        last_reading_query = """
            SELECT MAX(recorded_at) as last_time
            FROM temperature_readings
            WHERE customer_id = $1
        """
        last_reading_time = await db.fetchval(last_reading_query, str(customer_id))
        
        # Combine the results
        result = dict(customer)
        result['facility_count'] = facility_count or 0
        result['unit_count'] = unit_count or 0
        result['active_readings_count'] = readings_count or 0
        result['last_reading_time'] = last_reading_time
        
        return result
    
    @classmethod
    async def update_customer(cls, customer_id: UUID, customer_data):
        """
        Update a customer's profile.
        """
        # Build the query dynamically based on the provided fields
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
        
        # Add updated_at and customer_id
        update_fields.append(f"updated_at = NOW()")
        params.append(str(customer_id))
        
        # If no fields to update, return the current customer
        if not update_fields:
            return await cls.get_customer_profile(customer_id)
        
        update_query = f"""
            UPDATE customers
            SET {", ".join(update_fields)}
            WHERE id = ${len(params)}
            RETURNING *
        """
        
        result = await db.fetchrow(update_query, *params)
        return result
    
    @classmethod
    async def get_customer_tokens(cls, customer_id: UUID):
        """
        Get a customer's API tokens.
        """
        query = """
            SELECT id, token_name, permissions, rate_limit_per_hour, 
                   accessible_units, expires_at, last_used_at, created_at, is_active
            FROM customer_tokens
            WHERE customer_id = $1
            ORDER BY created_at DESC
        """
        tokens = await db.fetch(query, str(customer_id))
        return tokens
    
    @classmethod
    async def create_token(cls, customer_id: UUID, token_data):
        """
        Create a new API token for a customer.
        """
        # Generate a secure random token
        token = secrets.token_hex(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Insert the token
        insert_query = """
            INSERT INTO customer_tokens (
                customer_id, token_hash, token_name, permissions, 
                rate_limit_per_hour, accessible_units, expires_at, is_active, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE, NOW())
            RETURNING id, token_name, permissions, rate_limit_per_hour, 
                     accessible_units, expires_at, created_at, is_active
        """
        
        result = await db.fetchrow(
            insert_query,
            str(customer_id),
            token_hash,
            token_data.token_name,
            token_data.permissions,
            token_data.rate_limit_per_hour,
            token_data.accessible_units,
            token_data.expires_at
        )
        
        # Return the token details with the plain token (will only be shown once)
        return {**dict(result), 'token': token}
    
    @classmethod
    async def revoke_token(cls, token_id: UUID, customer_id: UUID):
        """
        Revoke an API token.
        """
        update_query = """
            UPDATE customer_tokens
            SET is_active = FALSE
            WHERE id = $1 AND customer_id = $2
            RETURNING id, token_name, is_active
        """
        
        result = await db.fetchrow(update_query, str(token_id), str(customer_id))
        return result