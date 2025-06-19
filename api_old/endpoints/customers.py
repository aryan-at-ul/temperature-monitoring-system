# api/endpoints/customers.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from api.auth.middleware import get_current_user
from api.auth.permissions import PermissionChecker, Permission
from api.models.responses import Customer
from api.services.customer_service import CustomerService
from api.utils.helpers import trigger_data_generation, get_latest_data_files

router = APIRouter()
customer_service = CustomerService()

@router.get("/customers/me", response_model=Customer)
async def get_my_customer_info(user: dict = Depends(get_current_user)):
    """Get current customer's information"""
    
    PermissionChecker.check_permission(user["permissions"], Permission.READ)
    
    customer = customer_service.get_customer(user["customer_id"])
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer

@router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: str,
    user: dict = Depends(get_current_user)
):
    """Get specific customer information"""
    
    PermissionChecker.check_permission(user["permissions"], Permission.READ)
    PermissionChecker.check_customer_access(user["customer_id"], customer_id, user["permissions"])
    
    customer = customer_service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer

@router.post("/customers/me/trigger-ingestion")
async def trigger_my_data_ingestion(user: dict = Depends(get_current_user)):
    """Trigger data ingestion for current customer"""
    
    PermissionChecker.check_permission(user["permissions"], Permission.WRITE)
    
    # Get customer info to determine data method
    customer = customer_service.get_customer(user["customer_id"])
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Trigger data generation
    result = trigger_data_generation(user["customer_id"], customer.data_sharing_method)
    
    return {
        "customer_id": user["customer_id"],
        "data_sharing_method": customer.data_sharing_method,
        "ingestion_result": result,
        "message": "Data ingestion triggered successfully"
    }

@router.get("/customers/me/data-files")
async def get_my_data_files(user: dict = Depends(get_current_user)):
    """Get information about current customer's data files"""
    
    PermissionChecker.check_permission(user["permissions"], Permission.READ)
    
    data_info = get_latest_data_files(user["customer_id"])
    
    return {
        "customer_id": user["customer_id"],
        "data_files": data_info,
        "total_csv_files": len(data_info["csv_files"]),
        "total_json_files": len(data_info["json_files"]),
        "latest_csv_file": data_info["latest_csv"],
        "latest_json_file": data_info["latest_json"]
    }

@router.get("/customers/me/facilities")
async def get_my_facilities(user: dict = Depends(get_current_user)):
    """Get current customer's facilities with latest readings"""
    
    PermissionChecker.check_permission(user["permissions"], Permission.READ)
    
    customer = customer_service.get_customer(user["customer_id"])
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get latest readings for each facility
    from api.services.temperature_service import TemperatureService
    temp_service = TemperatureService()
    latest_readings = temp_service.get_latest_readings(user["customer_id"])
    
    # Group readings by facility
    facility_readings = {}
    for reading in latest_readings:
        if reading.facility_id not in facility_readings:
            facility_readings[reading.facility_id] = []
        facility_readings[reading.facility_id].append(reading)
    
    # Add readings to facilities
    facilities_with_readings = []
    for facility in customer.facilities:
        facility_dict = facility.dict()
        facility_dict["latest_readings"] = facility_readings.get(facility.facility_code, [])
        facility_dict["total_units"] = len(facility.storage_units)
        facility_dict["units_with_recent_data"] = len(facility_dict["latest_readings"])
        facilities_with_readings.append(facility_dict)
    
    return {
        "customer_id": user["customer_id"],
        "total_facilities": len(facilities_with_readings),
        "facilities": facilities_with_readings
    }

@router.get("/customers/me/units/{unit_id}/status")
async def get_my_unit_status(
    unit_id: str,
    user: dict = Depends(get_current_user)
):
    """Get detailed status for a specific storage unit"""
    
    PermissionChecker.check_permission(user["permissions"], Permission.READ)
    
    from database.connection import DatabaseConnection
    
    db = DatabaseConnection()
    try:
        # Get unit details with recent readings
        query = """
        SELECT 
            su.id,
            su.unit_code,
            su.name,
            su.size_value,
            su.size_unit,
            su.set_temperature,
            su.temperature_unit,
            su.equipment_type,
            f.facility_code,
            f.name as facility_name,
            c.customer_code,
            (
                SELECT COUNT(*) 
                FROM temperature_readings tr 
                WHERE tr.storage_unit_id = su.id 
                AND tr.recorded_at > NOW() - INTERVAL '24 hours'
            ) as readings_24h,
            (
                SELECT COUNT(*) 
                FROM temperature_readings tr 
                WHERE tr.storage_unit_id = su.id 
                AND tr.recorded_at > NOW() - INTERVAL '24 hours'
                AND tr.temperature IS NULL
            ) as failures_24h
        FROM storage_units su
        JOIN facilities f ON su.facility_id = f.id
        JOIN customers c ON f.customer_id = c.id
        WHERE su.unit_code = %s AND c.customer_code = %s
        """
        
        result = db.execute_query(query, (unit_id, user["customer_id"]))
        
        if not result:
            raise HTTPException(status_code=404, detail="Storage unit not found")
        
        unit_data = result[0]
        
        # Get recent readings
        readings_query = """
        SELECT temperature, temperature_unit, recorded_at, equipment_status, quality_score
        FROM temperature_readings tr
        JOIN storage_units su ON tr.storage_unit_id = su.id
        JOIN facilities f ON su.facility_id = f.id
        JOIN customers c ON f.customer_id = c.id
        WHERE su.unit_code = %s AND c.customer_code = %s
        ORDER BY recorded_at DESC
        LIMIT 10
        """
        
        recent_readings = db.execute_query(readings_query, (unit_id, user["customer_id"]))
        
        return {
            "unit_id": unit_data['unit_code'],
            "unit_name": unit_data['name'],
            "facility_id": unit_data['facility_code'],
            "facility_name": unit_data['facility_name'],
            "size": f"{unit_data['size_value']} {unit_data['size_unit']}",
            "set_temperature": f"{unit_data['set_temperature']}°{unit_data['temperature_unit']}",
            "equipment_type": unit_data['equipment_type'],
            "status": {
                "readings_last_24h": unit_data['readings_24h'],
                "failures_last_24h": unit_data['failures_24h'],
                "failure_rate": (unit_data['failures_24h'] / max(unit_data['readings_24h'], 1)) * 100
            },
            "recent_readings": [
                {
                    "temperature": float(r['temperature']) if r['temperature'] else None,
                    "temperature_unit": r['temperature_unit'],
                    "recorded_at": r['recorded_at'],
                    "equipment_status": r['equipment_status'],
                    "quality_score": float(r['quality_score'])
                }
                for r in recent_readings
            ]
        }
        
    finally:
        db.disconnect()