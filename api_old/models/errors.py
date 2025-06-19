class BaseError(Exception):
    """Base error class for API exceptions"""
    
    def __init__(self, message: str = None):
        self.message = message or "An error occurred"
        super().__init__(self.message)


class AuthenticationError(BaseError):
    """Raised for authentication failures"""
    
    def __init__(self, message: str = None):
        super().__init__(message or "Authentication failed")


class AuthorizationError(BaseError):
    """Raised for authorization failures"""
    
    def __init__(self, message: str = None):
        super().__init__(message or "Not authorized to perform this operation")


class ResourceNotFoundError(BaseError):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource_type: str = "Resource", identifier: str = None):
        message = f"{resource_type} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message)


class ValidationError(BaseError):
    """Raised for data validation errors"""
    
    def __init__(self, message: str = None, field: str = None):
        if field:
            message = f"Validation error on field '{field}': {message or 'invalid value'}"
        super().__init__(message or "Validation failed")


class DatabaseError(BaseError):
    """Raised for database operation errors"""
    
    def __init__(self, message: str = None, operation: str = None):
        if operation:
            message = f"Database error during {operation}: {message or 'operation failed'}"
        super().__init__(message or "Database operation failed")


class ConfigurationError(BaseError):
    """Raised for system configuration errors"""
    
    def __init__(self, message: str = None, component: str = None):
        if component:
            message = f"Configuration error in {component}: {message or 'invalid configuration'}"
        super().__init__(message or "System configuration error")


class DataIngestionError(BaseError):
    """Raised for data ingestion errors"""
    
    def __init__(self, message: str = None, customer_id: str = None):
        if customer_id:
            message = f"Data ingestion error for customer {customer_id}: {message or 'ingestion failed'}"
        super().__init__(message or "Data ingestion failed")


class RateLimitError(BaseError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = None, limit: int = None):
        if limit:
            message = f"Rate limit exceeded: {limit} requests per hour allowed"
        super().__init__(message or "Rate limit exceeded")