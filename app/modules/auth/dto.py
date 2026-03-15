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


# -------------------------------------------------------------------------
# Teacher Account Creation DTOs
# -------------------------------------------------------------------------

class CreateTeacherAccountRequest(BaseModel):
    """Yêu cầu tạo tài khoản cho Giáo viên."""
    
    send_email: bool = Field(default=True, description="Có gửi email thông báo không")


class CreateTeacherAccountResponse(BaseModel):
    """Response sau khi tạo tài khoản Giáo viên."""
    
    user_id: int
    teacher_id: int
    teacher_code: str
    teacher_name: str
    email: str
    username: str
    temp_password: str
    email_sent: bool
    must_change_password: bool = True
    
    model_config = {"from_attributes": True}


# -------------------------------------------------------------------------
# Password Reset DTOs
# -------------------------------------------------------------------------

class ForgotPasswordRequest(BaseModel):
    """Yêu cầu quên mật khẩu - gửi email reset."""
    
    email: str = Field(..., description="Email của tài khoản cần khôi phục")


class ForgotPasswordResponse(BaseModel):
    """Response sau khi yêu cầu quên mật khẩu."""
    
    email: str
    email_sent: bool
    message: str


class ResetPasswordRequest(BaseModel):
    """Yêu cầu đặt lại mật khẩu với token."""
    
    token: str = Field(..., description="Token reset từ email")
    new_password: str = Field(..., min_length=6, max_length=128, description="Mật khẩu mới")


class ResetPasswordResponse(BaseModel):
    """Response sau khi đặt lại mật khẩu."""
    
    success: bool
    message: str


class ChangePasswordRequest(BaseModel):
    """Yêu cầu đổi mật khẩu (khi đã đăng nhập)."""
    
    old_password: str = Field(..., description="Mật khẩu cũ")
    new_password: str = Field(..., min_length=6, max_length=128, description="Mật khẩu mới")
