"""
Authentication & Authorization exceptions for the EMS system.
Covers JWT token handling, role-based access control (RBAC),
and account status management.
"""

from app.core.exceptions.base import EMSException


# =============================================================================
# 401 - Authentication Errors
# =============================================================================

class InvalidCredentialsException(EMSException):
    """Raised when username/password combination is incorrect."""

    status_code = 401
    message = "Invalid Credentials"
    detail = "The provided username or password is incorrect"


class TokenExpiredException(EMSException):
    """Raised when the JWT token has expired."""

    status_code = 401
    message = "Token Expired"
    detail = "Your authentication token has expired. Please log in again"


class TokenInvalidException(EMSException):
    """Raised when the JWT token is malformed or cannot be decoded."""

    status_code = 401
    message = "Invalid Token"
    detail = "The provided authentication token is invalid"


class TokenBlacklistedException(EMSException):
    """Raised when the JWT token has been revoked/blacklisted (stored in Redis)."""

    status_code = 401
    message = "Token Revoked"
    detail = "This authentication token has been revoked. Please log in again"


# =============================================================================
# 403 - Authorization Errors (RBAC: Admin, Giáo viên, Kế toán, Học sinh)
# =============================================================================

class InsufficientRoleException(EMSException):
    """Raised when the user's role does not have access to the requested resource."""

    status_code = 403
    message = "Insufficient Role"
    detail = "Your role does not have permission to access this resource"

    def __init__(self, required_role: str = "", current_role: str = "", **kwargs):
        detail = "Your role does not have permission to access this resource"
        if required_role and current_role:
            detail = (
                f"Access denied. Required role: '{required_role}', "
                f"your role: '{current_role}'"
            )
        elif required_role:
            detail = f"Access denied. Required role: '{required_role}'"
        super().__init__(detail=detail, **kwargs)


class AccountDisabledException(EMSException):
    """Raised when attempting to authenticate with a disabled account."""

    status_code = 403
    message = "Account Disabled"
    detail = "This account has been disabled. Please contact the administrator"


class AccountLockedException(EMSException):
    """Raised when the account is locked due to too many failed login attempts."""

    status_code = 423
    message = "Account Locked"
    detail = "This account has been locked due to too many failed login attempts. Please try again later or contact the administrator"
