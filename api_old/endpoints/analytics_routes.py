from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from datetime import datetime, timedelta

from api.auth.token_auth import get_current_customer, get_admin_user, check_read_permission
from api.models.customer import AuthenticatedCustomer, AdminUser
from api.models.temperature import (
    TemperatureStats, FacilityStats, StorageUnitStats, CustomerStats,
    TemperatureAlert, TemperatureAlertResponse
)
from api.models.responses import ErrorResponse, MetricsResponse, PaginatedResponse
from api.services.temperature_service import TemperatureService
from database.connection import db

router = APIRouter()


@router.get(
    "/analytics/dashboard",
    response_model=CustomerStats,
    summary="Get customer dashboard stats",
    description="Get dashboard statistics for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_customer_dashboard(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """
    Get dashboard statistics for the authenticated customer.
    
    Includes overall stats and breakdown by facility and storage unit.
    """
    # Default date range is last 7 days if not specified
    if not end_date:
        end_date = datetime.now()
        
    if not start_date:
        start_date = end_date - timedelta(days=7)
        
    # Get customer info
    customer_query = """
        SELECT customer_code, name FROM customers WHERE id = $1
    """
    customer_info = await db.fetchrow(customer_query, customer.customer_id)
    
    # Get overall stats
    overall_stats = await TemperatureService.get_statistics(
        customer.customer_id, start_date, end_date
    )
    
    # Get facilities
    facilities_query = """
        SELECT id, facility_code, name, city, country
        FROM facilities
        WHERE customer_id = $1
    """
    facilities = await db.fetch(facilities_query, customer.customer_id)
    
    # Build facility stats
    facility_stats = []
    for facility in facilities:
        # Get facility stats
        facility_id = facility['id']
        f_stats = await TemperatureService.get_statistics(
            customer.customer_id, start_date, end_date, facility_id=facility_id
        )
        
        # Get storage units for this facility
        units_query = """
            SELECT id, unit_code, name
            FROM storage_units
            WHERE facility_id = $1
        """
        units = await db.fetch(units_query, facility_id)
        
        # Build unit stats
        unit_stats = []
        for unit in units:
            # Get unit stats
            unit_id = unit['id']
            u_stats = await TemperatureService.get_statistics(
                customer.customer_id, start_date, end_date, storage_unit_id=unit_id
            )
            
            unit_stats.append(
                StorageUnitStats(
                    unit_id=unit_id,
                    unit_code=unit['unit_code'],
                    unit_name=unit['name'],
                    statistics=u_stats
                )
            )
            
        facility_stats.append(
            FacilityStats(
                facility_id=facility_id,
                facility_code=facility['facility_code'],
                facility_name=facility['name'],
                city=facility['city'],
                country=facility['country'],
                statistics=f_stats,
                units=unit_stats
            )
        )
        
    # Return combined stats
    return CustomerStats(
        customer_id=customer.customer_id,
        customer_code=customer_info['customer_code'],
        customer_name=customer_info['name'],
        statistics=overall_stats,
        facilities=facility_stats
    )


@router.get(
    "/analytics/alerts",
    response_model=PaginatedResponse[TemperatureAlertResponse],
    summary="Get temperature alerts",
    description="Get temperature alerts for the authenticated customer",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def get_temperature_alerts(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgement status"),
    severity: Optional[str] = Query(None, description="Filter by severity (warning, critical)"),
    facility_id: Optional[str] = Query(None, description="Filter by facility ID"),
    unit_id: Optional[str] = Query(None, description="Filter by storage unit ID"),
    limit: int = Query(100, description="Maximum number of alerts to return"),
    offset: int = Query(0, description="Number of alerts to skip"),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """
    Get temperature alerts for the authenticated customer.
    
    Alerts are generated when temperature readings deviate significantly from the
    set temperature of a storage unit.
    """
    # Build base query
    base_query = """
        SELECT 
            a.id, a.customer_id, a.facility_id, a.storage_unit_id, 
            a.temperature, a.temperature_unit, a.set_temperature, 
            a.deviation, a.threshold, a.severity, a.recorded_at, 
            a.created_at, a.acknowledged, a.acknowledged_at, a.acknowledged_by, a.notes,
            c.customer_code, c.name as customer_name,
            f.facility_code, f.name as facility_name,
            su.unit_code, su.name as unit_name
        FROM 
            temperature_alerts a
            JOIN customers c ON a.customer_id = c.id
            JOIN facilities f ON a.facility_id = f.id
            JOIN storage_units su ON a.storage_unit_id = su.id
        WHERE 
            a.customer_id = $1
    """
    
    count_query = """
        SELECT COUNT(*) 
        FROM 
            temperature_alerts a
        WHERE 
            a.customer_id = $1
    """
    
    # Build where clause and parameters
    where_clauses = []
    params = [customer.customer_id]
    param_index = 2
    
    if start_date:
        where_clauses.append(f"a.recorded_at >= ${param_index}")
        params.append(start_date)
        param_index += 1
        
    if end_date:
        where_clauses.append(f"a.recorded_at <= ${param_index}")
        params.append(end_date)
        param_index += 1
        
    if acknowledged is not None:
        where_clauses.append(f"a.acknowledged = ${param_index}")
        params.append(acknowledged)
        param_index += 1
        
    if severity:
        where_clauses.append(f"a.severity = ${param_index}")
        params.append(severity)
        param_index += 1
        
    if facility_id:
        where_clauses.append(f"a.facility_id = ${param_index}")
        params.append(facility_id)
        param_index += 1
        
    if unit_id:
        where_clauses.append(f"a.storage_unit_id = ${param_index}")
        params.append(unit_id)
        param_index += 1
        
    # Add where clauses to queries
    if where_clauses:
        additional_clauses = " AND " + " AND ".join(where_clauses)
        base_query += additional_clauses
        count_query += additional_clauses
        
    # Add ordering and pagination
    base_query += " ORDER BY a.recorded_at DESC LIMIT $" + str(param_index) + " OFFSET $" + str(param_index + 1)
    params.append(limit)
    params.append(offset)
    
    # Execute queries
    alerts = await db.fetch(base_query, *params)
    count = await db.fetchval(count_query, *params[:-2])  # Exclude limit and offset
    
    # Convert to model instances
    alert_models = [
        TemperatureAlertResponse(
            id=a['id'],
            customer_id=a['customer_id'],
            facility_id=a['facility_id'],
            storage_unit_id=a['storage_unit_id'],
            temperature=a['temperature'],
            temperature_unit=a['temperature_unit'],
            set_temperature=a['set_temperature'],
            deviation=a['deviation'],
            threshold=a['threshold'],
            severity=a['severity'],
            recorded_at=a['recorded_at'],
            created_at=a['created_at'],
            acknowledged=a['acknowledged'],
            acknowledged_at=a['acknowledged_at'],
            acknowledged_by=a['acknowledged_by'],
            notes=a['notes'],
            customer_code=a['customer_code'],
            customer_name=a['customer_name'],
            facility_code=a['facility_code'],
            facility_name=a['facility_name'],
            unit_code=a['unit_code'],
            unit_name=a['unit_name']
        )
        for a in alerts
    ]
    
    # Calculate pagination info
    page = (offset // limit) + 1 if limit > 0 else 1
    pages = (count + limit - 1) // limit if limit > 0 else 1
    
    return PaginatedResponse(
        items=alert_models,
        total=count,
        page=page,
        page_size=limit,
        pages=pages
    )


@router.post(
    "/analytics/alerts/{alert_id}/acknowledge",
    response_model=TemperatureAlertResponse,
    summary="Acknowledge alert",
    description="Acknowledge a temperature alert",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Alert not found"},
    }
)
async def acknowledge_alert(
    alert_id: str = Path(..., description="Alert ID"),
    notes: Optional[str] = Query(None, description="Optional notes about the acknowledgement"),
    customer: AuthenticatedCustomer = Depends(check_read_permission)
):
    """
    Acknowledge a temperature alert.
    
    This marks the alert as having been seen and handled by an operator.
    """
    # Check if alert exists and belongs to customer
    alert_query = """
        SELECT * FROM temperature_alerts WHERE id = $1 AND customer_id = $2
    """
    alert = await db.fetchrow(alert_query, alert_id, customer.customer_id)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
        
    # Update the alert
    update_query = """
        UPDATE temperature_alerts
        SET acknowledged = true, acknowledged_at = $1, acknowledged_by = $2, notes = $3
        WHERE id = $4
        RETURNING *
    """
    
    acknowledged_at = datetime.now()
    acknowledged_by = f"{customer.customer_code} ({customer.customer_name})"
    
    updated = await db.fetchrow(
        update_query, acknowledged_at, acknowledged_by, notes, alert_id
    )
    
    # Get additional data for response
    additional_query = """
        SELECT 
            c.customer_code, c.name as customer_name,
            f.facility_code, f.name as facility_name,
            su.unit_code, su.name as unit_name
        FROM 
            customers c
            JOIN facilities f ON f.customer_id = c.id
            JOIN storage_units su ON su.facility_id = f.id
        WHERE 
            c.id = $1 AND f.id = $2 AND su.id = $3
    """
    
    additional = await db.fetchrow(
        additional_query, 
        updated['customer_id'], 
        updated['facility_id'], 
        updated['storage_unit_id']
    )
    
    # Return combined alert response
    return TemperatureAlertResponse(
        id=updated['id'],
        customer_id=updated['customer_id'],
        facility_id=updated['facility_id'],
        storage_unit_id=updated['storage_unit_id'],
        temperature=updated['temperature'],
        temperature_unit=updated['temperature_unit'],
        set_temperature=updated['set_temperature'],
        deviation=updated['deviation'],
        threshold=updated['threshold'],
        severity=updated['severity'],
        recorded_at=updated['recorded_at'],
        created_at=updated['created_at'],
        acknowledged=updated['acknowledged'],
        acknowledged_at=updated['acknowledged_at'],
        acknowledged_by=updated['acknowledged_by'],
        notes=updated['notes'],
        customer_code=additional['customer_code'],
        customer_name=additional['customer_name'],
        facility_code=additional['facility_code'],
        facility_name=additional['facility_name'],
        unit_code=additional['unit_code'],
        unit_name=additional['unit_name']
    )


@router.get(
    "/admin/metrics",
    response_model=MetricsResponse,
    summary="[Admin] Get system metrics",
    description="Get system-wide metrics (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def admin_get_metrics(
    admin: AdminUser = Depends(get_admin_user)
):
    """
    Get system-wide metrics.
    
    Provides an overview of the system's usage and data volumes.
    """
    # Get current timestamp for date calculations
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = datetime(now.year, now.month, 1, 0, 0, 0)
    
    # Execute metrics queries
    metrics = {}
    
    # Total customers
    metrics['total_customers'] = await db.fetchval(
        "SELECT COUNT(*) FROM customers WHERE is_active = true"
    )
    
    # Total facilities
    metrics['total_facilities'] = await db.fetchval(
        "SELECT COUNT(*) FROM facilities"
    )
    
    # Total storage units
    metrics['total_storage_units'] = await db.fetchval(
        "SELECT COUNT(*) FROM storage_units"
    )
    
    # Total readings
    metrics['total_readings'] = await db.fetchval(
        "SELECT COUNT(*) FROM temperature_readings"
    )
    
    # Readings today
    metrics['readings_today'] = await db.fetchval(
        "SELECT COUNT(*) FROM temperature_readings WHERE recorded_at >= $1",
        today_start
    )
    
    # Readings this week
    metrics['readings_this_week'] = await db.fetchval(
        "SELECT COUNT(*) FROM temperature_readings WHERE recorded_at >= $1",
        week_start
    )
    
    # Readings this month
    metrics['readings_this_month'] = await db.fetchval(
        "SELECT COUNT(*) FROM temperature_readings WHERE recorded_at >= $1",
        month_start
    )
    
    # Latest reading time
    metrics['latest_reading_time'] = await db.fetchval(
        "SELECT MAX(recorded_at) FROM temperature_readings"
    )
    
    # Customers by sharing method
    sharing_methods = await db.fetch(
        """
        SELECT data_sharing_method, COUNT(*) as count
        FROM customers
        WHERE is_active = true
        GROUP BY data_sharing_method
        """
    )
    metrics['customers_by_sharing_method'] = {
        row['data_sharing_method']: row['count'] for row in sharing_methods
    }
    
    # Readings by status
    status_counts = await db.fetch(
        """
        SELECT equipment_status, COUNT(*) as count
        FROM temperature_readings
        GROUP BY equipment_status
        """
    )
    metrics['readings_by_status'] = {
        row['equipment_status']: row['count'] for row in status_counts
    }
    
    return MetricsResponse(**metrics)