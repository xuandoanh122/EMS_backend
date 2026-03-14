"""
Auth service.
"""

from datetime import datetime, timedelta
from typing import Optional

from app.core.exceptions.auth import (
    AccountDisabledException,
    InvalidCredentialsException,
    TokenBlacklistedException,
    TokenInvalidException,
)
from app.core.exceptions.common import AlreadyExistsException, NotFoundException, ValidationException
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.modules.auth.dto import (
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.auth.entity import User, UserRole
from app.modules.auth.repository import AuthRepository


class AuthService:
    def __init__(self, session) -> None:
        self._repo = AuthRepository(session)

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await self._repo.get_user_by_username(username)
        if not user:
            raise InvalidCredentialsException()
        if not user.is_active:
            raise AccountDisabledException()
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

        token_data = {"sub": str(user.id), "role": user.role.value, "teacher_id": user.teacher_id}
        access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data=token_data, expires_delta=refresh_token_expires)

        await self._repo.update_last_login(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            role=user.role,
            user_id=user.id,
            teacher_id=user.teacher_id,
        )

    async def refresh(self, data: RefreshRequest) -> TokenResponse:
        payload = decode_token(data.refresh_token)
        token_type = payload.get("type")
        jti = payload.get("jti")
        if token_type != "refresh" or not jti:
            raise TokenInvalidException()

        if await self._repo.is_blacklisted(jti):
            raise TokenBlacklistedException()

        user_id_raw = payload.get("sub")
        role = payload.get("role")
        teacher_id = payload.get("teacher_id")
        if not user_id_raw or not role:
            raise TokenInvalidException()

        user = await self._repo.get_user_by_id(int(user_id_raw))
        if not user or not user.is_active:
            raise AccountDisabledException()

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

        token_data = {"sub": str(user.id), "role": user.role.value, "teacher_id": user.teacher_id}
        access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data=token_data, expires_delta=refresh_token_expires)

        # Rotate refresh token: blacklist old one
        exp_ts = payload.get("exp")
        if exp_ts:
            await self._repo.add_blacklist(
                jti=jti,
                token_type="refresh",
                expires_at=datetime.utcfromtimestamp(exp_ts),
            )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            role=user.role,
            user_id=user.id,
            teacher_id=user.teacher_id,
        )

    async def logout(self, data: LogoutRequest) -> None:
        payload = decode_token(data.token)
        token_type = payload.get("type")
        jti = payload.get("jti")
        if not jti:
            raise TokenInvalidException()

        exp_ts = payload.get("exp")
        if exp_ts is None:
            raise TokenInvalidException()

        if token_type not in ("access", "refresh"):
            raise TokenInvalidException()

        if data.token_type and data.token_type != token_type:
            raise TokenInvalidException()

        await self._repo.add_blacklist(
            jti=jti,
            token_type=token_type,
            expires_at=datetime.utcfromtimestamp(exp_ts),
        )

    async def create_user(self, data: UserCreateRequest) -> UserResponse:
        existing = await self._repo.get_user_by_username(data.username)
        if existing:
            raise AlreadyExistsException(resource="User", identifier=data.username)

        if data.role == UserRole.TEACHER:
            if not data.teacher_id:
                raise ValidationException(detail="teacher_id is required for teacher role")
            teacher = await self._repo.get_teacher_by_id(data.teacher_id)
            if not teacher:
                raise NotFoundException(resource="Teacher", identifier=str(data.teacher_id))

        user = User(
            username=data.username,
            password_hash=get_password_hash(data.password),
            role=data.role,
            teacher_id=data.teacher_id,
            is_active=True,
        )
        created = await self._repo.create_user(user)
        return UserResponse.model_validate(created)

    async def list_users(
        self,
        page: int,
        page_size: int,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> UserListResponse:
        users, total = await self._repo.list_users(page, page_size, role, is_active)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        return UserListResponse(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_user(self, user_id: int) -> UserResponse:
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: int, data: UserUpdateRequest) -> UserResponse:
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", identifier=str(user_id))

        update_data = data.model_dump(exclude_none=True)
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))

        if "role" in update_data and update_data["role"] == UserRole.TEACHER:
            teacher_id = update_data.get("teacher_id") or user.teacher_id
            if not teacher_id:
                raise ValidationException(detail="teacher_id is required for teacher role")
            teacher = await self._repo.get_teacher_by_id(teacher_id)
            if not teacher:
                raise NotFoundException(resource="Teacher", identifier=str(teacher_id))

        updated = await self._repo.update_user(user, update_data)
        return UserResponse.model_validate(updated)
