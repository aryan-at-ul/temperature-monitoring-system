# api/endpoints/analytics_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import logging
import traceback

from api.auth.token_auth import get_current_customer, get_admin_user, check_read_permission
from api.models.temperature import TemperatureStats, AggregationResult
from api.models.responses import ErrorResponse, PaginatedResponse
from api.services.temperature_service import TemperatureService
from database.connection import db
from database.connection import DatabaseConnection  

db_manager = DatabaseConnection() 

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_db():
    """Get database connection"""
    return db_manager



@router.get(
    "/analytics/temperature/summary",
    response_model=TemperatureStats,
    summary="Get temperature summary",
    description="Get temperature summary statistics for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_temperature_summary(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    facility_id: Optional[UUID] = Query(None, description="Filter by facility ID"),
    unit_id: Optional[UUID] = Query(None, description="Filter by storage unit ID"),
    customer: dict = Depends(check_read_permission)
):
    """
    Get temperature summary statistics for the authenticated customer.
    
    Optional parameters can be used to filter the data.
    """
    try:
        stats = await TemperatureService.get_statistics(
            customer['id'], start_date, end_date,
            facility_id=str(facility_id) if facility_id else None,
            storage_unit_id=str(unit_id) if unit_id else None
        )
        return stats
    except Exception as e:
        logger.error(f"Error in get_temperature_summary: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving temperature summary: {str(e)}"
        )

@router.get(
    "/analytics/temperature/trends",
    response_model=List[AggregationResult],
    summary="Get temperature trends",
    description="Get temperature trends over time",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def get_temperature_trends(
    interval: str = Query("day", description="Time interval (hour, day, week, month)"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    facility_id: Optional[UUID] = Query(None, description="Filter by facility ID"),
    unit_id: Optional[UUID] = Query(None, description="Filter by storage unit ID"),
    customer: dict = Depends(check_read_permission)
):
    """
    Get temperature trends over time.
    
    Time interval can be hour, day, week, or month. Optional parameters can be used to filter the data.
    """
    try:
        # Validate interval
        valid_intervals = ["hour", "day", "week", "month"]
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid interval: {interval}. Valid values are {valid_intervals}"
            )
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now()
        
        if not start_date:
            if interval == "hour":
                start_date = end_date - timedelta(days=1)
            elif interval == "day":
                start_date = end_date - timedelta(days=7)
            elif interval == "week":
                start_date = end_date - timedelta(days=30)
            else:  # month
                start_date = end_date - timedelta(days=365)
        
        
        aggregation_params = {
            "group_by": [interval],
            "aggregations": ["avg", "min", "max", "count"],
            "start_date": start_date,
            "end_date": end_date,
            "facility_id": facility_id,
            "storage_unit_id": unit_id
        }
        
        from api.models.temperature import TemperatureAggregation
        aggregation = TemperatureAggregation(**aggregation_params)
        
        results = await TemperatureService.get_aggregation(customer['id'], aggregation)
        return results
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in get_temperature_trends: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving temperature trends: {str(e)}"
        )

