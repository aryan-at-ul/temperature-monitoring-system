# api/endpoints/admin.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import datetime
from datetime import datetime
from api.auth.middleware import get_current_user
from api.auth.permissions import PermissionChecker, Permission
from api.models.requests import TokenRequest
from api.models.responses import Customer, TokenResponse
from api.services.customer_service import CustomerService
from api.auth.token_manager import TokenManager
from api.utils.helpers import trigger_data_generation, get_latest_data_files

router = APIRouter()
customer_service = CustomerService()
token_manager = TokenManager()

@router.get("/customers", response_model=List[Customer])
async def get_all_customers(user: dict = Depends(get_current_user)):
    """Get all customers (admin only)"""
    
    PermissionChecker.check_permission(user["permissions"], Permission.ADMIN)
    
    return customer_service.get_customers()

@router.get("/customers/{customer_id}/status")
async def get_customer_status(
    customer_id: str,
    user: dict = Depends(get_current_user)
):
    """Get detailed customer status (admin only)"""
    
    PermissionChecker.check_permission(user["permissions"], Permission.ADMIN)
    
    from database.connection import DatabaseConnection
    
    db = DatabaseConnection()
    try:
        # Get customer with statistics
        query = """
        SELECT 
            c.id,
            c.customer_code,
            c.name,
            c.data_sharing_method,
            c.data_frequency_seconds,
            c.is_active,
            c.created_at,
            c.updated_at,
            COUNT(DISTINCT f.id) as facility_count,
            COUNT(DISTINCT su.id) as unit_count,
            COUNT(DISTINCT tr.id) as total_readings,
            COUNT(CASE WHEN tr.recorded_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_readings,
            COUNT(CASE WHEN tr.temperature IS NULL AND tr.recorded_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_failures,
            MAX(tr.recorded_at) as last_reading_at
        FROM customers c
        LEFT JOIN facilities f ON c.id = f.customer_id
        LEFT JOIN storage_units su ON f.id = su.facility_id
        LEFT JOIN temperature_readings tr ON su.id = tr.storage_unit_id
        WHERE c.customer_code = %s
        GROUP BY c.id
        """
        
        result = db.execute_query(query, (customer_id,))
        
        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_data = result[0]
        
        # Get data files info
        data_files = get_latest_data_files(customer_id)
        
        return {
            "customer_id": customer_data['customer_code'],
            "name": customer_data['name'],
            "data_sharing_method": customer_data['data_sharing_method'],
            "data_frequency_seconds": customer_data['data_frequency_seconds'],
            "is_active": customer_data['is_active'],
            "created_at": customer_data['created_at'],
            "updated_at": customer_data['updated_at'],
            "statistics": {
                "facility_count": customer_data['facility_count'],
                "unit_count": customer_data['unit_count'],
                "total_readings": customer_data['total_readings'],
                "recent_readings_24h": customer_data['recent_readings'],
                "recent_failures_24h": customer_data['recent_failures'],
                "last_reading_at": customer_data['last_reading_at']
            },
            "data_files": {
                "total_csv_files": len(data_files["csv_files"]),
                "total_json_files": len(data_files["json_files"]),
                "latest_csv": data_files["latest_csv"],
                "latest_json": data_files["latest_json"]
            }
        }
        
    finally:
        db.disconnect()

@router.patch("/customers/{customer_id}/activate")
async def activate_customer(
    customer_id: str,
    user: dict = Depends(get_current_user)
):
    """Activate a customer (admin only)"""
    
    PermissionChecker.check_permission(user["permissions"], Permission.ADMIN)
    
    from database.connection import DatabaseConnection
    
    db = DatabaseConnection()
    try:
        affected = db.execute_command(
            "UPDATE customers SET is_active = TRUE, updated_at = NOW() WHERE customer_code = %s",
            (customer_id,)
        )

        if affected == 0:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {
            "customer_id": customer_id,
            "status": "activated",
            "message": f"Customer {customer_id} has been activated",
            "timestamp": datetime.utcnow().isoformat()
        }

    finally:
        db.disconnect()

@router.patch("/customers/{customer_id}/deactivate")
async def deactivate_customer(
   customer_id: str,
   user: dict = Depends(get_current_user)
):
   """Deactivate a customer (admin only)"""
   
   PermissionChecker.check_permission(user["permissions"], Permission.ADMIN)
   
   from database.connection import DatabaseConnection
   
   db = DatabaseConnection()
   try:
       affected = db.execute_command(
           "UPDATE customers SET is_active = FALSE, updated_at = NOW() WHERE customer_code = %s",
           (customer_id,)
       )
       
       if affected == 0:
           raise HTTPException(status_code=404, detail="Customer not found")
       
       return {
           "customer_id": customer_id,
           "status": "deactivated",
           "message": f"Customer {customer_id} has been deactivated",
           "timestamp": datetime.utcnow().isoformat()
       }
       
   finally:
       db.disconnect()

