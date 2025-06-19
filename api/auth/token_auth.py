# api/auth/token_auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
from database.connection import db
import json
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_customer(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the token and returns the associated customer.
    """
    token = credentials.credentials
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    logger.debug(f"Validating token hash: {token_hash}")
    
    try:
 
        query = """
            SELECT ct.*, c.* 
            FROM customer_tokens ct
            JOIN customers c ON ct.customer_id = c.id
            WHERE ct.token_hash = $1 AND ct.is_active = TRUE
        """
        result = await db.fetch(query, token_hash)
        
        if not result:
            logger.warning(f"No matching token found for hash: {token_hash}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
            

        token_data = result[0]
        
    
        try:
            await db.execute(
                "UPDATE customer_tokens SET last_used_at = NOW() WHERE token_hash = $1",
                token_hash
            )
        except Exception as e:
            logger.warning(f"Failed to update last_used_at: {str(e)}")
        
      
        permissions = token_data.get('permissions', [])
        
        if isinstance(permissions, str):
            try:
               
                permissions = json.loads(permissions)
            except json.JSONDecodeError:
                
                permissions = [permissions]
        
        customer = {
            'id': token_data['customer_id'],
            'customer_code': token_data['customer_code'],
            'name': token_data['name'],
            'is_active': token_data['is_active'],
            'permissions': permissions
        }
        
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error"
        )

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the token and ensures it has admin permissions.
    """
    customer = await get_current_customer(credentials)
    
  
    if 'admin' not in customer['permissions']:
        logger.warning(f"User {customer['customer_code']} attempted admin access without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )
        
    return customer

async def check_read_permission(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the token and ensures it has read permission.
    """
    customer = await get_current_customer(credentials)
    
   
    if 'read' not in customer['permissions'] and 'admin' not in customer['permissions']:
        logger.warning(f"User {customer['customer_code']} attempted access without read permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read permission required"
        )
        
    return customer

async def check_write_permission(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the token and ensures it has write permission.
    """
    customer = await get_current_customer(credentials)
    
   
    if 'write' not in customer['permissions'] and 'admin' not in customer['permissions']:
        logger.warning(f"User {customer['customer_code']} attempted write operation without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write permission required"
        )
        
    return customer