"""
Teacher Repository – direct database access layer.

Responsibilities:
  - Execute all SQL queries via SQLAlchemy (CRUD + search + pagination).
  - Service calls Repository; Repository never calls Service.
  - Uses async SQLAlchemy session for non-blocking I/O.
"""

from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database import DatabaseIntegrityException, DatabaseQueryException
from app.modules.teacher.dto import TeacherQueryParams, TeacherUpdateRequest
from app.modules.teacher.entity import Teacher, TeacherStatus


class TeacherRepository:
    """
    Data-access class for the teachers table.
    All methods are async and require an injected AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def create(self, teacher: Teacher) -> Teacher:
        """
        Persist a new Teacher entity.
        Raises DatabaseIntegrityException on unique constraint violations.
        """
        try:
            self._session.add(teacher)
            await self._session.commit()
            await self._session.refresh(teacher)
            return teacher
        except IntegrityError as exc:
            await self._session.rollback()
            raise DatabaseIntegrityException(constraint=str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise DatabaseQueryException(
                operation="create_teacher", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # READ – single record
    # ------------------------------------------------------------------

    async def get_by_id(self, teacher_id: int) -> Optional[Teacher]:
        """Return an active teacher by PK, or None."""
        try:
            result = await self._session.execute(
                select(Teacher).where(
                    Teacher.id == teacher_id,
                    Teacher.is_active == True,
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_teacher_by_id", reason=str(exc)
            ) from exc

    async def get_by_teacher_code(self, teacher_code: str) -> Optional[Teacher]:
        """Return an active teacher by business code, or None."""
        try:
            result = await self._session.execute(
                select(Teacher).where(
                    Teacher.teacher_code == teacher_code,
                    Teacher.is_active == True,
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_teacher_by_code", reason=str(exc)
            ) from exc

    async def get_by_email(self, email: str) -> Optional[Teacher]:
        """Return an active teacher by email, or None. Used for uniqueness check."""
        try:
            result = await self._session.execute(
                select(Teacher).where(
                    Teacher.email == email,
                    Teacher.is_active == True,
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_teacher_by_email", reason=str(exc)
            ) from exc

    async def get_by_national_id(self, national_id: str) -> Optional[Teacher]:
        """Return a teacher by national ID regardless of active flag (uniqueness check)."""
        try:
            result = await self._session.execute(
                select(Teacher).where(Teacher.national_id == national_id)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_teacher_by_national_id", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # READ – list with filter + pagination
    # ------------------------------------------------------------------

    async def list_teachers(
        self, params: TeacherQueryParams
    ) -> Tuple[List[Teacher], int]:
        """
        Return (teachers_page, total_count) matching the query params.
        """
        try:
            base_query = select(Teacher).where(Teacher.is_active == True)

            # ── Filters ──────────────────────────────────────────────
            if params.search:
                term = f"%{params.search}%"
                base_query = base_query.where(
                    or_(
                        Teacher.teacher_code.ilike(term),
                        Teacher.full_name.ilike(term),
                        Teacher.email.ilike(term),
                    )
                )
            if params.employment_status:
                base_query = base_query.where(
                    Teacher.employment_status == params.employment_status
                )
            if params.department:
                base_query = base_query.where(
                    Teacher.department.ilike(f"%{params.department}%")
                )
            if params.specialization:
                base_query = base_query.where(
                    Teacher.specialization.ilike(f"%{params.specialization}%")
                )

            # ── Count total ──────────────────────────────────────────
            count_result = await self._session.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total = count_result.scalar_one()

            # ── Paginate ─────────────────────────────────────────────
            offset = (params.page - 1) * params.page_size
            paginated_query = (
                base_query
                .order_by(Teacher.teacher_code.asc())
                .offset(offset)
                .limit(params.page_size)
            )
            rows = await self._session.execute(paginated_query)
            teachers = list(rows.scalars().all())

            return teachers, total

        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="list_teachers", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    async def update(
        self, teacher: Teacher, data: TeacherUpdateRequest
    ) -> Teacher:
        """Apply partial update from DTO to entity (PATCH semantics)."""
        try:
            update_data = data.model_dump(exclude_none=True, exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(teacher, field):
                    setattr(teacher, field, value)

            await self._session.commit()
            await self._session.refresh(teacher)
            return teacher
        except IntegrityError as exc:
            await self._session.rollback()
            raise DatabaseIntegrityException(constraint=str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise DatabaseQueryException(
                operation="update_teacher", reason=str(exc)
            ) from exc

    async def update_status(
        self, teacher: Teacher, new_status: TeacherStatus
    ) -> Teacher:
        """Persist a status-only change on a teacher entity."""
        try:
            teacher.employment_status = new_status
            await self._session.commit()
            await self._session.refresh(teacher)
            return teacher
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise DatabaseQueryException(
                operation="update_teacher_status", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # DELETE (soft delete)
    # ------------------------------------------------------------------

    async def soft_delete(self, teacher: Teacher) -> Teacher:
        """Soft-delete: set is_active=False."""
        try:
            teacher.is_active = False
            await self._session.commit()
            await self._session.refresh(teacher)
            return teacher
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise DatabaseQueryException(
                operation="soft_delete_teacher", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # Existence helpers
    # ------------------------------------------------------------------

    async def exists_by_teacher_code(self, teacher_code: str) -> bool:
        """Check if a teacher_code already exists (including soft-deleted records)."""
        try:
            result = await self._session.execute(
                select(func.count(Teacher.id)).where(
                    Teacher.teacher_code == teacher_code
                )
            )
            return (result.scalar_one() or 0) > 0
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="check_teacher_code_exists", reason=str(exc)
            ) from exc
