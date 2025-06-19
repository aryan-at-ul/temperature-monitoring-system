# api/auth/token_auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
from database.connection import db
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
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
        # Get the token from the database
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
            
        # Token found - get the data
        token_data = result[0]
        logger.debug(f"Token found: {token_data.get('token_name', 'unknown')}")
        
        # Update last_used_at
        try:
            await db.execute(
                "UPDATE customer_tokens SET last_used_at = NOW() WHERE token_hash = $1",
                token_hash
            )
        except Exception as e:
            logger.warning(f"Failed to update last_used_at: {str(e)}")
        
        # Process permissions from JSONB field
        permissions = token_data.get('permissions', [])
        logger.debug(f"Raw permissions: {permissions}, type: {type(permissions)}")
        
        # Handle different formats of permissions data
        if isinstance(permissions, str):
            try:
                # If it's stored as a string, parse it as JSON
                permissions = json.loads(permissions)
                logger.debug(f"Parsed JSON permissions: {permissions}")
            except json.JSONDecodeError:
                # If it's not valid JSON, treat it as a single permission
                permissions = [permissions]
                logger.debug(f"Treating as single permission: {permissions}")
        elif isinstance(permissions, list):
            # Already a list, keep as is
            logger.debug(f"Permissions already as list: {permissions}")
        else:
            # If it's neither string nor list, default to empty list
            logger.warning(f"Unexpected permissions format: {permissions}, defaulting to empty list")
            permissions = []
            
        # Ensure customer has necessary fields
        customer = {
            'id': token_data.get('customer_id'),
            'customer_code': token_data.get('customer_code'),
            'name': token_data.get('name'),
            'is_active': token_data.get('is_active', True),
            'permissions': permissions
        }
        
        logger.debug(f"Authenticated customer: {customer}")
        
        if not customer['id'] or not customer['customer_code']:
            logger.error(f"Missing critical customer data: {customer}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing customer data"
            )
        
        return customer
    except HTTPException:
        # Re-raise HTTP exceptions
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
    
    # Check if the token has admin permissions
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
    
    # Check if the token has read permission (or admin, which implies all permissions)
    if 'read' not in customer['permissions'] and 'admin' not in customer['permissions']:
        logger.warning(f"User {customer['customer_code']} attempted access without read permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read permission required"
        )
        
    return customer