"""
Database & Cache exceptions for the EMS system.
Covers MSSQL (via SQLAlchemy) and Redis connection/operation errors.
"""

from app.core.exceptions.base import EMSException


# =============================================================================
# MSSQL / SQLAlchemy Exceptions
# =============================================================================

class DatabaseConnectionException(EMSException):
    """Raised when unable to establish a connection to MSSQL."""

    status_code = 503
    message = "Database Connection Error"
    detail = "Unable to connect to the database. Please try again later"


class DatabaseQueryException(EMSException):
    """Raised when a database query fails during execution."""

    status_code = 500
    message = "Database Query Error"
    detail = "An error occurred while executing a database query"

    def __init__(self, operation: str = "", reason: str = "", **kwargs):
        detail = "An error occurred while executing a database query"
        if operation and reason:
            detail = f"Database query failed during '{operation}': {reason}"
        elif operation:
            detail = f"Database query failed during '{operation}'"
        elif reason:
            detail = f"Database query error: {reason}"
        super().__init__(detail=detail, **kwargs)


class DatabaseIntegrityException(EMSException):
    """
    Raised when a database integrity constraint is violated.
    Examples: unique constraint, foreign key constraint, check constraint.
    """

    status_code = 409
    message = "Data Integrity Error"
    detail = "The operation violates a database integrity constraint"

    def __init__(self, constraint: str = "", **kwargs):
        detail = "The operation violates a database integrity constraint"
        if constraint:
            detail = f"Database integrity constraint violated: {constraint}"
        super().__init__(detail=detail, **kwargs)


class DatabaseTimeoutException(EMSException):
    """Raised when a database query exceeds the configured timeout."""

    status_code = 504
    message = "Database Timeout"
    detail = "The database query timed out. Please try again with a simpler query or contact the administrator"


# =============================================================================
# Redis / Cache Exceptions
# =============================================================================

class RedisConnectionException(EMSException):
    """Raised when unable to establish a connection to Redis."""

    status_code = 503
    message = "Cache Connection Error"
    detail = "Unable to connect to the cache server (Redis). Please try again later"


class CacheOperationException(EMSException):
    """Raised when a cache read/write/invalidation operation fails."""

    status_code = 500
    message = "Cache Operation Error"
    detail = "An error occurred during a cache operation"

    def __init__(self, operation: str = "", key: str = "", **kwargs):
        detail = "An error occurred during a cache operation"
        if operation and key:
            detail = f"Cache {operation} failed for key '{key}'"
        elif operation:
            detail = f"Cache {operation} operation failed"
        super().__init__(detail=detail, **kwargs)
