"""
Base exception class for the EMS (Education Management System).
All custom exceptions in the system inherit from EMSException.
"""

from typing import Any, Optional


class EMSException(Exception):
    """
    Base exception for the entire EMS system.

    Attributes:
        status_code: HTTP status code to return to the client.
        message: Short, user-friendly error message.
        detail: Detailed description for developers/debugging.
        errors: Optional additional error data (validation errors, etc.).
    """

    status_code: int = 500
    message: str = "Internal Server Error"
    detail: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        status_code: Optional[int] = None,
        errors: Optional[Any] = None,
    ) -> None:
        if message is not None:
            self.message = message
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        self.errors = errors
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to the standardized API response dict."""
        response = {
            "code": self.status_code,
            "message": self.message,
            "detail": self.detail,
            "data": None,
        }
        if self.errors is not None:
            response["errors"] = self.errors
        return response

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"status_code={self.status_code}, "
            f"message='{self.message}', "
            f"detail='{self.detail}')"
        )