@router.post("/customers/{customer_id}/trigger-ingestion")
async def trigger_customer_ingestion(
   customer_id: str,
   user: dict = Depends(get_current_user)
):
   """Trigger data ingestion for any customer (admin only)"""
   
   PermissionChecker.check_permission(user["permissions"], Permission.ADMIN)
   
   # Get customer info
   customer = customer_service.get_customer(customer_id)
   if not customer:
       raise HTTPException(status_code=404, detail="Customer not found")
   
   # Trigger data generation
   result = trigger_data_generation(customer_id, customer.data_sharing_method)
   
   return {
       "customer_id": customer_id,
       "data_sharing_method": customer.data_sharing_method,
       "ingestion_result": result,
       "triggered_by": user["customer_id"],
       "message": f"Data ingestion triggered for customer {customer_id}"
   }

@router.post("/tokens", response_model=TokenResponse)
async def create_token(
   token_request: TokenRequest,
   user: dict = Depends(get_current_user)
):
   """Create a new API token (admin only)"""
   
   PermissionChecker.check_permission(user["permissions"], Permission.ADMIN)
   
   # Verify customer exists
   customer = customer_service.get_customer(token_request.customer_id)
   if not customer:
       raise HTTPException(status_code=404, detail="Customer not found")
   
   # Generate token
   token = token_manager.generate_token(
       token_request.customer_id,
       token_request.permissions,
       token_request.expires_hours
   )
   
   from datetime import datetime, timedelta
   expires_at = datetime.utcnow() + timedelta(hours=token_request.expires_hours)
   
   return TokenResponse(
       token=token,
       expires_at=expires_at,
       permissions=token_request.permissions
   )

@router.get("/system/overview")
async def get_system_overview(user: dict = Depends(get_current_user)):
   """Get system overview (admin only)"""
   
   PermissionChecker.check_permission(user["permissions"], Permission.ADMIN)
   
   from database.connection import DatabaseConnection
   
   db = DatabaseConnection()
   try:
       # Get comprehensive system statistics
       stats_query = """
       SELECT 
           (SELECT COUNT(*) FROM customers WHERE is_active = TRUE) as active_customers,
           (SELECT COUNT(*) FROM customers WHERE is_active = FALSE) as inactive_customers,
           (SELECT COUNT(*) FROM facilities) as total_facilities,
           (SELECT COUNT(*) FROM storage_units) as total_units,
           (SELECT COUNT(*) FROM temperature_readings) as total_readings,
           (SELECT COUNT(*) FROM temperature_readings WHERE recorded_at > NOW() - INTERVAL '24 hours') as recent_readings,
           (SELECT COUNT(*) FROM temperature_readings WHERE temperature IS NULL AND recorded_at > NOW() - INTERVAL '24 hours') as recent_failures,
           (SELECT MAX(recorded_at) FROM temperature_readings) as latest_reading,
           (SELECT COUNT(*) FROM customer_tokens WHERE is_active = TRUE) as active_tokens
       """
       
       stats = db.execute_query(stats_query)[0]
       
       # Get customer breakdown by data sharing method
       method_breakdown = db.execute_query("""
           SELECT 
               data_sharing_method,
               COUNT(*) as customer_count,
               SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_count
           FROM customers
           GROUP BY data_sharing_method
       """)
       
       # Get recent activity
       recent_activity = db.execute_query("""
           SELECT 
               c.customer_code,
               COUNT(*) as reading_count,
               MAX(tr.recorded_at) as last_reading
           FROM temperature_readings tr
           JOIN storage_units su ON tr.storage_unit_id = su.id
           JOIN facilities f ON su.facility_id = f.id
           JOIN customers c ON f.customer_id = c.id
           WHERE tr.recorded_at > NOW() - INTERVAL '1 hour'
           GROUP BY c.customer_code
           ORDER BY reading_count DESC
           LIMIT 10
       """)
       
       return {
           "system_statistics": {
               "customers": {
                   "active": stats['active_customers'],
                   "inactive": stats['inactive_customers'],
                   "total": stats['active_customers'] + stats['inactive_customers']
               },
               "infrastructure": {
                   "total_facilities": stats['total_facilities'],
                   "total_units": stats['total_units']
               },
               "data": {
                   "total_readings": stats['total_readings'],
                   "recent_readings_24h": stats['recent_readings'],
                   "recent_failures_24h": stats['recent_failures'],
                   "latest_reading": stats['latest_reading']
               },
               "security": {
                   "active_tokens": stats['active_tokens']
               }
           },
           "customer_breakdown": [
               {
                   "data_sharing_method": row['data_sharing_method'],
                   "total_customers": row['customer_count'],
                   "active_customers": row['active_count']
               }
               for row in method_breakdown
           ],
           "recent_activity": [
               {
                   "customer_id": row['customer_code'],
                   "readings_last_hour": row['reading_count'],
                   "last_reading_at": row['last_reading']
               }
               for row in recent_activity
           ],
           "generated_at": datetime.utcnow().isoformat()
       }
       
   finally:
       db.disconnect()

