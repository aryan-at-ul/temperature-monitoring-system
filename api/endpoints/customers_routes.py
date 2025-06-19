# api/endpoints/customers_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
import logging
import traceback
from datetime import datetime
from api.auth.token_auth import get_current_customer, check_read_permission, check_write_permission
from api.models.customer import CustomerProfile, CustomerUpdate, CustomerToken, TokenCreate, CustomerDetail
from api.models.responses import ErrorResponse
from api.services.customer_service import CustomerService
from database.connection import db

from database.connection import DatabaseConnection  

db_manager = DatabaseConnection() 



router = APIRouter()
logger = logging.getLogger(__name__)



async def get_db():
    """Get database connection"""
    return db_manager


@router.get(
    "/customers/profile",
    response_model=CustomerDetail,
    summary="Get customer profile",
    description="Get the authenticated customer's profile",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Customer not found"},
    }
)
async def get_customer_profile(
    customer: dict = Depends(check_read_permission)
):
    """
    Get the authenticated customer's profile.
    """
    try:
        profile = await CustomerService.get_customer_detail(customer['id'])
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_customer_profile: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving customer profile: {str(e)}"
        )

@router.put(
    "/customers/profile",
    response_model=CustomerProfile,
    summary="Update customer profile",
    description="Update the authenticated customer's profile",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Customer not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def update_customer_profile(
    customer_update: CustomerUpdate,
    customer: dict = Depends(check_write_permission)
):
    """
    Update the authenticated customer's profile.
    """
    try:
        result = await CustomerService.update_customer(customer['id'], customer_update)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_customer_profile: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating customer profile: {str(e)}"
        )



@router.get(
    "/customers/tokens",
    response_model=List[CustomerToken],
    summary="Get customer tokens",
    description="Get the authenticated customer's API tokens",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_customer_tokens(
    customer: dict = Depends(check_read_permission),
    db = Depends(get_db)
):
    """
    Get the authenticated customer's API tokens.
    """
    try:
        # Fix: Use the correct table name 'customer_tokens' instead of 'api_tokens'
        tokens_query = """
            SELECT 
                id,
                token_name,
                permissions,
                accessible_units,
                created_at,
                last_used_at as last_used,
                rate_limit_per_hour,
                is_active
            FROM customer_tokens 
            WHERE customer_id = $1 AND is_active = true
            ORDER BY created_at DESC
        """
        
        tokens_data = await db.fetch(tokens_query, customer['id'])
        
        # Convert to proper format
        tokens = []
        for token_row in tokens_data:
            token_dict = dict(token_row)
            
            # Ensure permissions is a list
            if isinstance(token_dict['permissions'], str):
                import json
                try:
                    token_dict['permissions'] = json.loads(token_dict['permissions'])
                except:
                    token_dict['permissions'] = [token_dict['permissions']]
            elif not isinstance(token_dict['permissions'], list):
                token_dict['permissions'] = []
            
            # Ensure accessible_units is a dict
            if isinstance(token_dict['accessible_units'], str):
                import json
                try:
                    token_dict['accessible_units'] = json.loads(token_dict['accessible_units'])
                except:
                    token_dict['accessible_units'] = {}
            elif not isinstance(token_dict['accessible_units'], dict):
                token_dict['accessible_units'] = {}
            
            tokens.append(token_dict)
        
        return tokens
    except Exception as e:
        logger.error(f"Error in get_customer_tokens: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving customer tokens: {str(e)}"
        )


@router.post(
    "/customers/tokens",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create customer token",
    description="Create a new API token for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def create_customer_token(
    token_data: TokenCreate,
    customer: dict = Depends(check_write_permission)
):
    """
    Create a new API token for the authenticated customer.
    
    The token value is only returned once and cannot be retrieved later.
    """
    try:
        result = await CustomerService.create_token(customer['id'], token_data)
        return result
    except Exception as e:
        logger.error(f"Error in create_customer_token: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating customer token: {str(e)}"
        )

@router.delete(
    "/customers/tokens/{token_id}",
    response_model=CustomerToken,
    summary="Revoke customer token",
    description="Revoke an API token for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Token not found"},
    }
)
async def revoke_customer_token(
    token_id: UUID,
    customer: dict = Depends(check_write_permission)
):
    """
    Revoke an API token for the authenticated customer.
    """
    try:
        result = await CustomerService.revoke_token(token_id, customer['id'])
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in revoke_customer_token: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking customer token: {str(e)}"
        )