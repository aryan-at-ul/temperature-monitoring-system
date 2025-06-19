# api/auth/permissions.py
from enum import Enum
from typing import List
from api.models.errors import PermissionError

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class PermissionChecker:
    """Check user permissions for various operations"""
    
    @staticmethod
    def check_permission(user_permissions: List[str], required_permission: Permission):
        """Check if user has required permission"""
        if Permission.ADMIN.value in user_permissions:
            return True  # Admin has all permissions
        
        if required_permission.value in user_permissions:
            return True
        
        raise PermissionError(f"Permission {required_permission.value} required")
    
    @staticmethod
    def check_customer_access(user_customer_id: str, requested_customer_id: str, 
                            user_permissions: List[str]):
        """Check if user can access requested customer data"""
        # Admin can access any customer
        if Permission.ADMIN.value in user_permissions:
            return True
        
        # Users can only access their own data
        if user_customer_id != requested_customer_id:
            raise PermissionError("Access denied: Cannot access other customer data")
        
        return True

