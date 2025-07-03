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



# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
    
#     openapi_schema = get_openapi(
#         title="Temperature Monitoring API",
#         version="1.0.0",
#         description="API for temperature monitoring system",
#         routes=app.routes,
#     )
    
#     # Add security scheme definition
#     openapi_schema["components"]["securitySchemes"] = {
#         "BearerAuth": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT",
#             "description": "Enter your API token with the 'Bearer ' prefix"
#         }
#     }
    
#     # All protected endpoints - using the same pattern that worked for temperature
#     protected_endpoints = [
#         # Temperature endpoints
#         "/api/v1/temperature",
#         "/api/v1/temperature/latest", 
#         "/api/v1/temperature/facility/{facility_id}",
#         "/api/v1/temperature/unit/{unit_id}",
#         "/api/v1/temperature/stats",
#         "/api/v1/temperature/aggregate",
#         "/api/v1/admin/temperature",
        
#         # Facilities endpoints
#         "/api/v1/facilities",
#         "/api/v1/facilities/{facility_id}",
#         "/api/v1/facilities/{facility_id}/detailed",
#         "/api/v1/facilities/{facility_id}/units",
#         "/api/v1/units/{unit_id}",
        
#         # Customer endpoints
#         "/api/v1/customers/profile",
#         "/api/v1/customers/tokens",
#         "/api/v1/customers/tokens/{token_id}",
        
#         # Analytics endpoints
#         "/api/v1/analytics/temperature/summary",
#         "/api/v1/analytics/temperature/trends",
#         "/api/v1/analytics/alarms/history",
#         "/api/v1/analytics/performance",
        
#         # Admin endpoints
#         "/api/v1/admin/customers",
#         "/api/v1/admin/customers/{customer_id}",
#         "/api/v1/admin/customers/{customer_id}/tokens",
#         "/api/v1/admin/facilities",
#         "/api/v1/admin/config",
#         "/api/v1/admin/config/{key}",
#         "/api/v1/admin/ingestion/logs",
#         "/api/v1/admin/analytics/temperature/summary",

#         # Health endpoints that require auth
#         "/system-info"  # Add this line

#     ]
    
#     # Use the same matching logic that worked for temperature endpoints
#     for path_key, path_item in openapi_schema["paths"].items():
#         if any(path_key.startswith(endpoint.replace("{", "{").replace("}", "}")) for endpoint in protected_endpoints):
#             for method, operation in path_item.items():
#                 if method in ["get", "post", "put", "delete", "patch"]:
#                     operation["security"] = [{"BearerAuth": []}]
    
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema



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
    

    protected_endpoints = [
        # Temperature endpoints
        "/api/v1/temperature",
        "/api/v1/temperature/latest", 
        "/api/v1/temperature/facility/{facility_id}",
        "/api/v1/temperature/unit/{unit_id}",
        "/api/v1/temperature/stats",
        "/api/v1/temperature/aggregate",
        "/api/v1/admin/temperature",
        
        # Facilities endpoints
        "/api/v1/facilities",
        "/api/v1/facilities/{facility_id}",
        "/api/v1/facilities/{facility_id}/detailed",
        "/api/v1/facilities/{facility_id}/units",
        "/api/v1/units/{unit_id}",
        
        # Customer endpoints
        "/api/v1/customers/profile",
        "/api/v1/customers/tokens",
        "/api/v1/customers/tokens/{token_id}",
        
        # Analytics endpoints
        "/api/v1/analytics/temperature/summary",
        "/api/v1/analytics/temperature/trends",
        "/api/v1/analytics/alarms/history",
        "/api/v1/analytics/performance",
        
        # Admin endpoints
        "/api/v1/admin/customers",
        "/api/v1/admin/customers/{customer_id}",
        "/api/v1/admin/customers/{customer_id}/tokens",
        "/api/v1/admin/facilities",
        "/api/v1/admin/config",
        "/api/v1/admin/config/{key}",
        "/api/v1/admin/ingestion/logs",
        "/api/v1/admin/analytics/temperature/summary",
        
        # Health endpoints, will require auth
        "/system-info"  
    ]
    
    # Use the same matching logic that worked for temperature endpoints
    for path_key, path_item in openapi_schema["paths"].items():
        # should ideally come from customer_token table >> accessible_units (todo)
        if path_key == "/system-info":
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    operation["security"] = [{"BearerAuth": []}]
                    print(f"Applied security to /system-info {method}")  

        elif any(path_key.startswith(endpoint.replace("{", "{").replace("}", "}")) for endpoint in protected_endpoints):
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
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
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000) #, reload=True)