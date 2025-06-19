from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Body
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from api.auth.token_auth import get_admin_user
from api.models.customer import (
    AdminUser, CustomerResponse, CustomerTokenResponse
)
from api.models.temperature import (
    TemperatureStats, CustomerStats
)
from api.models.responses import SuccessResponse, ErrorResponse, MetricsResponse
from api.utils.auth_utils import generate_admin_token
from database.connection import db

router = APIRouter()


@router.get(
    "/admin/system/status",
    response_model=Dict[str, Any],
    summary="[Admin] Get system status",
    description="Get detailed system status information (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def admin_get_system_status(admin: AdminUser = Depends(get_admin_user)):
    """
    Get detailed system status information.
    
    Includes database metrics, queue status, and resource usage.
    """
    # Get current timestamp
    now = datetime.now()
    
    # Database metrics
    db_metrics = {}
    
    # Total records by table
    table_counts = await db.fetch(
        """
        SELECT 
            table_name, 
            (xpath('/row/cnt/text()', 
                    query_to_xml(format('SELECT COUNT(*) AS cnt FROM %I', table_name), 
                                false, true, '')))[1]::text::bigint AS count
        FROM 
            information_schema.tables
        WHERE 
            table_schema = 'public'
            AND table_type = 'BASE TABLE'
        ORDER BY 
            table_name
        """
    )
    
    db_metrics["table_records"] = {
        row["table_name"]: row["count"] for row in table_counts
    }
    
    # Latest records
    db_metrics["latest_readings"] = await db.fetchval(
        "SELECT MAX(recorded_at) FROM temperature_readings"
    )
    db_metrics["latest_logs"] = await db.fetchval(
        "SELECT MAX(start_time) FROM ingestion_logs"
    )
    
    # Recent activity
    db_metrics["readings_last_hour"] = await db.fetchval(
        "SELECT COUNT(*) FROM temperature_readings WHERE recorded_at > $1",
        now - timedelta(hours=1)
    )
    db_metrics["readings_last_day"] = await db.fetchval(
        "SELECT COUNT(*) FROM temperature_readings WHERE recorded_at > $1",
        now - timedelta(days=1)
    )
    
    # Ingestion stats
    ingestion_stats = await db.fetch(
        """
        SELECT 
            status, 
            COUNT(*) as count,
            SUM(records_processed) as total_processed,
            SUM(records_succeeded) as total_succeeded,
            SUM(records_failed) as total_failed,
            AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds
        FROM 
            ingestion_logs
        WHERE 
            start_time > $1
        GROUP BY 
            status
        """,
        now - timedelta(days=1)
    )
    
    db_metrics["ingestion_stats_24h"] = {
        row["status"]: {
            "count": row["count"],
            "total_processed": row["total_processed"],
            "total_succeeded": row["total_succeeded"],
            "total_failed": row["total_failed"],
            "avg_duration_seconds": row["avg_duration_seconds"]
        } for row in ingestion_stats
    }
    
    # Data volume by customer
    customer_volumes = await db.fetch(
        """
        SELECT 
            c.customer_code, 
            c.name,
            COUNT(tr.id) as reading_count,
            MIN(tr.recorded_at) as earliest_reading,
            MAX(tr.recorded_at) as latest_reading
        FROM 
            customers c
            LEFT JOIN temperature_readings tr ON c.id = tr.customer_id
        GROUP BY 
            c.id, c.customer_code, c.name
        ORDER BY 
            reading_count DESC
        """
    )
    
    customer_data = []
    for row in customer_volumes:
        customer_data.append({
            "customer_code": row["customer_code"],
            "name": row["name"],
            "reading_count": row["reading_count"],
            "earliest_reading": row["earliest_reading"],
            "latest_reading": row["latest_reading"]
        })
    
    # Build response
    status_data = {
        "timestamp": now,
        "database": db_metrics,
        "customers": customer_data
    }
    
    return status_data


@router.get(
    "/admin/system/logs",
    response_model=List[Dict[str, Any]],
    summary="[Admin] Get system logs",
    description="Get system ingestion logs (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def admin_get_system_logs(
    admin: AdminUser = Depends(get_admin_user),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    offset: int = Query(0, description="Number of logs to skip")
):
    """
    Get system ingestion logs.
    
    Filter by date range, status, or customer ID.
    """
    # Build base query
    query = """
        SELECT 
            il.*,
            c.customer_code,
            c.name as customer_name
        FROM 
            ingestion_logs il
            JOIN customers c ON il.customer_id = c.id
        WHERE 1=1
    """
    
    count_query = """
        SELECT COUNT(*)
        FROM 
            ingestion_logs il
            JOIN customers c ON il.customer_id = c.id
        WHERE 1=1
    """
    
    # Build where clause and parameters
    where_clauses = []
    params = []
    param_index = 1
    
    if start_date:
        where_clauses.append(f"il.start_time >= ${param_index}")
        params.append(start_date)
        param_index += 1
        
    if end_date:
        where_clauses.append(f"il.start_time <= ${param_index}")
        params.append(end_date)
        param_index += 1
        
    if status:
        where_clauses.append(f"il.status = ${param_index}")
        params.append(status)
        param_index += 1
        
    if customer_id:
        where_clauses.append(f"il.customer_id = ${param_index}")
        params.append(customer_id)
        param_index += 1
        
    # Add where clauses to queries
    if where_clauses:
        additional_clauses = " AND " + " AND ".join(where_clauses)
        query += additional_clauses
        count_query += additional_clauses
        
    # Add ordering and pagination
    query += " ORDER BY il.start_time DESC LIMIT $" + str(param_index) + " OFFSET $" + str(param_index + 1)
    params.append(limit)
    params.append(offset)
    
    # Execute queries
    logs = await db.fetch(query, *params)
    
    # Convert to dictionaries
    return [dict(log) for log in logs]


@router.post(
    "/admin/tokens",
    response_model=CustomerTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create admin token",
    description="Create a new admin token (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def admin_create_admin_token(
    token_name: str = Query(..., description="Token name"),
    admin: AdminUser = Depends(get_admin_user)
):
    """Create a new admin token."""
    # Generate admin token
    token_data = generate_admin_token(admin.user_id, admin.username)
    
    # Insert the token
    query = """
        INSERT INTO customer_tokens
            (id, customer_id, token_hash, token_name, permissions, accessible_units, 
             rate_limit_per_hour, created_at, is_active)
        VALUES
            ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id, customer_id, token_name, permissions, accessible_units,
                  rate_limit_per_hour, expires_at, last_used_at, created_at, is_active
    """
    
    token_id = str(uuid.uuid4())
    created_at = datetime.now()
    
    result = await db.fetchrow(
        query,
        token_id,
        admin.user_id,
        token_data['token_hash'],
        token_name,
        token_data['permissions'],
        {},  # accessible_units
        2000,  # rate_limit_per_hour
        created_at,
        True  # is_active
    )
    
    # Return the token with the raw token included (only time it's returned)
    response = CustomerTokenResponse(**result)
    response.token = token_data['token']
    
    return response


@router.get(
    "/admin/dashboard",
    response_model=Dict[str, Any],
    summary="[Admin] Get admin dashboard",
    description="Get system-wide dashboard metrics (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    }
)
async def admin_dashboard(
    admin: AdminUser = Depends(get_admin_user),
    days: int = Query(7, description="Number of days to include in time series data")
):
    """
    Get system-wide dashboard metrics.
    
    Includes customer statistics, data volume trends, and system health indicators.
    """
    # Current timestamp
    now = datetime.now()
    start_date = now - timedelta(days=days)
    
    # Basic metrics
    metrics = {}
    
    # Customer counts
    metrics["customer_count"] = await db.fetchval(
        "SELECT COUNT(*) FROM customers WHERE is_active = true"
    )
    metrics["facility_count"] = await db.fetchval(
        "SELECT COUNT(*) FROM facilities"
    )
    metrics["storage_unit_count"] = await db.fetchval(
        "SELECT COUNT(*) FROM storage_units"
    )
    
    # Reading statistics
    metrics["total_readings"] = await db.fetchval(
        "SELECT COUNT(*) FROM temperature_readings"
    )
    metrics["readings_today"] = await db.fetchval(
        "SELECT COUNT(*) FROM temperature_readings WHERE recorded_at >= $1",
        datetime(now.year, now.month, now.day)
    )
    
    # Status distribution
    status_counts = await db.fetch(
        """
        SELECT equipment_status, COUNT(*) as count
        FROM temperature_readings
        WHERE recorded_at >= $1
        GROUP BY equipment_status
        """,
        start_date
    )
    
    metrics["status_distribution"] = {
        row["equipment_status"]: row["count"] for row in status_counts
    }
    
    # Daily reading counts
    daily_counts = await db.fetch(
        """
        SELECT 
            DATE_TRUNC('day', recorded_at) as day,
            COUNT(*) as count
        FROM 
            temperature_readings
        WHERE 
            recorded_at >= $1
        GROUP BY 
            DATE_TRUNC('day', recorded_at)
        ORDER BY 
            day
        """,
        start_date
    )
    
    metrics["daily_reading_counts"] = [
        {"date": row["day"], "count": row["count"]} for row in daily_counts
    ]
    
    # Ingestion success rates
    ingestion_stats = await db.fetch(
        """
        SELECT 
            DATE_TRUNC('day', start_time) as day,
            status,
            COUNT(*) as count
        FROM 
            ingestion_logs
        WHERE 
            start_time >= $1
        GROUP BY 
            DATE_TRUNC('day', start_time),
            status
        ORDER BY 
            day, status
        """,
        start_date
    )
    
    # Group by day
    ingestion_by_day = {}
    for row in ingestion_stats:
        day = row["day"].isoformat()
        if day not in ingestion_by_day:
            ingestion_by_day[day] = {}
        ingestion_by_day[day][row["status"]] = row["count"]
    
    metrics["daily_ingestion_stats"] = [
        {"date": day, **stats} for day, stats in ingestion_by_day.items()
    ]
    
    # Customer data volume (top 5)
    customer_volumes = await db.fetch(
        """
        SELECT 
            c.customer_code,
            c.name,
            COUNT(tr.id) as reading_count
        FROM 
            customers c
            JOIN temperature_readings tr ON c.id = tr.customer_id
        WHERE 
            tr.recorded_at >= $1
        GROUP BY 
            c.id, c.customer_code, c.name
        ORDER BY 
            reading_count DESC
        LIMIT 5
        """,
        start_date
    )
    
    metrics["top_customers"] = [
        {
            "customer_code": row["customer_code"],
            "name": row["name"],
            "reading_count": row["reading_count"]
        } for row in customer_volumes
    ]
    
    return metrics