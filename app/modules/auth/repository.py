"""
Auth repository.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database import DatabaseQueryException
from app.modules.auth.entity import TokenBlacklist, User
from app.modules.teacher.entity import Teacher


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_user_by_username(self, username: str) -> Optional[User]:
        try:
            result = await self._s.execute(
                select(User).where(User.username == username)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_user_by_username", reason=str(exc)) from exc

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        try:
            result = await self._s.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_user_by_id", reason=str(exc)) from exc

    async def list_users(
        self,
        page: int,
        page_size: int,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        try:
            q = select(User)
            if role:
                q = q.where(User.role == role)
            if is_active is not None:
                q = q.where(User.is_active == is_active)
            count_result = await self._s.execute(select(func.count()).select_from(q.subquery()))
            total = count_result.scalar_one()
            offset = (page - 1) * page_size
            rows = await self._s.execute(
                q.order_by(User.id.asc()).offset(offset).limit(page_size)
            )
            return list(rows.scalars().all()), total
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_users", reason=str(exc)) from exc

    async def create_user(self, user: User) -> User:
        try:
            self._s.add(user)
            await self._s.commit()
            await self._s.refresh(user)
            return user
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="create_user", reason=str(exc)) from exc

    async def update_user(self, user: User, data: dict) -> User:
        try:
            for field, value in data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            await self._s.commit()
            await self._s.refresh(user)
            return user
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="update_user", reason=str(exc)) from exc

    async def update_last_login(self, user: User) -> None:
        try:
            user.last_login_at = datetime.utcnow()
            await self._s.commit()
            await self._s.refresh(user)
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="update_last_login", reason=str(exc)) from exc

    async def get_teacher_by_id(self, teacher_id: int) -> Optional[Teacher]:
        try:
            result = await self._s.execute(
                select(Teacher).where(Teacher.id == teacher_id)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_teacher_by_id", reason=str(exc)) from exc

    async def add_blacklist(self, jti: str, token_type: str, expires_at: datetime) -> None:
        try:
            obj = TokenBlacklist(jti=jti, token_type=token_type, expires_at=expires_at)
            self._s.add(obj)
            await self._s.commit()
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="add_blacklist", reason=str(exc)) from exc

    async def is_blacklisted(self, jti: str) -> bool:
        try:
            result = await self._s.execute(
                select(TokenBlacklist.id).where(TokenBlacklist.jti == jti)
            )
            return result.scalar() is not None
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="is_blacklisted", reason=str(exc)) from exc
