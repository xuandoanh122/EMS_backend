"""
Auth controller.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import AuthContext, require_role, require_any_role
from app.core.response import APIResponse
from app.modules.auth.dto import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
    CreateTeacherAccountRequest,
    CreateTeacherAccountResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
)
from app.modules.auth.service import AuthService

router = APIRouter()


def get_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    return AuthService(session)


@router.post("/login", status_code=200, summary="Login")
async def login(
    data: LoginRequest,
    service: AuthService = Depends(get_service),
) -> APIResponse[TokenResponse]:
    result = await service.login(data.username, data.password)
    return APIResponse.success(data=result.model_dump(), detail="Login success")


@router.post("/refresh", status_code=200, summary="Refresh access token")
async def refresh(
    data: RefreshRequest,
    service: AuthService = Depends(get_service),
) -> APIResponse[TokenResponse]:
    result = await service.refresh(data)
    return APIResponse.success(data=result.model_dump(), detail="Token refreshed")


@router.post("/logout", status_code=200, summary="Logout")
async def logout(
    data: LogoutRequest,
    service: AuthService = Depends(get_service),
) -> APIResponse:
    await service.logout(data)
    return APIResponse.success(detail="Logged out")


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------

@router.post("/users", status_code=201, summary="Create user")
async def create_user(
    data: UserCreateRequest,
    _: AuthContext = Depends(require_role("admin")),
    service: AuthService = Depends(get_service),
) -> APIResponse[UserResponse]:
    result = await service.create_user(data)
    return APIResponse.created(data=result.model_dump(), detail="User created")


@router.get("/users", status_code=200, summary="List users")
async def list_users(
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: AuthContext = Depends(require_role("admin")),
    service: AuthService = Depends(get_service),
) -> APIResponse[UserListResponse]:
    result = await service.list_users(page, page_size, role, is_active)
    return APIResponse.success(data=result.model_dump(), detail="User list")


@router.get("/users/{user_id}", status_code=200, summary="Get user")
async def get_user(
    user_id: int,
    _: AuthContext = Depends(require_role("admin")),
    service: AuthService = Depends(get_service),
) -> APIResponse[UserResponse]:
    result = await service.get_user(user_id)
    return APIResponse.success(data=result.model_dump(), detail="User detail")


@router.patch("/users/{user_id}", status_code=200, summary="Update user")
async def update_user(
    user_id: int,
    data: UserUpdateRequest,
    _: AuthContext = Depends(require_role("admin")),
    service: AuthService = Depends(get_service),
) -> APIResponse[UserResponse]:
    result = await service.update_user(user_id, data)
    return APIResponse.success(data=result.model_dump(), detail="User updated")


# ---------------------------------------------------------------------------
# Teacher Account Creation (admin only)
# ----------------------------------------------------------------------------

@router.post(
    "/teachers/{teacher_id}/account", 
    status_code=201, 
    summary="Tạo tài khoản cho Giáo viên"
)
async def create_teacher_account(
    teacher_id: int,
    data: CreateTeacherAccountRequest,
    _: AuthContext = Depends(require_role("admin")),
    service: AuthService = Depends(get_service),
) -> APIResponse[CreateTeacherAccountResponse]:
    """
    Tạo tài khoản cho Giáo viên.
    
    - Tự động tạo username từ email
    - Tạo mật khẩu tạm thời ngẫu nhiên
    - Gửi email thông báo cho Giáo viên (nếu send_email=True)
    - Đánh dấu must_change_password = True để bắt buộc đổi mật khẩu
    """
    # Override teacher_id from path
    result = await service.create_teacher_account(teacher_id, data.send_email)
    return APIResponse.created(data=result, detail="Tài khoản Giáo viên đã được tạo")


# ---------------------------------------------------------------------------
# Change Password (auth required)
# ---------------------------------------------------------------------------

@router.post(
    "/forgot-password", 
    status_code=200, 
    summary="Quên mật khẩu - gửi email reset"
)
async def forgot_password(
    data: ForgotPasswordRequest,
    service: AuthService = Depends(get_service),
) -> APIResponse:
    """
    Yêu cầu đặt lại mật khẩu qua email.
    
    - Gửi email chứa link reset mật khẩu
    - Link có hiệu lực trong 30 phút
    - Luôn trả về thành công để tránh email enumeration
    """
    result = await service.forgot_password(data.email)
    return APIResponse.success(detail=result["message"])


@router.post(
    "/reset-password", 
    status_code=200, 
    summary="Đặt lại mật khẩu với token"
)
async def reset_password(
    data: ResetPasswordRequest,
    service: AuthService = Depends(get_service),
) -> APIResponse:
    """
    Đặt lại mật khẩu với token từ email.
    
    - Token có hiệu lực trong 30 phút
    - Mỗi token chỉ sử dụng được 1 lần
    - Mật khẩu mới phải có ít nhất 6 ký tự
    """
    result = await service.reset_password(data.token, data.new_password)
    return APIResponse.success(detail=result["message"])


@router.post(
    "/change-password", 
    status_code=200, 
    summary="Đổi mật khẩu (khi đã đăng nhập)"
)
async def change_password(
    data: ChangePasswordRequest,
    auth: AuthContext = Depends(require_any_role("admin", "teacher", "accountant")),
    service: AuthService = Depends(get_service),
) -> APIResponse:
    """
    Đổi mật khẩu khi đã đăng nhập.
    
    - Yêu cầu nhập mật khẩu cũ để xác thực
    - Mật khẩu mới phải có ít nhất 6 ký tự
    """
    result = await service.change_password(
        user_id=auth.user_id,
        old_password=data.old_password,
        new_password=data.new_password,
    )
    return APIResponse.success(detail=result["message"])


# ---------------------------------------------------------------------------
# User Account Management (admin only)
# ---------------------------------------------------------------------------

@router.delete(
    "/users/{user_id}", 
    status_code=200, 
    summary="Xóa vĩnh viễn tài khoản"
)
async def delete_user(
    user_id: int,
    auth: AuthContext = Depends(require_role("admin")),
    service: AuthService = Depends(get_service),
) -> APIResponse:
    """
    Xóa vĩnh viễn tài khoản người dùng (Hard Delete).
    
    - Chỉ Admin mới có quyền xóa
    - Không thể tự xóa chính mình
    - Dữ liệu sẽ bị xóa vĩnh viễn
    """
    # Không cho phép tự xóa
    if user_id == auth.user_id:
        return APIResponse.error(detail="Không thể tự xóa tài khoản của chính mình", status_code=400)
    
    result = await service.delete_user(user_id)
    return APIResponse.success(detail=result["message"])


@router.post(
    "/users/{user_id}/deactivate", 
    status_code=200, 
    summary="Vô hiệu hóa tài khoản"
)
async def deactivate_user(
    user_id: int,
    auth: AuthContext = Depends(require_role("admin")),
    service: AuthService = Depends(get_service),
) -> APIResponse:
    """
    Vô hiệu hóa tài khoản người dùng (Soft Delete).
    
    - User sẽ không thể đăng nhập
    - Dữ liệu vẫn được giữ nguyên
    - Có thể kích hoạt lại sau
    - Không thể tự vô hiệu hóa chính mình
    """
    # Không cho phép tự vô hiệu hóa
    if user_id == auth.user_id:
        return APIResponse.error(detail="Không thể tự vô hiệu hóa tài khoản của chính mình", status_code=400)
    
    result = await service.deactivate_user(user_id)
    return APIResponse.success(detail=result["message"], data=result)


@router.post(
    "/users/{user_id}/reactivate", 
    status_code=200, 
    summary="Kích hoạt lại tài khoản"
)
async def reactivate_user(
    user_id: int,
    _: AuthContext = Depends(require_role("admin")),
    service: AuthService = Depends(get_service),
) -> APIResponse:
    """
    Kích hoạt lại tài khoản người dùng đã bị vô hiệu hóa.
    
    - User sẽ có thể đăng nhập lại
    """
    result = await service.reactivate_user(user_id)
    return APIResponse.success(detail=result["message"], data=result)