@router.get(
    "/analytics/alarms/history",
    response_model=PaginatedResponse[dict],
    summary="Get alarm history",
    description="Get temperature alarm history",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_alarm_history(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    facility_id: Optional[UUID] = Query(None, description="Filter by facility ID"),
    unit_id: Optional[UUID] = Query(None, description="Filter by storage unit ID"),
    customer: dict = Depends(check_read_permission)
):
    """
    Get temperature alarm history.
    
    Alarms are triggered when temperature readings have an equipment_status of 'warning' or 'error'.
    Optional parameters can be used to filter the data.
    """
    try:
    
        sql_query = """
            SELECT tr.*, f.name as facility_name, su.name as unit_name
            FROM temperature_readings tr
            JOIN facilities f ON tr.facility_id = f.id
            JOIN storage_units su ON tr.storage_unit_id = su.id
            WHERE tr.customer_id = $1 
            AND tr.equipment_status IN ('warning', 'error')
        """
        
        params = [customer['id']]
        param_count = 2
        
        if facility_id:
            sql_query += f" AND tr.facility_id = ${param_count}"
            params.append(str(facility_id))
            param_count += 1
        
        if unit_id:
            sql_query += f" AND tr.storage_unit_id = ${param_count}"
            params.append(str(unit_id))
            param_count += 1

       
        if start_date:
            sql_query += f" AND tr.recorded_at >= ${param_count}"
            params.append(start_date)
            param_count += 1
            
        if end_date:
            sql_query += f" AND tr.recorded_at <= ${param_count}"
            params.append(end_date)
            param_count += 1
        
        
        sql_query += " ORDER BY tr.recorded_at DESC"
        
        
        sql_query += f" LIMIT ${param_count} OFFSET ${param_count + 1}"
        params.extend([limit, offset])
        
      
        alarms = await db.fetch(sql_query, *params)
        
       
        count_query = """
            SELECT COUNT(*) as count
            FROM temperature_readings tr
            WHERE tr.customer_id = $1 
            AND tr.equipment_status IN ('warning', 'error')
        """
        
        count_params = [customer['id']]
        param_count = 2
        
        if facility_id:
            count_query += f" AND tr.facility_id = ${param_count}"
            count_params.append(str(facility_id))
            param_count += 1
        
        if unit_id:
            count_query += f" AND tr.storage_unit_id = ${param_count}"
            count_params.append(str(unit_id))
            param_count += 1
            
        if start_date:
            count_query += f" AND tr.recorded_at >= ${param_count}"
            count_params.append(start_date)
            param_count += 1
            
        if end_date:
            count_query += f" AND tr.recorded_at <= ${param_count}"
            count_params.append(end_date)
            param_count += 1
        
        count_result = await db.fetchrow(count_query, *count_params)
        total = count_result['count'] if count_result else 0
        
        
        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return PaginatedResponse(
            items=alarms,
            total=total,
            page=page,
            page_size=limit,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Error in get_alarm_history: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving alarm history: {str(e)}"
        )


@router.get(
    "/analytics/performance",
    response_model=Dict[str, Any],
    summary="Get performance metrics",
    description="Get performance metrics for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_performance_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    customer: dict = Depends(check_read_permission),
    db = Depends(get_db)  # Add this line
):
    """
    Get performance metrics for the authenticated customer.
    """
    try:
        
        if not end_date:
            end_date = datetime.now()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
      
        uptime_query = """
            WITH time_periods AS (
                SELECT 
                    generate_series(
                        $1::timestamp, 
                        $2::timestamp, 
                        interval '1 hour'
                    ) as hour
            ),
            readings_per_hour AS (
                SELECT 
                    date_trunc('hour', recorded_at) as hour,
                    COUNT(*) as reading_count
                FROM temperature_readings
                WHERE customer_id = $3
                AND recorded_at BETWEEN $1 AND $2
                GROUP BY date_trunc('hour', recorded_at)
            )
            SELECT 
                COUNT(rph.reading_count) as hours_with_readings,
                COUNT(tp.hour) as total_hours,
                ROUND((COUNT(rph.reading_count)::numeric / COUNT(tp.hour)::numeric * 100)::numeric, 2) as uptime_percentage
            FROM time_periods tp
            LEFT JOIN readings_per_hour rph ON tp.hour = rph.hour
        """
        
        uptime_result = await db.fetchrow(uptime_query, start_date, end_date, customer['id'])
        
        
        quality_query = """
            SELECT 
                COUNT(*) as total_readings,
                COUNT(CASE WHEN quality_score = 1 THEN 1 END) as good_readings,
                ROUND((COUNT(CASE WHEN quality_score = 1 THEN 1 END)::numeric / COUNT(*)::numeric * 100)::numeric, 2) as quality_percentage
            FROM temperature_readings
            WHERE customer_id = $1
            AND recorded_at BETWEEN $2 AND $3
        """
        
        quality_result = await db.fetchrow(quality_query, customer['id'], start_date, end_date)
        
        
        deviation_query = """
            WITH deviations AS (
                SELECT 
                    tr.temperature,
                    su.set_temperature,
                    ABS(tr.temperature - su.set_temperature) as deviation
                FROM temperature_readings tr
                JOIN storage_units su ON tr.storage_unit_id = su.id
                WHERE tr.customer_id = $1
                AND tr.recorded_at BETWEEN $2 AND $3
                AND tr.temperature_unit = su.temperature_unit
            )
            SELECT 
                ROUND(AVG(deviation)::numeric, 2) as avg_deviation,
                ROUND(MAX(deviation)::numeric, 2) as max_deviation,
                ROUND(MIN(deviation)::numeric, 2) as min_deviation
            FROM deviations
        """
        
        deviation_result = await db.fetchrow(deviation_query, customer['id'], start_date, end_date)
        
       
        status_query = """
            SELECT 
                equipment_status,
                COUNT(*) as count,
                ROUND((COUNT(*)::numeric / (SELECT COUNT(*) FROM temperature_readings WHERE customer_id = $1 AND recorded_at BETWEEN $2 AND $3)::numeric * 100)::numeric, 2) as percentage
            FROM temperature_readings
            WHERE customer_id = $1
            AND recorded_at BETWEEN $2 AND $3
            GROUP BY equipment_status
            ORDER BY count DESC
        """
        
        status_result = await db.fetch(status_query, customer['id'], start_date, end_date)
        
      
        performance_metrics = {
            "uptime": {
                "hours_with_readings": uptime_result['hours_with_readings'] if uptime_result else 0,
                "total_hours": uptime_result['total_hours'] if uptime_result else 0,
                "uptime_percentage": float(uptime_result['uptime_percentage']) if uptime_result and uptime_result['uptime_percentage'] else 0.0
            },
            "data_quality": {
                "total_readings": quality_result['total_readings'] if quality_result else 0,
                "good_readings": quality_result['good_readings'] if quality_result else 0,
                "quality_percentage": float(quality_result['quality_percentage']) if quality_result and quality_result['quality_percentage'] else 0.0
            },
            "temperature_deviation": {
                "avg_deviation": float(deviation_result['avg_deviation']) if deviation_result and deviation_result['avg_deviation'] else 0.0,
                "max_deviation": float(deviation_result['max_deviation']) if deviation_result and deviation_result['max_deviation'] else 0.0,
                "min_deviation": float(deviation_result['min_deviation']) if deviation_result and deviation_result['min_deviation'] else 0.0
            },
            "status_distribution": [dict(row) for row in status_result] if status_result else [],
            "time_range": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
        return performance_metrics
    except Exception as e:
        logger.error(f"Error in get_performance_metrics: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving performance metrics: {str(e)}"
        )





@router.get(
    "/admin/analytics/temperature/summary",
    response_model=Dict[str, TemperatureStats],
    summary="[Admin] Get system-wide temperature summary",
    description="Get temperature summary statistics across all customers (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def admin_get_temperature_summary(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    admin: dict = Depends(get_admin_user)
):
    """
    Get temperature summary statistics across all customers.
    
    Only accessible to admin users. Optional parameters can be used to filter the time range.
    """
    try:
        
        customers_query = "SELECT id, customer_code FROM customers"
        customers = await db.fetch(customers_query)
        
        
        summary = {}
        for customer in customers:
            stats = await TemperatureService.get_statistics(
                customer['id'], start_date, end_date
            )
            summary[customer['customer_code']] = stats
        
        
        system_query = """
            SELECT 
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature,
                AVG(temperature) as avg_temperature,
                COUNT(*) as reading_count,
                COUNT(CASE WHEN equipment_status = 'normal' THEN 1 END) as normal_count,
                COUNT(CASE WHEN equipment_status = 'warning' THEN 1 END) as warning_count,
                COUNT(CASE WHEN equipment_status = 'error' THEN 1 END) as error_count,
                MIN(recorded_at) as time_range_start,
                MAX(recorded_at) as time_range_end,
                COUNT(DISTINCT storage_unit_id) as unit_count,
                MODE() WITHIN GROUP (ORDER BY temperature_unit) as temperature_unit
            FROM temperature_readings
        """
        
        params = []
        
        if start_date:
            system_query += " WHERE recorded_at >= $1"
            params.append(start_date)
            
            if end_date:
                system_query += " AND recorded_at <= $2"
                params.append(end_date)
        elif end_date:
            system_query += " WHERE recorded_at <= $1"
            params.append(end_date)
        
        system_stats = await db.fetchrow(system_query, *params)
        summary["system"] = system_stats
        
        return summary
    except Exception as e:
        logger.error(f"Error in admin_get_temperature_summary: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving temperature summary: {str(e)}"
        )