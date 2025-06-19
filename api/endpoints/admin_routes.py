# api/endpoints/admin_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import logging
import traceback

from api.auth.token_auth import get_admin_user
from api.models.customer import CustomerDetail, CustomerCreate, CustomerUpdate, TokenCreate
from api.models.facility import FacilityDetail, FacilityCreate, FacilityUpdate, StorageUnitDetail
from api.models.responses import PaginatedResponse, ErrorResponse
from api.services.admin_service import AdminService
from api.services.customer_service import CustomerService
from api.services.facility_service import FacilityService
from database.connection import db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/admin/customers",
    response_model=PaginatedResponse[CustomerDetail],
    summary="[Admin] Get all customers",
    description="Get a list of all customers (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_all_customers(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(get_admin_user)
):
    """
    Get a list of all customers.
    
    Only accessible to admin users.
    """
    try:
        customers, total = await AdminService.get_all_customers(limit, offset)
        
        # Calculate pagination info
        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return PaginatedResponse(
            items=customers,
            total=total,
            page=page,
            page_size=limit,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Error in get_all_customers: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving customers: {str(e)}"
        )

@router.get(
    "/admin/customers/{customer_id}",
    response_model=CustomerDetail,
    summary="[Admin] Get customer",
    description="Get a specific customer (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Customer not found"},
    }
)
async def get_customer(
    customer_id: UUID = Path(..., description="Customer ID"),
    admin: dict = Depends(get_admin_user)
):
    """
    Get a specific customer.
    
    Only accessible to admin users.
    """
    try:
        customer = await AdminService.get_customer(customer_id)
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_customer: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving customer: {str(e)}"
        )

@router.post(
    "/admin/customers",
    response_model=CustomerDetail,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create customer",
    description="Create a new customer (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def create_customer(
    customer: CustomerCreate,
    admin: dict = Depends(get_admin_user)
):
    """
    Create a new customer.
    
    Only accessible to admin users.
    """
    try:
        result = await AdminService.create_customer(customer)
        return result
    except Exception as e:
        logger.error(f"Error in create_customer: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating customer: {str(e)}"
        )

@router.put(
    "/admin/customers/{customer_id}",
    response_model=CustomerDetail,
    summary="[Admin] Update customer",
    description="Update a customer (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Customer not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def update_customer(
    customer_id: UUID = Path(..., description="Customer ID"),
    customer: CustomerUpdate = None,
    admin: dict = Depends(get_admin_user)
):
    """
    Update a customer.
    
    Only accessible to admin users.
    """
    try:
        result = await AdminService.update_customer(customer_id, customer)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_customer: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating customer: {str(e)}"
        )

@router.get(
    "/admin/customers/{customer_id}/tokens",
    response_model=List[dict],
    summary="[Admin] Get customer tokens",
    description="Get a customer's API tokens (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Customer not found"},
    }
)
async def get_customer_tokens(
    customer_id: UUID = Path(..., description="Customer ID"),
    admin: dict = Depends(get_admin_user)
):
    """
    Get a customer's API tokens.
    
    Only accessible to admin users.
    """
    try:
        # First, verify the customer exists
        customer_query = "SELECT id FROM customers WHERE id = $1"
        customer = await db.fetchrow(customer_query, str(customer_id))
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        tokens = await CustomerService.get_customer_tokens(customer_id)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_customer_tokens: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving customer tokens: {str(e)}"
        )

@router.post(
    "/admin/customers/{customer_id}/tokens",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create customer token",
    description="Create a new API token for a customer (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Customer not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def create_customer_token(
    customer_id: UUID = Path(..., description="Customer ID"),
    token_data: TokenCreate = None,
    admin: dict = Depends(get_admin_user)
):
    """
    Create a new API token for a customer.
    
    Only accessible to admin users. The token value is only returned once and cannot be retrieved later.
    """
    try:
        # First, verify the customer exists
        customer_query = "SELECT id FROM customers WHERE id = $1"
        customer = await db.fetchrow(customer_query, str(customer_id))
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        result = await CustomerService.create_token(customer_id, token_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_customer_token: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating customer token: {str(e)}"
        )

@router.get(
    "/admin/facilities",
    response_model=PaginatedResponse[FacilityDetail],
    summary="[Admin] Get all facilities",
    description="Get a list of all facilities (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_all_facilities(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    admin: dict = Depends(get_admin_user)
):
    """
    Get a list of all facilities.
    
    Only accessible to admin users. Can be filtered by customer ID.
    """
    try:
        facilities, total = await AdminService.get_all_facilities(limit, offset, customer_id)
        
        # Calculate pagination info
        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return PaginatedResponse(
            items=facilities,
            total=total,
            page=page,
            page_size=limit,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Error in get_all_facilities: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving facilities: {str(e)}"
        )

@router.get(
    "/admin/config",
    response_model=Dict[str, Dict[str, Any]],
    summary="[Admin] Get system configuration",
    description="Get system configuration (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_system_config(
    admin: dict = Depends(get_admin_user)
):
    """
    Get system configuration.
    
    Only accessible to admin users.
    """
    try:
        config = await AdminService.get_system_config()
        return config
    except Exception as e:
        logger.error(f"Error in get_system_config: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system configuration: {str(e)}"
        )

@router.put(
    "/admin/config/{key}",
    response_model=dict,
    summary="[Admin] Update system configuration",
    description="Update system configuration (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def update_system_config(
    key: str = Path(..., description="Configuration key"),
    value: Any = Query(..., description="Configuration value"),
    description: Optional[str] = Query(None, description="Configuration description"),
    admin: dict = Depends(get_admin_user)
):
    """
    Update system configuration.
    
    Only accessible to admin users.
    """
    try:
        result = await AdminService.update_system_config(key, value, description)
        return result
    except Exception as e:
        logger.error(f"Error in update_system_config: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating system configuration: {str(e)}"
        )

@router.get(
    "/admin/ingestion/logs",
    response_model=PaginatedResponse[dict],
    summary="[Admin] Get ingestion logs",
    description="Get ingestion logs (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_ingestion_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by status (success, failure)"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    admin: dict = Depends(get_admin_user)
):
    """
    Get ingestion logs.
    
    Only accessible to admin users. Can be filtered by customer ID, status, and date range.
    """
    try:
        logs, total = await AdminService.get_ingestion_logs(
            limit, offset, customer_id, status, start_date, end_date
        )
        
        # Calculate pagination info
        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return PaginatedResponse(
            items=logs,
            total=total,
            page=page,
            page_size=limit,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Error in get_ingestion_logs: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving ingestion logs: {str(e)}"
        )