from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Body
from typing import List, Optional
from datetime import datetime

from api.auth.token_auth import (
    get_current_customer, get_admin_user, 
    check_read_permission, check_write_permission
)
from api.models.customer import (
    AuthenticatedCustomer, AdminUser, CustomerResponse,
    CustomerCreate, CustomerUpdate, CustomerTokenResponse,
    CustomerTokenCreate, CustomerTokenUpdate
)
from api.models.responses import SuccessResponse, ErrorResponse
from api.utils.auth_utils import generate_token, hash_token, generate_customer_tokens
from database.connection import db

router = APIRouter()


@router.get(
    "/customer",
    response_model=CustomerResponse,
    summary="Get customer profile",
    description="Get the authenticated customer's profile",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_customer_profile(customer: AuthenticatedCustomer = Depends(check_read_permission)):
    """Get the authenticated customer's profile."""
    query = """
        SELECT id, customer_code, name, data_sharing_method, data_frequency_seconds,
               api_url, is_active, created_at, updated_at
        FROM customers
        WHERE id = $1
    """
    
    customer_data = await db.fetchrow(query, customer.customer_id)
    
    if not customer_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
        
    return CustomerResponse(**customer_data)


@router.get(
    "/customer/tokens",
    response_model=List[CustomerTokenResponse],
    summary="Get customer tokens",
    description="Get the authenticated customer's API tokens",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_customer_tokens(customer: AuthenticatedCustomer = Depends(check_read_permission)):
    """Get the authenticated customer's API tokens."""
    query = """
        SELECT id, customer_id, token_name, permissions, accessible_units,
               rate_limit_per_hour, expires_at, last_used_at, created_at, is_active
        FROM customer_tokens
        WHERE customer_id = $1
        ORDER BY created_at DESC
    """
    
    tokens = await db.fetch(query, customer.customer_id)
    
    return [CustomerTokenResponse(**token) for token in tokens]


@router.post(
    "/customer/tokens",
    response_model=CustomerTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create token",
    description="Create a new API token for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def create_customer_token(
    token_data: CustomerTokenCreate,
    customer: AuthenticatedCustomer = Depends(check_write_permission)
):
    """Create a new API token for the authenticated customer."""
    # Generate a new token
    token = generate_token()
    token_hash = hash_token(token)
    
    query = """
        INSERT INTO customer_tokens
            (id, customer_id, token_hash, token_name, permissions, accessible_units, 
             rate_limit_per_hour, expires_at, created_at, is_active)
        VALUES
            ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id, customer_id, token_name, permissions, accessible_units,
                  rate_limit_per_hour, expires_at, last_used_at, created_at, is_active
    """
    
    token_id = str(datetime.uuid4())
    created_at = datetime.now()
    
    result = await db.fetchrow(
        query,
        token_id,
        customer.customer_id,
        token_hash,
        token_data.token_name,
        token_data.permissions,
        token_data.accessible_units,
        token_data.rate_limit_per_hour,
        token_data.expires_at,
        created_at,
        True  # is_active
    )
    
    # Return the token with the raw token included (only time it's returned)
    response = CustomerTokenResponse(**result)
    response.token = token
    
    return response


@router.put(
    "/customer/tokens/{token_id}",
    response_model=CustomerTokenResponse,
    summary="Update token",
    description="Update an existing API token",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Token not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def update_customer_token(
    token_id: str = Path(..., description="Token ID"),
    token_data: CustomerTokenUpdate = Body(...),
    customer: AuthenticatedCustomer = Depends(check_write_permission)
):
    """Update an existing API token."""
    # Check if token exists and belongs to customer
    token_exists = await db.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM customer_tokens 
            WHERE id = $1 AND customer_id = $2
        )
        """,
        token_id, customer.customer_id
    )
    
    if not token_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
        
    # Build update query
    update_fields = []
    params = [token_id]
    param_index = 2
    
    if token_data.token_name is not None:
        update_fields.append(f"token_name = ${param_index}")
        params.append(token_data.token_name)
        param_index += 1
        
    if token_data.permissions is not None:
        update_fields.append(f"permissions = ${param_index}")
        params.append(token_data.permissions)
        param_index += 1
        
    if token_data.accessible_units is not None:
        update_fields.append(f"accessible_units = ${param_index}")
        params.append(token_data.accessible_units)
        param_index += 1
        
    if token_data.rate_limit_per_hour is not None:
        update_fields.append(f"rate_limit_per_hour = ${param_index}")
        params.append(token_data.rate_limit_per_hour)
        param_index += 1
        
    if token_data.expires_at is not None:
        update_fields.append(f"expires_at = ${param_index}")
        params.append(token_data.expires_at)
        param_index += 1
        
    if token_data.is_active is not None:
        update_fields.append(f"is_active = ${param_index}")
        params.append(token_data.is_active)
        param_index += 1
        
    # If no fields to update
    if not update_fields:
        # Return current token data
        query = """
            SELECT id, customer_id, token_name, permissions, accessible_units,
                   rate_limit_per_hour, expires_at, last_used_at, created_at, is_active
            FROM customer_tokens
            WHERE id = $1
        """
        
        token = await db.fetchrow(query, token_id)
        return CustomerTokenResponse(**token)
        
    # Execute update
    query = f"""
        UPDATE customer_tokens
        SET {", ".join(update_fields)}
        WHERE id = $1
        RETURNING id, customer_id, token_name, permissions, accessible_units,
                  rate_limit_per_hour, expires_at, last_used_at, created_at, is_active
    """
    
    result = await db.fetchrow(query, *params)
    
    return CustomerTokenResponse(**result)


@router.delete(
    "/customer/tokens/{token_id}",
    response_model=SuccessResponse,
    summary="Delete token",
    description="Delete an API token",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Token not found"},
    }
)
async def delete_customer_token(
    token_id: str = Path(..., description="Token ID"),
    customer: AuthenticatedCustomer = Depends(check_write_permission)
):
    """Delete an API token."""
    # Check if token exists and belongs to customer
    token_exists = await db.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM customer_tokens 
            WHERE id = $1 AND customer_id = $2
        )
        """,
        token_id, customer.customer_id
    )
    
    if not token_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )