"""
Auth dependencies.
"""

from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions.auth import AccountDisabledException, InsufficientRoleException, TokenBlacklistedException, TokenInvalidException
from app.core.security import decode_token
from app.modules.auth.repository import AuthRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthContext:
    def __init__(self, user_id: int, role: str, teacher_id: Optional[int]) -> None:
        self.user_id = user_id
        self.role = role
        self.teacher_id = teacher_id


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> AuthContext:
    payload = decode_token(token)
    user_id_raw = payload.get("sub")
    role = payload.get("role")
    teacher_id = payload.get("teacher_id")
    token_type = payload.get("type")
    jti = payload.get("jti")

    if not user_id_raw or not role or token_type != "access" or not jti:
        raise TokenInvalidException()

    repo = AuthRepository(session)
    if await repo.is_blacklisted(jti):
        raise TokenBlacklistedException()

    try:
        user_id = int(user_id_raw)
    except ValueError as exc:
        raise TokenInvalidException() from exc

    user = await repo.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise AccountDisabledException()

    return AuthContext(user_id=user.id, role=user.role.value, teacher_id=user.teacher_id)


def require_role(required_role: str):
    async def _checker(user: AuthContext = Depends(get_current_user)) -> AuthContext:
        if user.role != required_role:
            raise InsufficientRoleException(required_role=required_role, current_role=user.role)
        return user

    return _checker


def require_any_role(*required_roles: str):
    required_set = {role for role in required_roles if role}

    async def _checker(user: AuthContext = Depends(get_current_user)) -> AuthContext:
        if user.role not in required_set:
            required_display = "|".join(sorted(required_set)) if required_set else ""
            raise InsufficientRoleException(required_role=required_display, current_role=user.role)
        return user

    return _checker
