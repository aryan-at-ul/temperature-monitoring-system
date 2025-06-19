# api/auth/token_manager.py (Updated for JSONB)
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, List
from database.connection import DatabaseConnection
from api.models.errors import AuthenticationError

class TokenManager:
    """Manage API tokens for customer authentication"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.secret_key = "your-secret-key-change-in-production-f8k3j9d0s2l1p4m7"
        self.algorithm = "HS256"
    
    def generate_token(self, customer_id: str, permissions: List[str] = None, 
                      expires_hours: int = 24) -> str:
        """Generate a new API token"""
        if permissions is None:
            permissions = ["read"]
        
        try:
            # Create simple token
            import time
            timestamp = str(int(time.time()))
            token = f"token_{customer_id}_{timestamp}_{'_'.join(permissions)}"
            
            # Store token hash in database
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Get customer database ID
            customer_result = self.db.execute_query(
                "SELECT id FROM customers WHERE customer_code = %s",
                (customer_id,)
            )
            
            if not customer_result:
                raise AuthenticationError(f"Customer {customer_id} not found")
            
            customer_db_id = customer_result[0]['id']
            
            # Store token in database with proper JSONB handling
            self.db.execute_command("""
                INSERT INTO customer_tokens 
                (customer_id, token_hash, token_name, permissions, expires_at, is_active)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
            """, (
                customer_db_id,
                token_hash,
                f"Generated token for {customer_id}",
                json.dumps(permissions),  # Convert to JSON string
                datetime.utcnow() + timedelta(hours=expires_hours),
                True
            ))
            
            return token
            
        except Exception as e:
            print(f"Debug - Token generation error for {customer_id}: {e}")
            raise AuthenticationError(f"Token generation failed: {e}")
    
    def verify_token(self, token: str) -> dict:
        """Verify API token"""
        try:
            # Check token hash in database
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            token_result = self.db.execute_query("""
                SELECT ct.*, c.customer_code
                FROM customer_tokens ct
                JOIN customers c ON ct.customer_id = c.id
                WHERE ct.token_hash = %s AND ct.is_active = TRUE
                AND (ct.expires_at IS NULL OR ct.expires_at > NOW())
            """, (token_hash,))
            
            if not token_result:
                raise AuthenticationError("Invalid or expired token")
            
            token_data = token_result[0]
            
            # Update last used timestamp
            self.db.execute_command(
                "UPDATE customer_tokens SET last_used_at = NOW() WHERE token_hash = %s",
                (token_hash,)
            )
            
            # Extract permissions (JSONB is automatically parsed by psycopg2)
            permissions = token_data['permissions']
            if isinstance(permissions, str):
                permissions = json.loads(permissions)
            
            return {
                "customer_id": token_data['customer_code'],
                "customer_db_id": token_data['customer_id'],
                "permissions": permissions,
                "token_id": token_data['id']
            }
            
        except Exception as e:
            print(f"Debug - Token verification error: {e}")
            raise AuthenticationError(f"Token verification failed: {e}")
    
    def revoke_token(self, token: str) -> bool:
        """Revoke an API token"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            affected = self.db.execute_command(
                "UPDATE customer_tokens SET is_active = FALSE WHERE token_hash = %s",
                (token_hash,)
            )
            
            return affected > 0
            
        except Exception:
            return False