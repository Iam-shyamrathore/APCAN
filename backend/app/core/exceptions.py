"""
Custom Exception Classes
Industry standard: Domain-specific exceptions with HTTP status codes
"""

from fastapi import status


class APCANException(Exception):
    """Base exception for all APCAN errors"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(APCANException):
    """Authentication failed"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(APCANException):
    """Insufficient permissions"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundError(APCANException):
    """Resource not found"""

    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status.HTTP_404_NOT_FOUND)


class ValidationError(APCANException):
    """Validation failed"""

    def __init__(self, message: str):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class DatabaseError(APCANException):
    """Database operation failed"""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)
