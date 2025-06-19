# api/endpoints/temperature_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import logging
import traceback

from api.auth.token_auth import get_current_customer, get_admin_user, check_read_permission, check_write_permission
from api.models.temperature import (
    TemperatureReadingDetail, TemperatureReadingCreate, TemperatureQuery, 
    TemperatureStats, TemperatureAggregation, AggregationResult
)
from api.models.responses import PaginatedResponse, ErrorResponse
from api.services.temperature_service import TemperatureService
from database.connection import DatabaseConnection  


db_manager = DatabaseConnection() 
router = APIRouter()
logger = logging.getLogger(__name__)


async def get_db():
    """Get database connection"""
    return db_manager



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
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    min_temperature: Optional[float] = Query(None, description="Minimum temperature"),
    max_temperature: Optional[float] = Query(None, description="Maximum temperature"),
    equipment_status: Optional[str] = Query(None, description="Equipment status (normal, warning, error)"),
    quality_score: Optional[int] = Query(None, ge=0, le=1, description="Quality score (0=bad, 1=good)"),
    sensor_id: Optional[str] = Query(None, description="Sensor ID"),
    customer: dict = Depends(check_read_permission)
):
    """
    Get temperature readings for the authenticated customer.
    
    Query parameters can be used to filter and paginate the results.
    """
    try:
        
        query = TemperatureQuery(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            min_temperature=min_temperature,
            max_temperature=max_temperature,
            equipment_status=equipment_status,
            quality_score=quality_score,
            sensor_id=sensor_id
        )
        
        readings, total = await TemperatureService.get_readings(customer, query)
        
     
        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return PaginatedResponse(
            items=readings,
            total=total,
            page=page,
            page_size=limit,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Error in get_temperature_readings: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving temperature readings: {str(e)}"
        )



