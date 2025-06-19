import hashlib
import secrets
import string
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def generate_token(length: int = 32) -> str:
    """
    Generate a random token string
    
    Args:
        length: Length of the token
        
    Returns:
        Random token string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_token(token: str) -> str:
    """
    Hash a token for storage in the database
    
    Args:
        token: The token to hash
        
    Returns:
        SHA-256 hash of the token as a hex string
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def verify_token_hash(token: str) -> Optional[str]:
    """
    Verify a token by hashing it for comparison
    
    Args:
        token: The raw token string
        
    Returns:
        Hashed token if valid, None if invalid
    """
    try:
        return hash_token(token)
    except Exception as e:
        logger.error(f"Error hashing token: {e}")
        return None


def generate_customer_tokens(customer_id: str, customer_code: str) -> Dict[str, Any]:
    """
    Generate read and write tokens for a customer
    
    Args:
        customer_id: UUID of the customer
        customer_code: Customer code
        
    Returns:
        Dictionary with token information
    """
    read_token = generate_token()
    write_token = generate_token()
    
    return {
        "read": {
            "token": read_token,
            "token_hash": hash_token(read_token),
            "token_name": f"Read token for {customer_code}",
            "permissions": ["read"],
            "customer_id": customer_id
        },
        "write": {
            "token": write_token,
            "token_hash": hash_token(write_token),
            "token_name": f"Write token for {customer_code}",
            "permissions": ["read", "write"],
            "customer_id": customer_id
        }
    }


def generate_admin_token(user_id: str, username: str) -> Dict[str, Any]:
    """
    Generate an admin token
    
    Args:
        user_id: UUID of the admin user
        username: Admin username
        
    Returns:
        Dictionary with admin token information
    """
    admin_token = generate_token()
    
    return {
        "token": admin_token,
        "token_hash": hash_token(admin_token),
        "token_name": f"Admin token for {username}",
        "permissions": ["read", "write", "admin"],
        "customer_id": user_id
    }