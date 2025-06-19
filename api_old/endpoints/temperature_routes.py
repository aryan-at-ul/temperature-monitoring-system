from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from datetime import datetime, timedelta

from api.auth.token_auth import get_current_customer, get_admin_user, check_read_permission
from api.models.customer import AuthenticatedCustomer, AdminUser
from api.models.temperature import (
    TemperatureReadingDetail, TemperatureQuery, TemperatureStats,
    TemperatureAggregation, AggregationResult
)
from api.models.responses import PaginatedResponse, ErrorResponse
from api.services.temperature_service import TemperatureService
from database.connection import db

router = APIRouter()


@router.get(
    "/temperature",
    response_model=PaginatedResponse[TemperatureReadingDetail],
    summary="Get temperature readings",
    description="Get temperature readings for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_temperature_readings(
    query: TemperatureQuery = Depends(),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """
    Get temperature readings for the authenticated customer.
    
    Query parameters can be used to filter and paginate the results.
    """
    readings, total = await TemperatureService.get_readings(customer, query)
    
    # Calculate pagination info
    page = (query.offset // query.limit) + 1 if query.limit > 0 else 1
    pages = (total + query.limit - 1) // query.limit if query.limit > 0 else 1
    
    return PaginatedResponse(
        items=readings,
        total=total,
        page=page,
        page_size=query.limit,
        pages=pages
    )


@router.get(
    "/temperature/facility/{facility_id}",
    response_model=PaginatedResponse[TemperatureReadingDetail],
    summary="Get temperature readings for a facility",
    description="Get temperature readings for a specific facility",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
    }
)
async def get_facility_temperature_readings(
    facility_id: str = Path(..., description="Facility ID"),
    query: TemperatureQuery = Depends(),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """
    Get temperature readings for a specific facility.
    
    Query parameters can be used to filter and paginate the results.
    """
    readings, total = await TemperatureService.get_readings(
        customer, query, facility_id=facility_id
    )
    
    if not readings and total == 0:
        # Check if facility exists and belongs to customer
        # This is a simple check to verify that the facility ID is valid
        facility_exists = await db.fetchval(
            "SELECT EXISTS(SELECT 1 FROM facilities WHERE id = $1 AND customer_id = $2)",
            facility_id, customer.customer_id
        )
        
        if not facility_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
    
    # Calculate pagination info
    page = (query.offset // query.limit) + 1 if query.limit > 0 else 1
    pages = (total + query.limit - 1) // query.limit if query.limit > 0 else 1
    
    return PaginatedResponse(
        items=readings,
        total=total,
        page=page,
        page_size=query.limit,
        pages=pages
    )


@router.get(
    "/temperature/unit/{unit_id}",
    response_model=PaginatedResponse[TemperatureReadingDetail],
    summary="Get temperature readings for a storage unit",
    description="Get temperature readings for a specific storage unit",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Storage unit not found"},
    }
)
async def get_unit_temperature_readings(
    unit_id: str = Path(..., description="Storage unit ID"),
    query: TemperatureQuery = Depends(),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """
    Get temperature readings for a specific storage unit.
    
    Query parameters can be used to filter and paginate the results.
    """
    # First, check if the unit exists and belongs to the customer's facilities
    unit_query = """
        SELECT su.id, f.customer_id
        FROM storage_units su
        JOIN facilities f ON su.facility_id = f.id
        WHERE su.id = $1 AND f.customer_id = $2
    """
    unit = await db.fetchrow(unit_query, unit_id, customer.customer_id)
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage unit not found"
        )
    
    readings, total = await TemperatureService.get_readings(
        customer, query, storage_unit_id=unit_id
    )
    
    # Calculate pagination info
    page = (query.offset // query.limit) + 1 if query.limit > 0 else 1
    pages = (total + query.limit - 1) // query.limit if query.limit > 0 else 1
    
    return PaginatedResponse(
        items=readings,
        total=total,
        page=page,
        page_size=query.limit,
        pages=pages
    )


@router.get(
    "/temperature/stats",
    response_model=TemperatureStats,
    summary="Get temperature statistics",
    description="Get temperature statistics for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_temperature_stats(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """
    Get temperature statistics for the authenticated customer.
    
    Optional start_date and end_date parameters can be used to filter the time range.
    """
    stats = await TemperatureService.get_statistics(
        customer.customer_id, start_date, end_date
    )
    
    return stats


@router.get(
    "/temperature/stats/facility/{facility_id}",
    response_model=TemperatureStats,
    summary="Get temperature statistics for a facility",
    description="Get temperature statistics for a specific facility",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
    }
)
async def get_facility_temperature_stats(
    facility_id: str = Path(..., description="Facility ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """
    Get temperature statistics for a specific facility.
    
    Optional start_date and end_date parameters can be used to filter the time range.
    """
    # Check if facility exists and belongs to customer
    facility_exists = await db.fetchval(
        "SELECT EXISTS(SELECT 1 FROM facilities WHERE id = $1 AND customer_id = $2)",
        facility_id, customer.customer_id
    )
    
    if not facility_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    stats = await TemperatureService.get_statistics(
        customer.customer_id, start_date, end_date, facility_id=facility_id
    )
    
    return stats


@router.get(
    "/temperature/stats/unit/{unit_id}",
    response_model=TemperatureStats,
    summary="Get temperature statistics for a storage unit",
    description="Get temperature statistics for a specific storage unit",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Storage unit not found"},
    }
)
async def get_unit_temperature_stats(
    unit_id: str = Path(..., description="Storage unit ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """
    Get temperature statistics for a specific storage unit.
    
    Optional start_date and end_date parameters can be used to filter the time range.
    """
    # Check if unit exists and belongs to customer's facilities
    unit_query = """
        SELECT su.id, f.customer_id
        FROM storage_units su
        JOIN facilities f ON su.facility_id = f.id
        WHERE su.id = $1 AND f.customer_id = $2
    """
    unit = await db.fetchrow(unit_query, unit_id, customer.customer_id)
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage unit not found"
        )
    
    stats = await TemperatureService.get_statistics(
        customer.customer_id, start_date, end_date, storage_unit_id=unit_id
    )
    
    return stats


@router.post(
    "/temperature/aggregate",
    response_model=List[AggregationResult],
    summary="Aggregate temperature data",
    description="Aggregate temperature data with various grouping options",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def aggregate_temperature_data(
    aggregation: TemperatureAggregation,
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """
    Aggregate temperature data with various grouping options.
    
    You can group by hour, day, week, month, facility, unit, or sensor.
    Available aggregation functions are avg, min, max, and count.
    """
    try:
        results = await TemperatureService.get_aggregation(
            customer.customer_id, aggregation
        )
        return results
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


# Admin routes for temperature data

@router.get(
    "/admin/temperature",
    response_model=PaginatedResponse[TemperatureReadingDetail],
    summary="[Admin] Get temperature readings for all customers",
    description="Get temperature readings across all customers (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def admin_get_temperature_readings(
    query: TemperatureQuery = Depends(),
    admin: AdminUser = Depends(get_admin_user),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID")
):
    """
    Get temperature readings across all customers.
    
    Only accessible to admin users. Query parameters can be used to filter and paginate the results.
    """
    readings, total = await TemperatureService.get_admin_readings(
        query, customer_id=customer_id
    )
    
    # Calculate pagination info
    page = (query.offset // query.limit) + 1 if query.limit > 0 else 1
    pages = (total + query.limit - 1) // query.limit if query.limit > 0 else 1
    
    return PaginatedResponse(
        items=readings,
        total=total,
        page=page,
        page_size=query.limit,
        pages=pages
    )


@router.get(
    "/admin/temperature/facility/{facility_id}",
    response_model=PaginatedResponse[TemperatureReadingDetail],
    summary="[Admin] Get temperature readings for a facility",
    description="Get temperature readings for a specific facility (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
    }
)
async def admin_get_facility_temperature_readings(
    facility_id: str = Path(..., description="Facility ID"),
    query: TemperatureQuery = Depends(),
    admin: AdminUser = Depends(get_admin_user)
):
    """
    Get temperature readings for a specific facility across all customers.
    
    Only accessible to admin users. Query parameters can be used to filter and paginate the results.
    """
    # Check if facility exists
    facility_exists = await db.fetchval(
        "SELECT EXISTS(SELECT 1 FROM facilities WHERE id = $1)",
        facility_id
    )
    
    if not facility_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    readings, total = await TemperatureService.get_admin_readings(
        query, facility_id=facility_id
    )
    
    # Calculate pagination info
    page = (query.offset // query.limit) + 1 if query.limit > 0 else 1
    pages = (total + query.limit - 1) // query.limit if query.limit > 0 else 1
    
    return PaginatedResponse(
        items=readings,
        total=total,
        page=page,
        page_size=query.limit,
        pages=pages
    )


@router.get(
    "/admin/temperature/unit/{unit_id}",
    response_model=PaginatedResponse[TemperatureReadingDetail],
    summary="[Admin] Get temperature readings for a storage unit",
    description="Get temperature readings for a specific storage unit (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Storage unit not found"},
    }
)
async def admin_get_unit_temperature_readings(
    unit_id: str = Path(..., description="Storage unit ID"),
    query: TemperatureQuery = Depends(),
    admin: AdminUser = Depends(get_admin_user)
):
    """
    Get temperature readings for a specific storage unit across all customers.
    
    Only accessible to admin users. Query parameters can be used to filter and paginate the results.
    """
    # Check if unit exists
    unit_exists = await db.fetchval(
        "SELECT EXISTS(SELECT 1 FROM storage_units WHERE id = $1)",
        unit_id
    )
    
    if not unit_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage unit not found"
        )
    
    readings, total = await TemperatureService.get_admin_readings(
        query, storage_unit_id=unit_id
    )
    
    # Calculate pagination info
    page = (query.offset // query.limit) + 1 if query.limit > 0 else 1
    pages = (total + query.limit - 1) // query.limit if query.limit > 0 else 1
    
    return PaginatedResponse(
        items=readings,
        total=total,
        page=page,
        page_size=query.limit,
        pages=pages
    )