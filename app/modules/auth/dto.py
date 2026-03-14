"""
Auth DTOs.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.modules.auth.entity import UserRole


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    token: str
    token_type: str = Field(default="refresh", description="access | refresh")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: UserRole
    user_id: int
    teacher_id: Optional[int] = None


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    role: UserRole
    teacher_id: Optional[int] = None


class UserUpdateRequest(BaseModel):
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    role: Optional[UserRole] = None
    teacher_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    teacher_id: Optional[int]
    is_active: bool
    last_login_at: Optional[datetime]

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
