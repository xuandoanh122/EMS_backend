"""
Student Repository – direct database access layer.

Responsibilities:
  - Execute all SQL queries via SQLAlchemy (CRUD + search + pagination).
  - Service calls Repository; Repository never calls Service.
  - Uses async SQLAlchemy session for non-blocking I/O.
  - Avoids N+1 query problems (uses single query with filters).
"""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, exists, func, not_, or_, select, text
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
    # AUTO-GENERATE STUDENT CODE
    # ------------------------------------------------------------------

    async def generate_student_code(self, yymm: str) -> str:
        """
        Sinh mã học sinh theo format Stud + YYMM + xxx (3 chữ số, zero-padded).
        VD: Stud2603001 = HS thứ 1 trong tháng 03/2026.
        Query MAX hiện có trong tháng để tính số thứ tự tiếp theo.
        """
        try:
            prefix = f"Stud{yymm}"
            result = await self._session.execute(
                select(func.max(Student.student_code)).where(
                    Student.student_code.like(f"{prefix}%")
                )
            )
            max_code = result.scalar_one_or_none()
            if max_code:
                # Lấy 3 chữ số cuối và tăng lên 1
                try:
                    seq = int(max_code[-3:]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
            return f"{prefix}{seq:03d}"
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="generate_student_code", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def create(self, student: Student) -> Student:
        """
        Persist a new Student entity.
        Raises DatabaseIntegrityException on unique constraint violations
        (duplicate student_code, email, national_id).
        NOTE: Caller is responsible for flushing/committing within a transaction.
        """
        try:
            self._session.add(student)
            await self._session.flush()   # flush để lấy id, KHÔNG commit
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

    async def commit(self) -> None:
        """Explicit commit – dùng sau khi create() và enroll trong transaction."""
        try:
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise DatabaseQueryException(operation="commit", reason=str(exc)) from exc

    # ------------------------------------------------------------------
    # READ – single record
    # ------------------------------------------------------------------

    async def get_by_id(self, student_id: int) -> Optional[Student]:
        """Return an active student by internal PK, or None."""
        try:
            result = await self._session.execute(
                select(Student).where(
                    Student.id == student_id,
                    Student.is_active == True,
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
                    Student.is_active == True,
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
                    Student.is_active == True,
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
        Supports has_enrollment and classroom_id filters.
        """
        try:
            # Import here to avoid circular import
            from app.modules.classroom.entity import StudentClassEnrollment, EnrollmentStatus

            base_query = select(Student).where(Student.is_active == True)

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

            # Filter: has_enrollment
            if params.has_enrollment is not None:
                active_enrollment_subq = (
                    select(StudentClassEnrollment.student_id)
                    .where(
                        StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
                        StudentClassEnrollment.is_active == True,
                    )
                    .scalar_subquery()
                )
                if params.has_enrollment:
                    base_query = base_query.where(
                        Student.id.in_(active_enrollment_subq)
                    )
                else:
                    base_query = base_query.where(
                        Student.id.not_in(active_enrollment_subq)
                    )

            # Filter: classroom_id
            if params.classroom_id is not None:
                classroom_student_subq = (
                    select(StudentClassEnrollment.student_id)
                    .where(
                        StudentClassEnrollment.classroom_id == params.classroom_id,
                        StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
                        StudentClassEnrollment.is_active == True,
                    )
                    .scalar_subquery()
                )
                base_query = base_query.where(
                    Student.id.in_(classroom_student_subq)
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
    # READ – enrollments for a student (for detail response)
    # ------------------------------------------------------------------

    async def get_enrollments_for_student(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Lấy danh sách enrollment active của học sinh, kèm thông tin lớp học.
        Dùng cho GET /students/{student_code} – bổ sung current_enrollments.
        """
        try:
            from app.modules.classroom.entity import (
                Classroom,
                StudentClassEnrollment,
                EnrollmentStatus,
            )

            result = await self._session.execute(
                select(
                    StudentClassEnrollment.id.label("enrollment_id"),
                    StudentClassEnrollment.classroom_id,
                    StudentClassEnrollment.enrollment_type,
                    StudentClassEnrollment.status.label("enrollment_status"),
                    StudentClassEnrollment.enrolled_date,
                    Classroom.class_code,
                    Classroom.class_name,
                )
                .join(Classroom, Classroom.id == StudentClassEnrollment.classroom_id)
                .where(
                    StudentClassEnrollment.student_id == student_id,
                    StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
                    StudentClassEnrollment.is_active == True,
                    Classroom.is_active == True,
                )
                .order_by(StudentClassEnrollment.enrolled_date.asc())
            )
            rows = result.fetchall()
            return [
                {
                    "enrollment_id": r.enrollment_id,
                    "classroom_id": r.classroom_id,
                    "class_code": r.class_code,
                    "class_name": r.class_name,
                    "enrollment_type": r.enrollment_type.value
                    if hasattr(r.enrollment_type, "value")
                    else str(r.enrollment_type),
                    "enrollment_status": r.enrollment_status.value
                    if hasattr(r.enrollment_status, "value")
                    else str(r.enrollment_status),
                    "enrolled_date": r.enrolled_date,
                }
                for r in rows
            ]
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_enrollments_for_student", reason=str(exc)
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
