# api/endpoints/health_routes.py
from fastapi import APIRouter, status
from datetime import datetime
import logging
import traceback
import os
import sys
import psutil
import platform
from database.connection import db

router = APIRouter()
logger = logging.getLogger(__name__)

start_time = datetime.now()

@router.get(
    "/health",
    summary="Health check",
    description="Check the health of the API and its dependencies",
    tags=["Health"]
)
async def health_check():
    """
    Check the health of the API and its dependencies.
    """
    try:
        # Check database connection
        db_status = "ok"
        try:
            # Try a simple query to check the database connection
            await db.fetchval("SELECT 1")
        except Exception as e:
            db_status = f"error: {str(e)}"
            logger.error(f"Database health check failed: {str(e)}")
            logger.error(traceback.format_exc())
        
        # Check RabbitMQ connection (if applicable)
        rabbitmq_status = "ok"
        try:
            # Assuming rabbitmq client is available
            from data_ingestion.queue.rabbitmq_client import check_connection
            if not await check_connection():
                rabbitmq_status = "error: connection failed"
        except Exception as e:
            rabbitmq_status = f"error: {str(e)}"
            logger.error(f"RabbitMQ health check failed: {str(e)}")
            logger.error(traceback.format_exc())
        
        # Calculate uptime
        uptime = datetime.now() - start_time
        uptime_seconds = uptime.total_seconds()
        
        return {
            "status": "ok",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "rabbitmq": rabbitmq_status,
            "uptime_seconds": int(uptime_seconds)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get(
    "/ping",
    summary="Ping",
    description="Simple ping endpoint for load balancer health checks",
    tags=["Health"]
)
async def ping():
    """
    Simple ping endpoint for load balancer health checks.
    """
    return {"ping": "pong"}

@router.get(
    "/system-info",
    summary="System information",
    description="Get detailed system information (admin only)",
    tags=["Health"]
)
async def system_info():
    """
    Get detailed system information about the server.
    """
    try:
        # Get system information
        system_info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "cpu_count": os.cpu_count(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "process": {
                "pid": os.getpid(),
                "memory_percent": psutil.Process(os.getpid()).memory_percent(),
                "cpu_percent": psutil.Process(os.getpid()).cpu_percent(interval=0.1),
                "threads": len(psutil.Process(os.getpid()).threads()),
                "connections": len(psutil.Process(os.getpid()).connections())
            },
            "environment": {
                "hostname": platform.node(),
                "timezone": datetime.now().astimezone().tzinfo
            }
        }
        
        return system_info
    except Exception as e:
        logger.error(f"System info check failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e)
        }