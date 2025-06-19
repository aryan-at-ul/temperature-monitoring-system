import os
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
import logging
import asyncpg

from api.models.responses import HealthStatus, ErrorResponse
from database.connection import db
from data_ingestion.queue.rabbitmq_client import rabbitmq

logger = logging.getLogger(__name__)

router = APIRouter()

# Track service start time
start_time = time.time()

@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Health check",
    description="Check the health of the API and its dependencies",
    responses={
        500: {"model": ErrorResponse, "description": "Service unavailable"},
    }
)
async def health_check():
    """
    Check the health of the API and its dependencies.
    
    Verifies database and RabbitMQ connectivity.
    """
    try:
        # Check database connectivity
        db_status = "ok"
        try:
            await db.connect()
            await db.fetchval("SELECT 1")
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "error"
            
        # Check RabbitMQ connectivity
        rabbitmq_status = "ok"
        try:
            if not rabbitmq.connection or rabbitmq.connection.is_closed:
                await rabbitmq.connect()
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {e}")
            rabbitmq_status = "error"
            
        # Calculate uptime
        uptime_seconds = int(time.time() - start_time)
        
        # Get API version from environment or use default
        version = os.getenv("API_VERSION", "1.0.0")
        
        return HealthStatus(
            status="ok" if db_status == "ok" and rabbitmq_status == "ok" else "degraded",
            version=version,
            timestamp=datetime.now(),
            database=db_status,
            rabbitmq=rabbitmq_status,
            uptime_seconds=uptime_seconds
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service unavailable: {str(e)}"
        )


@router.get(
    "/ping",
    summary="Simple ping endpoint",
    description="Simple ping endpoint for load balancer health checks"
)
async def ping():
    """Simple ping endpoint for load balancer health checks."""
    return {"status": "ok"}