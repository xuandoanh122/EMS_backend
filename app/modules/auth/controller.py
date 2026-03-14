"""
Auth controller.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import AuthContext, require_role
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