@router.get(
    "/temperature/latest",
    response_model=List[TemperatureReadingDetail],
    summary="Get latest temperature readings",
    description="Get the latest temperature reading for each storage unit",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_latest_temperature_readings(
    limit: int = Query(20, ge=1, le=100),
    customer: dict = Depends(check_read_permission),
    db = Depends(get_db)  
):
    """
    Get the latest temperature reading for each storage unit.
    """
    try:
        query = """
            WITH latest_readings AS (
                SELECT DISTINCT ON (storage_unit_id) *
                FROM temperature_readings
                WHERE customer_id = $1
                ORDER BY storage_unit_id, recorded_at DESC
            )
            SELECT lr.*, f.name as facility_name, su.name as unit_name
            FROM latest_readings lr
            JOIN facilities f ON lr.facility_id = f.id
            JOIN storage_units su ON lr.storage_unit_id = su.id
            ORDER BY lr.recorded_at DESC
            LIMIT $2
        """
        
        readings = await db.fetch(query, customer['id'], limit)
        return readings
    except Exception as e:
        logger.error(f"Error in get_latest_temperature_readings: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving latest temperature readings: {str(e)}"
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
    facility_id: UUID = Path(..., description="Facility ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    min_temperature: Optional[float] = Query(None, description="Minimum temperature"),
    max_temperature: Optional[float] = Query(None, description="Maximum temperature"),
    equipment_status: Optional[str] = Query(None, description="Equipment status (normal, warning, error)"),
    quality_score: Optional[int] = Query(None, ge=0, le=1, description="Quality score (0=bad, 1=good)"),
    sensor_id: Optional[str] = Query(None, description="Sensor ID"),
    customer: dict = Depends(check_read_permission)
):
    """
    Get temperature readings for a specific facility.
    
    Query parameters can be used to filter and paginate the results.
    """
    try:
   
        query = TemperatureQuery(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            min_temperature=min_temperature,
            max_temperature=max_temperature,
            equipment_status=equipment_status,
            quality_score=quality_score,
            sensor_id=sensor_id
        )
        
        readings, total = await TemperatureService.get_readings(
            customer, query, facility_id=str(facility_id)
        )
        
        if not readings and total == 0:
           
            facility_exists = await db.fetchval(
                "SELECT EXISTS(SELECT 1 FROM facilities WHERE id = $1 AND customer_id = $2)",
                str(facility_id), customer['id']
            )
            
            if not facility_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Facility not found"
                )
        
     
        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return PaginatedResponse(
            items=readings,
            total=total,
            page=page,
            page_size=limit,
            pages=pages
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_facility_temperature_readings: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving facility temperature readings: {str(e)}"
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
    unit_id: UUID = Path(..., description="Storage unit ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    min_temperature: Optional[float] = Query(None, description="Minimum temperature"),
    max_temperature: Optional[float] = Query(None, description="Maximum temperature"),
    equipment_status: Optional[str] = Query(None, description="Equipment status (normal, warning, error)"),
    quality_score: Optional[int] = Query(None, ge=0, le=1, description="Quality score (0=bad, 1=good)"),
    sensor_id: Optional[str] = Query(None, description="Sensor ID"),
    customer: dict = Depends(check_read_permission),
    db = Depends(get_db) 
):
    """
    Get temperature readings for a specific storage unit.
    """
    try:
        
        unit_query = """
            SELECT su.id
            FROM storage_units su
            JOIN facilities f ON su.facility_id = f.id
            WHERE su.id = $1 AND f.customer_id = $2
        """
        unit = await db.fetchrow(unit_query, str(unit_id), customer['id'])
        
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage unit not found"
            )
        

        query = TemperatureQuery(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            min_temperature=min_temperature,
            max_temperature=max_temperature,
            equipment_status=equipment_status,
            quality_score=quality_score,
            sensor_id=sensor_id
        )
        
        readings, total = await TemperatureService.get_readings(
            customer, query, storage_unit_id=str(unit_id)
        )
        

        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return PaginatedResponse(
            items=readings,
            total=total,
            page=page,
            page_size=limit,
            pages=pages
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_unit_temperature_readings: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving unit temperature readings: {str(e)}"
        )

@router.post(
    "/temperature",
    response_model=TemperatureReadingDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a temperature reading",
    description="Create a new temperature reading",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Storage unit not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def create_temperature_reading(
    reading: TemperatureReadingCreate,
    customer: dict = Depends(check_write_permission)
):
    """
    Create a new temperature reading.
    
    The storage unit must belong to the authenticated customer.
    """
    try:
        result = await TemperatureService.create_reading(customer['id'], reading)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in create_temperature_reading: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating temperature reading: {str(e)}"
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
    customer: dict = Depends(check_read_permission)
):
    """
    Get temperature statistics for the authenticated customer.
    
    Optional start_date and end_date parameters can be used to filter the time range.
    """
    try:
        stats = await TemperatureService.get_statistics(
            customer['id'], start_date, end_date
        )
        return stats
    except Exception as e:
        logger.error(f"Error in get_temperature_stats: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving temperature statistics: {str(e)}"
        )

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
    customer: dict = Depends(check_read_permission)
):
    """
    Aggregate temperature data with various grouping options.
    
    You can group by hour, day, week, month, facility, unit, or sensor.
    Available aggregation functions are avg, min, max, and count.
    """
    try:
        results = await TemperatureService.get_aggregation(
            customer['id'], aggregation
        )
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in aggregate_temperature_data: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error aggregating temperature data: {str(e)}"
        )



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
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    min_temperature: Optional[float] = Query(None, description="Minimum temperature"),
    max_temperature: Optional[float] = Query(None, description="Maximum temperature"),
    equipment_status: Optional[str] = Query(None, description="Equipment status (normal, warning, error)"),
    quality_score: Optional[int] = Query(None, ge=0, le=1, description="Quality score (0=bad, 1=good)"),
    sensor_id: Optional[str] = Query(None, description="Sensor ID"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    admin: dict = Depends(get_admin_user)
):
    """
    Get temperature readings across all customers.
    
    Only accessible to admin users. Query parameters can be used to filter and paginate the results.
    """
    try:
        
        query = TemperatureQuery(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            min_temperature=min_temperature,
            max_temperature=max_temperature,
            equipment_status=equipment_status,
            quality_score=quality_score,
            sensor_id=sensor_id
        )
        
        readings, total = await TemperatureService.get_admin_readings(
            query, customer_id=str(customer_id) if customer_id else None
        )
        
       
        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return PaginatedResponse(
            items=readings,
            total=total,
            page=page,
            page_size=limit,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Error in admin_get_temperature_readings: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving temperature readings: {str(e)}"
        )