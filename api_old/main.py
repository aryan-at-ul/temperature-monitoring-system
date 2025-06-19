import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

# Import API components
from api.auth.token_auth import get_current_customer, get_admin_user
from api.models.responses import ErrorResponse

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/api.log"),
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Temperature Monitoring API",
    description="API for temperature monitoring system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.endpoints.health_routes import router as health_router
app.include_router(health_router, tags=["Health"])

# Import other routers conditionally to avoid import errors if files don't exist yet
try:
    from api.endpoints.temperature_routes import router as temperature_router
    app.include_router(temperature_router, prefix="/api/v1", tags=["Temperature"])
except ImportError:
    logger.warning("Temperature routes not found, skipping")

try:
    from api.endpoints.facilities_routes import router as facilities_router
    app.include_router(facilities_router, prefix="/api/v1", tags=["Facilities"])
except ImportError:
    logger.warning("Facilities routes not found, skipping")

try:
    from api.endpoints.customers_routes import router as customers_router
    app.include_router(customers_router, prefix="/api/v1", tags=["Customers"])
except ImportError:
    logger.warning("Customers routes not found, skipping")

try:
    from api.endpoints.admin_routes import router as admin_router
    app.include_router(admin_router, prefix="/api/v1", tags=["Admin"])
except ImportError:
    logger.warning("Admin routes not found, skipping")

try:
    from api.endpoints.analytics_routes import router as analytics_router
    app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"])
except ImportError:
    logger.warning("Analytics routes not found, skipping")

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Temperature Monitoring API",
        "version": "1.0.0",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
