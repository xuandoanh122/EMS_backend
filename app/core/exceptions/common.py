"""
Common exceptions used across all modules in the EMS system.
These are generic, reusable exceptions not tied to any specific domain.
"""

from app.core.exceptions.base import EMSException


# =============================================================================
# 400 - Bad Request
# =============================================================================

class BadRequestException(EMSException):
    """Raised when the request is malformed or contains invalid parameters."""

    status_code = 400
    message = "Bad Request"
    detail = "The request could not be understood or was missing required parameters"


# =============================================================================
# 404 - Not Found
# =============================================================================

class NotFoundException(EMSException):
    """Raised when a requested resource is not found."""

    status_code = 404
    message = "Not Found"
    detail = "The requested resource was not found"

    def __init__(self, resource: str = "Resource", identifier: str = "", **kwargs):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} with identifier '{identifier}' not found"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# 409 - Conflict / Already Exists
# =============================================================================

class AlreadyExistsException(EMSException):
    """Raised when attempting to create a resource that already exists."""

    status_code = 409
    message = "Already Exists"
    detail = "The resource already exists"

    def __init__(self, resource: str = "Resource", identifier: str = "", **kwargs):
        detail = f"{resource} already exists"
        if identifier:
            detail = f"{resource} with identifier '{identifier}' already exists"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# 422 - Validation Error
# =============================================================================

class ValidationException(EMSException):
    """Raised when input data fails validation rules."""

    status_code = 422
    message = "Validation Error"
    detail = "The provided data failed validation"


# =============================================================================
# 403 - Forbidden / Permission Denied
# =============================================================================

class PermissionDeniedException(EMSException):
    """Raised when the user does not have permission to perform the action."""

    status_code = 403
    message = "Permission Denied"
    detail = "You do not have permission to perform this action"


# =============================================================================
# 500 - Internal Server Error
# =============================================================================

class InternalServerException(EMSException):
    """Raised for unexpected internal server errors."""

    status_code = 500
    message = "Internal Server Error"
    detail = "An unexpected internal error occurred. Please try again later"


# =============================================================================
# 429 - Rate Limit Exceeded
# =============================================================================

class RateLimitExceededException(EMSException):
    """Raised when the user exceeds the allowed request rate."""

    status_code = 429
    message = "Rate Limit Exceeded"
    detail = "Too many requests. Please slow down and try again later"


# =============================================================================
# 400 - File Processing Error
# =============================================================================

class FileProcessingException(EMSException):
    """Raised when there is an error processing a file (import/export Excel, CSV, PDF)."""

    status_code = 400
    message = "File Processing Error"
    detail = "An error occurred while processing the file"

    def __init__(self, filename: str = "", reason: str = "", **kwargs):
        detail = "An error occurred while processing the file"
        if filename and reason:
            detail = f"Failed to process file '{filename}': {reason}"
        elif filename:
            detail = f"Failed to process file '{filename}'"
        elif reason:
            detail = f"File processing error: {reason}"
        super().__init__(detail=detail, **kwargs)
