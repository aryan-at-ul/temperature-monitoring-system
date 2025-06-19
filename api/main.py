# api/main.py
import logging
import sys
import os
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from datetime import datetime


from api.auth.token_auth import get_current_customer, get_admin_user
from api.models.responses import ErrorResponse
from database.connection import DatabaseConnection  
from contextlib import asynccontextmanager

os.makedirs("logs", exist_ok=True)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/api.log"),
    ]
)

logger = logging.getLogger(__name__)




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
 
    try:
        db_manager = DatabaseConnection()
        await db_manager.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
       
    
    yield
    

    try:
        if 'db_manager' in locals():
            await db_manager.close()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

app = FastAPI(
    title="Temperature Monitoring API",
    description="API for temperature monitoring system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # this needs to be domain name
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from api.endpoints.health_routes import router as health_router
app.include_router(health_router, tags=["Health"])


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


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Temperature Monitoring API",
        version="1.0.0",
        description="API for temperature monitoring system",
        routes=app.routes,
    )
    

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your API token with the 'Bearer ' prefix"
        }
    }
    

    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if "security" not in operation:
                operation["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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