from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Body
from typing import List, Optional
from pydantic import UUID4

from api.auth.token_auth import (
    get_current_customer, get_admin_user, 
    check_read_permission, check_write_permission
)
from api.models.customer import AuthenticatedCustomer, AdminUser
from api.models.facility import (
    FacilityResponse, StorageUnitResponse, FacilityWithUnits,
    CustomerFacilities, FacilityCreate, FacilityUpdate,
    StorageUnitCreate, StorageUnitUpdate
)
from api.models.responses import SuccessResponse, ErrorResponse
from api.services.facility_service import FacilityService
from database.connection import db

router = APIRouter()


@router.get(
    "/facilities",
    response_model=List[FacilityResponse],
    summary="Get customer facilities",
    description="Get all facilities for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_facilities(customer: AuthenticatedCustomer = Depends(check_read_permission)):
    """Get all facilities for the authenticated customer."""
    return await FacilityService.get_customer_facilities(customer.customer_id)


@router.get(
    "/facilities/detailed",
    response_model=CustomerFacilities,
    summary="Get customer facilities with units",
    description="Get all facilities with their storage units for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_facilities_with_units(customer: AuthenticatedCustomer = Depends(check_read_permission)):
    """Get all facilities with their storage units for the authenticated customer."""
    return await FacilityService.get_customer_facilities_with_units(customer.customer_id)


@router.get(
    "/facilities/{facility_id}",
    response_model=FacilityResponse,
    summary="Get facility",
    description="Get a specific facility by ID",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
    }
)
async def get_facility(
    facility_id: str = Path(..., description="Facility ID"),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """Get a specific facility by ID."""
    facility = await FacilityService.get_facility(facility_id)
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
        
    # Check if facility belongs to customer
    if facility.customer_id != customer.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this facility"
        )
        
    return facility


@router.get(
    "/facilities/{facility_id}/detailed",
    response_model=FacilityWithUnits,
    summary="Get facility with storage units",
    description="Get a specific facility with its storage units",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
    }
)
async def get_facility_with_units(
    facility_id: str = Path(..., description="Facility ID"),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """Get a specific facility with its storage units."""
    facility = await FacilityService.get_facility_with_units(facility_id)
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
        
    # Check if facility belongs to customer
    if facility.customer_id != customer.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this facility"
        )
        
    return facility


@router.get(
    "/facilities/{facility_id}/units",
    response_model=List[StorageUnitResponse],
    summary="Get storage units",
    description="Get all storage units for a specific facility",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
    }
)
async def get_storage_units(
    facility_id: str = Path(..., description="Facility ID"),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """Get all storage units for a specific facility."""
    # Check if facility exists and belongs to customer
    facility = await FacilityService.get_facility(facility_id)
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
        
    # Check if facility belongs to customer
    if facility.customer_id != customer.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this facility"
        )
        
    return await FacilityService.get_storage_units(facility_id)


@router.get(
    "/units/{unit_id}",
    response_model=StorageUnitResponse,
    summary="Get storage unit",
    description="Get a specific storage unit by ID",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Storage unit not found"},
    }
)
async def get_storage_unit(
    unit_id: str = Path(..., description="Storage unit ID"),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """Get a specific storage unit by ID."""
    # Get the unit
    unit = await FacilityService.get_storage_unit(unit_id)
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage unit not found"
        )
        
    # Check if the unit belongs to a facility owned by the customer
    facility = await FacilityService.get_facility(unit.facility_id)
    
    if not facility or facility.customer_id != customer.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this storage unit"
        )
        
    return unit


# Write operations (require write permission)

