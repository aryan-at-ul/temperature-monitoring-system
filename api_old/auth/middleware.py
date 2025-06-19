from typing import Optional, List
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.auth.token_manager import TokenManager
from api.models.errors import AuthenticationError

# Create a custom HTTPBearer class that doesn't require authentication
class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        try:
            return await super().__call__(request)
        except HTTPException:
            return None

# Use our custom security class
security = OptionalHTTPBearer(scheme_name="API Key Authentication")

async def get_auth_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Extract and verify API token from request"""
    token_manager = TokenManager()
    
    # First check if token is in query parameters (for browser testing)
    token = request.query_params.get('token')
    
    # If not in query params, use the Authorization header
    if not token and credentials:
        token = credentials.credentials
    
    # No token found
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify the token
        token_data = token_manager.verify_token(token)
        return token_data
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_customer(
    token_data: dict = Depends(get_auth_token)
) -> dict:
    """Get current customer from token data"""
    return {
        "customer_id": token_data["customer_id"],
        "customer_db_id": token_data["customer_db_id"],
        "permissions": token_data["permissions"],
        "token_id": token_data["token_id"]
    }


# Permission dependency functions
def has_permission(required_permission: str):
    """Check if customer has required permission"""
    async def _has_permission(customer: dict = Depends(get_current_customer)) -> dict:
        if required_permission not in customer["permissions"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required",
            )
        return customer
    return _has_permission


# Commonly used permission dependencies
has_read_permission = has_permission("read")
has_write_permission = has_permission("write")
has_admin_permission = has_permission("admin")