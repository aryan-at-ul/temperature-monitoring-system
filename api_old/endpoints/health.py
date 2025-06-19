# api/endpoints/health.py
from fastapi import APIRouter, Depends
from datetime import datetime
import time
import psutil
from database.connection import test_connection
from api.models.responses import HealthResponse
from api.auth.middleware import get_optional_user

router = APIRouter()

# Track startup time
startup_time = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check(user: dict = Depends(get_optional_user)):
    """System health check endpoint"""
    
    # Test database connection
    db_status = "healthy" if test_connection() else "unhealthy"
    
    # Calculate uptime
    uptime_seconds = time.time() - startup_time
    
    # Get system metrics
    memory_percent = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent()
    disk_percent = psutil.disk_usage('/').percent
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        timestamp=datetime.utcnow(),
        database_status=db_status,
        version="1.0.0",
        uptime_seconds=uptime_seconds,
        system_metrics={
            "memory_usage_percent": memory_percent,
            "cpu_usage_percent": cpu_percent,
            "disk_usage_percent": disk_percent
        }
    )

@router.get("/health/detailed")
async def detailed_health_check(user: dict = Depends(get_optional_user)):
    """Detailed health check with database statistics"""
    
    from database.connection import DatabaseConnection
    
    try:
        db = DatabaseConnection()
        
        # Get database statistics
        stats = db.execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM customers WHERE is_active = TRUE) as active_customers,
                (SELECT COUNT(*) FROM temperature_readings) as total_readings,
                (SELECT MAX(recorded_at) FROM temperature_readings) as latest_reading,
                (SELECT COUNT(*) FROM temperature_readings WHERE recorded_at > NOW() - INTERVAL '1 hour') as recent_readings
        """)[0]
        
        db.disconnect()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": "connected",
                "active_customers": stats['active_customers'],
                "total_readings": stats['total_readings'],
                "latest_reading": stats['latest_reading'],
                "recent_readings": stats['recent_readings']
            },
            "system": {
                "uptime_seconds": time.time() - startup_time,
                "memory_percent": psutil.virtual_memory().percent,
                "cpu_percent": psutil.cpu_percent(),
                "disk_percent": psutil.disk_usage('/').percent
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "database": {"status": "disconnected"}
        }