@router.post(
    "/facilities",
    response_model=FacilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create facility",
    description="Create a new facility for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        409: {"model": ErrorResponse, "description": "Facility code already exists"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def create_facility(
    facility: FacilityCreate,
    customer: AuthenticatedCustomer = Depends(check_write_permission)
):
    """Create a new facility for the authenticated customer."""
    # Check if facility code already exists for this customer
    existing = await db.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM facilities 
            WHERE customer_id = $1 AND facility_code = $2
        )
        """,
        customer.customer_id, facility.facility_code
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Facility with code '{facility.facility_code}' already exists"
        )
        
    # Create the facility
    return await FacilityService.create_facility(
        customer_id=customer.customer_id,
        facility_code=facility.facility_code,
        name=facility.name,
        city=facility.city,
        country=facility.country,
        latitude=facility.latitude,
        longitude=facility.longitude
    )


@router.put(
    "/facilities/{facility_id}",
    response_model=FacilityResponse,
    summary="Update facility",
    description="Update a specific facility",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def update_facility(
    facility_id: str = Path(..., description="Facility ID"),
    facility: FacilityUpdate = Body(...),
    customer: AuthenticatedCustomer = Depends(check_write_permission)
):
    """Update a specific facility."""
    # Check if facility exists and belongs to customer
    existing = await FacilityService.get_facility(facility_id)
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
        
    if existing.customer_id != customer.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this facility"
        )
        
    # Update the facility
    updated = await FacilityService.update_facility(
        facility_id=facility_id,
        name=facility.name,
        city=facility.city,
        country=facility.country,
        latitude=facility.latitude,
        longitude=facility.longitude
    )
    
    return updated


@router.post(
    "/facilities/{facility_id}/units",
    response_model=StorageUnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create storage unit",
    description="Create a new storage unit for a specific facility",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
        409: {"model": ErrorResponse, "description": "Unit code already exists"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def create_storage_unit(
    facility_id: str = Path(..., description="Facility ID"),
    unit: StorageUnitCreate = Body(...),
    customer: AuthenticatedCustomer = Depends(check_write_permission)
):
    """Create a new storage unit for a specific facility."""
    # Check if facility exists and belongs to customer
    facility = await FacilityService.get_facility(facility_id)
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
        
    if facility.customer_id != customer.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this facility"
        )
        
    # Check if unit code already exists for this facility
    existing = await db.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM storage_units 
            WHERE facility_id = $1 AND unit_code = $2
        )
        """,
        facility_id, unit.unit_code
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Storage unit with code '{unit.unit_code}' already exists in this facility"
        )
        
    # Create the storage unit
    return await FacilityService.create_storage_unit(
        facility_id=facility_id,
        unit_code=unit.unit_code,
        name=unit.name,
        size_value=unit.size_value,
        size_unit=unit.size_unit,
        set_temperature=unit.set_temperature,
        temperature_unit=unit.temperature_unit,
        equipment_type=unit.equipment_type
    )


@router.put(
    "/units/{unit_id}",
    response_model=StorageUnitResponse,
    summary="Update storage unit",
    description="Update a specific storage unit",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Storage unit not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def update_storage_unit(
    unit_id: str = Path(..., description="Storage unit ID"),
    unit: StorageUnitUpdate = Body(...),
    customer: AuthenticatedCustomer = Depends(check_write_permission)
):
    """Update a specific storage unit."""
    # Get the unit
    existing = await FacilityService.get_storage_unit(unit_id)
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage unit not found"
        )
        
    # Check if the unit belongs to a facility owned by the customer
    facility = await FacilityService.get_facility(existing.facility_id)
    
    if not facility or facility.customer_id != customer.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this storage unit"
        )
        
    # Update the storage unit
    updated = await FacilityService.update_storage_unit(
        unit_id=unit_id,
        name=unit.name,
        size_value=unit.size_value,
        size_unit=unit.size_unit,
        set_temperature=unit.set_temperature,
        temperature_unit=unit.temperature_unit,
        equipment_type=unit.equipment_type
    )
    
    return updated


# Admin routes for facilities

@router.get(
    "/admin/facilities",
    response_model=List[FacilityResponse],
    summary="[Admin] Get all facilities",
    description="Get all facilities across all customers (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def admin_get_all_facilities(
    admin: AdminUser = Depends(get_admin_user),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID")
):
    """Get all facilities across all customers."""
    query = """
        SELECT 
            id, customer_id, facility_code, name, city, country,
            latitude, longitude, created_at
        FROM 
            public.facilities
    """
    
    params = []
    
    # Add customer filter if provided
    if customer_id:
        query += " WHERE customer_id = $1"
        params.append(customer_id)
        
    query += " ORDER BY customer_id, facility_code"
    
    facilities = await db.fetch(query, *params)
    
    return [
        FacilityResponse(
            id=f['id'],
            customer_id=f['customer_id'],
            facility_code=f['facility_code'],
            name=f['name'],
            city=f['city'],
            country=f['country'],
            latitude=f['latitude'],
            longitude=f['longitude'],
            created_at=f['created_at']
        )
        for f in facilities
    ]


@router.get(
    "/admin/facilities/{facility_id}",
    response_model=FacilityWithUnits,
    summary="[Admin] Get facility with storage units",
    description="Get a specific facility with its storage units (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
    }
)
async def admin_get_facility_with_units(
    facility_id: str = Path(..., description="Facility ID"),
    admin: AdminUser = Depends(get_admin_user)
):
    """Get a specific facility with its storage units."""
    facility = await FacilityService.get_facility_with_units(facility_id)
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
        
    return facility


@router.get(
    "/admin/units/{unit_id}",
    response_model=StorageUnitResponse,
    summary="[Admin] Get storage unit",
    description="Get a specific storage unit by ID (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Storage unit not found"},
    }
)
async def admin_get_storage_unit(
    unit_id: str = Path(..., description="Storage unit ID"),
    admin: AdminUser = Depends(get_admin_user)
):
    """Get a specific storage unit by ID."""
    unit = await FacilityService.get_storage_unit(unit_id)
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage unit not found"
        )
        
    return unit