@router.get("/system/alerts")
async def get_system_alerts(
   severity: Optional[str] = Query(None, description="Filter by severity: warning, critical"),
   user: dict = Depends(get_current_user)
):
   """Get system-wide alerts (admin only)"""
   
   PermissionChecker.check_permission(user["permissions"], Permission.ADMIN)
   
   from database.connection import DatabaseConnection
   
   db = DatabaseConnection()
   try:
       alerts = []
       
       # Check for customers with no recent data
       inactive_customers = db.execute_query("""
           SELECT 
               c.customer_code,
               c.name,
               MAX(tr.recorded_at) as last_reading,
               c.is_active
           FROM customers c
           LEFT JOIN facilities f ON c.id = f.customer_id
           LEFT JOIN storage_units su ON f.id = su.facility_id
           LEFT JOIN temperature_readings tr ON su.id = tr.storage_unit_id
           WHERE c.is_active = TRUE
           GROUP BY c.id
           HAVING MAX(tr.recorded_at) < NOW() - INTERVAL '2 hours' OR MAX(tr.recorded_at) IS NULL
       """)
       
       for customer in inactive_customers:
           alerts.append({
               "type": "no_recent_data",
               "severity": "warning",
               "customer_id": customer['customer_code'],
               "message": f"No data received from {customer['name']} in over 2 hours",
               "last_reading": customer['last_reading'],
               "detected_at": datetime.utcnow().isoformat()
           })
       
       # Check for high failure rates
       high_failure_customers = db.execute_query("""
           SELECT 
               c.customer_code,
               c.name,
               COUNT(*) as total_readings,
               COUNT(CASE WHEN tr.temperature IS NULL THEN 1 END) as failed_readings,
               ROUND(COUNT(CASE WHEN tr.temperature IS NULL THEN 1 END) * 100.0 / COUNT(*), 2) as failure_rate
           FROM temperature_readings tr
           JOIN storage_units su ON tr.storage_unit_id = su.id
           JOIN facilities f ON su.facility_id = f.id
           JOIN customers c ON f.customer_id = c.id
           WHERE tr.recorded_at > NOW() - INTERVAL '24 hours'
           AND c.is_active = TRUE
           GROUP BY c.id
           HAVING COUNT(CASE WHEN tr.temperature IS NULL THEN 1 END) * 100.0 / COUNT(*) > 5
       """)
       
       for customer in high_failure_customers:
           severity = "critical" if customer['failure_rate'] > 15 else "warning"
           alerts.append({
               "type": "high_failure_rate",
               "severity": severity,
               "customer_id": customer['customer_code'],
               "message": f"High failure rate for {customer['name']}: {customer['failure_rate']}%",
               "failure_rate": customer['failure_rate'],
               "failed_readings": customer['failed_readings'],
               "total_readings": customer['total_readings'],
               "detected_at": datetime.utcnow().isoformat()
           })
       
       # Filter by severity if requested
       if severity:
           alerts = [alert for alert in alerts if alert['severity'] == severity]
       
       return {
           "alerts": alerts,
           "total_alerts": len(alerts),
           "critical_count": len([a for a in alerts if a['severity'] == 'critical']),
           "warning_count": len([a for a in alerts if a['severity'] == 'warning']),
           "generated_at": datetime.utcnow().isoformat()
       }
       
   finally:
       db.disconnect()

# Future admin features (placeholders)
@router.post("/system/ml/train")
async def trigger_ml_training(
   model_type: str = Query("temperature_predictor", description="Model type to train"),
   user: dict = Depends(get_current_user)
):
   """Trigger ML model training (admin only - coming soon)"""
   
   PermissionChecker.check_permission(user["permissions"], Permission.ADMIN)
   
   return {
       "message": "ML model training feature coming soon",
       "model_type": model_type,
       "feature": "ml_training",
       "status": "planned",
       "estimated_release": "Q3 2025"
   }

@router.get("/system/ml/models")
async def get_ml_models(user: dict = Depends(get_current_user)):
   """Get ML model status (admin only - coming soon)"""
   
   PermissionChecker.check_permission(user["permissions"], Permission.ADMIN)
   
   return {
       "message": "ML model management feature coming soon",
       "feature": "ml_model_management",
       "status": "planned",
       "estimated_release": "Q3 2025"
   }