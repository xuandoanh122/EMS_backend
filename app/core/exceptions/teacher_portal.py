"""
Teacher Portal exceptions.
"""

from typing import Optional

from app.core.exceptions.base import EMSException


class TeacherAuthRequiredException(EMSException):
    status_code = 401
    message = "Unauthorized"
    detail = "Teacher authentication is required"


class TeacherAccessDeniedException(EMSException):
    status_code = 403
    message = "Forbidden"
    detail = "You do not have access to this resource"

    def __init__(self, detail: Optional[str] = None) -> None:
        super().__init__(detail=detail or self.detail)


class TeacherAssignmentNotFoundException(EMSException):
    status_code = 404
    message = "Not Found"
    detail = "Teacher assignment not found"

    def __init__(self, detail: Optional[str] = None) -> None:
        super().__init__(detail=detail or self.detail)


class TeacherPortalValidationException(EMSException):
    status_code = 400
    message = "Bad Request"
    detail = "Invalid teacher portal request"

    def __init__(self, detail: Optional[str] = None) -> None:
        super().__init__(detail=detail or self.detail)
