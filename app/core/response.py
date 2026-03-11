"""
Standardized API response model for the EMS system.
All API endpoints return responses in this format, ensuring consistency
for the Front-end to parse data easily.

Response format (from README):
{
    "code": 200,               // HTTP Status Code or Custom Business Code
    "message": "Success",      // Short user-friendly message
    "detail": "...",           // Detailed description for developers
    "data": { ... }            // Actual payload (only on success)
}
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API response wrapper used by all endpoints.

    Attributes:
        code: HTTP status code or custom business code.
        message: Short, user-friendly message.
        detail: Detailed description for developer debugging.
        data: The actual response payload (None on error responses).
    """

    code: int = Field(default=200, description="HTTP status code or custom business code")
    message: str = Field(default="Success", description="Short user-friendly message")
    detail: str = Field(default="", description="Detailed description for developers")
    data: Optional[T] = Field(default=None, description="Response payload")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "Success",
                "detail": "Retrieved student list successfully",
                "data": {},
            }
        }

    @classmethod
    def success(
        cls,
        data: Any = None,
        message: str = "Success",
        detail: str = "",
        code: int = 200,
    ) -> "APIResponse":
        """Create a successful response."""
        return cls(code=code, message=message, detail=detail, data=data)

    @classmethod
    def created(
        cls,
        data: Any = None,
        message: str = "Created",
        detail: str = "",
    ) -> "APIResponse":
        """Create a 201 Created response."""
        return cls(code=201, message=message, detail=detail, data=data)

    @classmethod
    def error(
        cls,
        code: int = 500,
        message: str = "Internal Server Error",
        detail: str = "An unexpected error occurred",
    ) -> "APIResponse":
        """Create an error response (data is always None)."""
        return cls(code=code, message=message, detail=detail, data=None)
