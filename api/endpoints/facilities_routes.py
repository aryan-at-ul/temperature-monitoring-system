# api/endpoints/facilities_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from uuid import UUID
import logging
import traceback
from datetime import datetime

from api.auth.token_auth import get_current_customer, get_admin_user, check_read_permission, check_write_permission
from api.models.facility import (
    FacilityDetail, FacilityCreate, FacilityUpdate, 
    StorageUnitDetail, StorageUnitCreate, StorageUnitUpdate,
    FacilityWithUnits
)
from api.models.responses import PaginatedResponse, ErrorResponse
from api.services.facility_service import FacilityService
from database.connection import db



router = APIRouter()
logger = logging.getLogger(__name__)



@router.get(
    "/facilities",
    response_model=PaginatedResponse[FacilityDetail],
    summary="Get facilities",
    description="Get facilities for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_facilities(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer: dict = Depends(check_read_permission)
):
    """
    Get facilities for the authenticated customer.
    """
    try:
        facilities, total = await FacilityService.get_facilities(customer['id'], limit, offset)
        
        
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
        logger.error(f"Error in get_facilities: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving facilities: {str(e)}"
        )

@router.get(
    "/facilities/{facility_id}",
    response_model=FacilityDetail,
    summary="Get facility",
    description="Get a facility by ID",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
    }
)
async def get_facility(
    facility_id: UUID = Path(..., description="Facility ID"),
    customer: dict = Depends(check_read_permission)
):
    """
    Get a facility by ID.
    """
    try:
        facility = await FacilityService.get_facility(facility_id, customer['id'])
        
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        return facility
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_facility: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving facility: {str(e)}"
        )

@router.get(
    "/facilities/{facility_id}/detailed",
    response_model=FacilityWithUnits,
    summary="Get facility with units",
    description="Get a facility with all its storage units and temperature statistics",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
    }
)
async def get_facility_with_units(
    facility_id: UUID = Path(..., description="Facility ID"),
    customer: dict = Depends(check_read_permission)
):
    """
    Get a facility with all its storage units and temperature statistics.
    """
    try:
        facility = await FacilityService.get_facility_with_units(facility_id, customer['id'])
        
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        return facility
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_facility_with_units: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving facility with units: {str(e)}"
        )

@router.get(
    "/facilities/{facility_id}/units",
    response_model=PaginatedResponse[StorageUnitDetail],
    summary="Get storage units",
    description="Get storage units for a facility",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
    }
)
async def get_facility_units(
    facility_id: UUID = Path(..., description="Facility ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer: dict = Depends(check_read_permission)
):
    """
    Get storage units for a facility.
    """
    try:
        units, total = await FacilityService.get_storage_units(facility_id, customer['id'], limit, offset)
        
        if units is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
   
        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return PaginatedResponse(
            items=units,
            total=total,
            page=page,
            page_size=limit,
            pages=pages
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_facility_units: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving storage units: {str(e)}"
        )

@router.get(
    "/units/{unit_id}",
    response_model=StorageUnitDetail,
    summary="Get storage unit",
    description="Get a storage unit by ID",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Storage unit not found"},
    }
)
async def get_storage_unit(
    unit_id: UUID = Path(..., description="Storage unit ID"),
    customer: dict = Depends(check_read_permission)
):
    """
    Get a storage unit by ID.
    """
    try:
        
        query = """
            SELECT su.*, 
                (
                    SELECT tr.temperature 
                    FROM temperature_readings tr 
                    WHERE tr.storage_unit_id = su.id 
                    ORDER BY tr.recorded_at DESC 
                    LIMIT 1
                ) as current_temperature,
                (
                    SELECT tr.temperature_unit 
                    FROM temperature_readings tr 
                    WHERE tr.storage_unit_id = su.id 
                    ORDER BY tr.recorded_at DESC 
                    LIMIT 1
                ) as current_temperature_unit,
                (
                    SELECT tr.equipment_status 
                    FROM temperature_readings tr 
                    WHERE tr.storage_unit_id = su.id 
                    ORDER BY tr.recorded_at DESC 
                    LIMIT 1
                ) as temperature_status,
                (
                    SELECT tr.recorded_at 
                    FROM temperature_readings tr 
                    WHERE tr.storage_unit_id = su.id 
                    ORDER BY tr.recorded_at DESC 
                    LIMIT 1
                ) as last_reading_time
            FROM storage_units su
            JOIN facilities f ON su.facility_id = f.id
            WHERE su.id = $1 AND f.customer_id = $2
        """
        
        unit = await db.fetchrow(query, str(unit_id), customer['id'])
        
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage unit not found"
            )
        
        return unit
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_storage_unit: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving storage unit: {str(e)}"
        )

@router.post(
    "/facilities",
    response_model=FacilityDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create facility",
    description="Create a new facility",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def create_facility(
    facility: FacilityCreate,
    customer: dict = Depends(check_write_permission)
):
    """
    Create a new facility.
    """
    try:
        
        facility_data = FacilityCreate(
            **facility.dict(),
            customer_id=customer['id']
        )
        
        result = await FacilityService.create_facility(facility_data)
        return result
    except Exception as e:
        logger.error(f"Error in create_facility: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating facility: {str(e)}"
        )

@router.put(
    "/facilities/{facility_id}",
    response_model=FacilityDetail,
    summary="Update facility",
    description="Update a facility",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def update_facility(
    facility_id: UUID = Path(..., description="Facility ID"),
    facility: FacilityUpdate = None,
    customer: dict = Depends(check_write_permission)
):
    """
    Update a facility.
    """
    try:
        result = await FacilityService.update_facility(facility_id, customer['id'], facility)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_facility: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating facility: {str(e)}"
        )

@router.post(
    "/facilities/{facility_id}/units",
    response_model=StorageUnitDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create storage unit",
    description="Create a new storage unit for a facility",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Facility not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def create_storage_unit(
    facility_id: UUID = Path(..., description="Facility ID"),
    unit: StorageUnitCreate = None,
    customer: dict = Depends(check_write_permission)
):
    """
    Create a new storage unit for a facility.
    """
    try:
    
        facility_query = """
            SELECT id FROM facilities WHERE id = $1 AND customer_id = $2
        """
        facility = await db.fetchrow(facility_query, str(facility_id), customer['id'])
        
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
      
        unit_data = StorageUnitCreate(
            **unit.dict(),
            facility_id=facility_id
        )
        
        result = await FacilityService.create_storage_unit(unit_data)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in create_storage_unit: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating storage unit: {str(e)}"
        )

@router.put(
    "/units/{unit_id}",
    response_model=StorageUnitDetail,
    summary="Update storage unit",
    description="Update a storage unit",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Storage unit not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def update_storage_unit(
    unit_id: UUID = Path(..., description="Storage unit ID"),
    unit: StorageUnitUpdate = None,
    customer: dict = Depends(check_write_permission)
):
    """
    Update a storage unit.
    """
    try:
        result = await FacilityService.update_storage_unit(unit_id, customer['id'], unit)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage unit not found"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_storage_unit: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating storage unit: {str(e)}"
        )