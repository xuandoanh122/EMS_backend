"""
Student Repository – direct database access layer.

Responsibilities:
  - Execute all SQL queries via SQLAlchemy (CRUD + search + pagination).
  - Service calls Repository; Repository never calls Service.
  - Uses async SQLAlchemy session for non-blocking I/O.
  - Avoids N+1 query problems (uses single query with filters).
"""

from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database import DatabaseIntegrityException, DatabaseQueryException
from app.modules.student.dto import StudentQueryParams, StudentUpdateRequest
from app.modules.student.entity import Student, StudentStatus


class StudentRepository:
    """
    Data-access class for the students table.
    All methods are async and require an injected AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def create(self, student: Student) -> Student:
        """
        Persist a new Student entity.
        Raises DatabaseIntegrityException on unique constraint violations
        (duplicate student_code, email, national_id).
        """
        try:
            self._session.add(student)
            await self._session.commit()
            await self._session.refresh(student)
            return student
        except IntegrityError as exc:
            await self._session.rollback()
            raise DatabaseIntegrityException(
                constraint=str(exc.orig)
            ) from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise DatabaseQueryException(
                operation="create_student", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # READ – single record
    # ------------------------------------------------------------------

    async def get_by_id(self, student_id: int) -> Optional[Student]:
        """Return an active student by internal PK, or None."""
        try:
            result = await self._session.execute(
                select(Student).where(
                    Student.id == student_id,
                    Student.is_active.is_(True),
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_student_by_id", reason=str(exc)
            ) from exc

    async def get_by_student_code(self, student_code: str) -> Optional[Student]:
        """Return an active student by business code, or None."""
        try:
            result = await self._session.execute(
                select(Student).where(
                    Student.student_code == student_code,
                    Student.is_active.is_(True),
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_student_by_code", reason=str(exc)
            ) from exc

    async def get_by_email(self, email: str) -> Optional[Student]:
        """Return an active student by email, or None. Used for uniqueness check."""
        try:
            result = await self._session.execute(
                select(Student).where(
                    Student.email == email,
                    Student.is_active.is_(True),
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_student_by_email", reason=str(exc)
            ) from exc

    async def get_by_national_id(self, national_id: str) -> Optional[Student]:
        """Return a student by national ID regardless of active flag (for uniqueness check)."""
        try:
            result = await self._session.execute(
                select(Student).where(Student.national_id == national_id)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_student_by_national_id", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # READ – list with filter + pagination
    # ------------------------------------------------------------------

    async def list_students(
        self, params: StudentQueryParams
    ) -> Tuple[List[Student], int]:
        """
        Return (students_page, total_count) matching the query params.
        Avoids N+1 by fetching both count and rows in a single filter build.
        """
        try:
            base_query = select(Student).where(Student.is_active.is_(True))

            # ── Filters ──────────────────────────────────────────────
            if params.search:
                term = f"%{params.search}%"
                base_query = base_query.where(
                    or_(
                        Student.student_code.ilike(term),
                        Student.full_name.ilike(term),
                        Student.email.ilike(term),
                    )
                )
            if params.academic_status:
                base_query = base_query.where(
                    Student.academic_status == params.academic_status
                )
            if params.class_name:
                base_query = base_query.where(
                    Student.class_name.ilike(f"%{params.class_name}%")
                )
            if params.program_name:
                base_query = base_query.where(
                    Student.program_name.ilike(f"%{params.program_name}%")
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
                .order_by(Student.student_code.asc())
                .offset(offset)
                .limit(params.page_size)
            )
            rows = await self._session.execute(paginated_query)
            students = list(rows.scalars().all())

            return students, total

        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="list_students", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    async def update(
        self, student: Student, data: StudentUpdateRequest
    ) -> Student:
        """
        Apply partial update from DTO to entity.
        Only fields that are not None in `data` will be written.
        """
        try:
            update_data = data.model_dump(exclude_none=True, exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(student, field):
                    setattr(student, field, value)

            await self._session.commit()
            await self._session.refresh(student)
            return student
        except IntegrityError as exc:
            await self._session.rollback()
            raise DatabaseIntegrityException(
                constraint=str(exc.orig)
            ) from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise DatabaseQueryException(
                operation="update_student", reason=str(exc)
            ) from exc

    async def update_status(
        self, student: Student, new_status: StudentStatus
    ) -> Student:
        """Persist a status-only change on a student entity."""
        try:
            student.academic_status = new_status
            await self._session.commit()
            await self._session.refresh(student)
            return student
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise DatabaseQueryException(
                operation="update_student_status", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # DELETE (soft delete)
    # ------------------------------------------------------------------

    async def soft_delete(self, student: Student) -> Student:
        """
        Soft-delete: set is_active=False instead of removing the row.
        Preserves audit trail and historical data.
        """
        try:
            student.is_active = False
            await self._session.commit()
            await self._session.refresh(student)
            return student
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise DatabaseQueryException(
                operation="soft_delete_student", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # Existence helpers
    # ------------------------------------------------------------------

    async def exists_by_student_code(self, student_code: str) -> bool:
        """Check if a student_code already exists (including soft-deleted records)."""
        try:
            result = await self._session.execute(
                select(func.count(Student.id)).where(
                    Student.student_code == student_code
                )
            )
            return (result.scalar_one() or 0) > 0
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="check_student_code_exists", reason=str(exc)
            ) from exc
