"""
Classroom Repository – database access layer.
"""

from typing import List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database import DatabaseIntegrityException, DatabaseQueryException
from app.modules.classroom.dto import (
    ClassroomQueryParams,
    ClassroomUpdateRequest,
    EnrollmentUpdateRequest,
)
from app.modules.classroom.entity import (
    Classroom,
    EnrollmentStatus,
    EnrollmentType,
    StudentClassEnrollment,
)


class ClassroomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ------------------------------------------------------------------
    # Classroom CRUD
    # ------------------------------------------------------------------

    async def create_classroom(self, obj: Classroom) -> Classroom:
        try:
            self._s.add(obj)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except IntegrityError as exc:
            await self._s.rollback()
            raise DatabaseIntegrityException(constraint=str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="create_classroom", reason=str(exc)) from exc

    async def get_classroom_by_id(self, classroom_id: int) -> Optional[Classroom]:
        try:
            result = await self._s.execute(
                select(Classroom).where(Classroom.id == classroom_id, Classroom.is_active == True)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_classroom_by_id", reason=str(exc)) from exc

    async def get_classroom_by_code(self, class_code: str) -> Optional[Classroom]:
        try:
            result = await self._s.execute(
                select(Classroom).where(Classroom.class_code == class_code, Classroom.is_active == True)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_classroom_by_code", reason=str(exc)) from exc

    async def get_classroom_by_code_any(self, class_code: str) -> Optional[Classroom]:
        """Get classroom by code regardless of active flag (used for status toggle)."""
        try:
            result = await self._s.execute(
                select(Classroom).where(Classroom.class_code == class_code)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_classroom_by_code_any", reason=str(exc)
            ) from exc

    async def list_classrooms(
        self, params: ClassroomQueryParams
    ) -> Tuple[List[Tuple[Classroom, int]], int]:
        """
        Trả về list of (Classroom, current_enrollment_count) để tránh lazy-load
        @property trong async context.
        """
        try:
            # Subquery đếm số enrollment đang active theo classroom_id
            enroll_count_sq = (
                select(
                    StudentClassEnrollment.classroom_id,
                    func.count(StudentClassEnrollment.id).label("cnt"),
                )
                .where(
                    StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
                    StudentClassEnrollment.is_active == True,
                )
                .group_by(StudentClassEnrollment.classroom_id)
                .subquery()
            )

            q_base = select(Classroom).where(Classroom.is_active == True)
            if params.search:
                term = f"%{params.search}%"
                q_base = q_base.where(
                    or_(Classroom.class_code.ilike(term), Classroom.class_name.ilike(term))
                )
            if params.class_type:
                q_base = q_base.where(Classroom.class_type == params.class_type)
            if params.academic_year:
                q_base = q_base.where(Classroom.academic_year == params.academic_year)
            if params.grade_level:
                q_base = q_base.where(Classroom.grade_level == params.grade_level)
            if params.homeroom_teacher_id:
                q_base = q_base.where(Classroom.homeroom_teacher_id == params.homeroom_teacher_id)

            count_result = await self._s.execute(
                select(func.count()).select_from(q_base.subquery())
            )
            total = count_result.scalar_one()

            offset = (params.page - 1) * params.page_size
            q_paged = (
                select(Classroom, func.coalesce(enroll_count_sq.c.cnt, 0).label("enrollment_count"))
                .outerjoin(enroll_count_sq, Classroom.id == enroll_count_sq.c.classroom_id)
                .where(Classroom.is_active == True)
            )
            if params.search:
                term = f"%{params.search}%"
                q_paged = q_paged.where(
                    or_(Classroom.class_code.ilike(term), Classroom.class_name.ilike(term))
                )
            if params.class_type:
                q_paged = q_paged.where(Classroom.class_type == params.class_type)
            if params.academic_year:
                q_paged = q_paged.where(Classroom.academic_year == params.academic_year)
            if params.grade_level:
                q_paged = q_paged.where(Classroom.grade_level == params.grade_level)
            if params.homeroom_teacher_id:
                q_paged = q_paged.where(Classroom.homeroom_teacher_id == params.homeroom_teacher_id)
            # Filter has_capacity: lớp chưa đầy (enrollment < max_capacity)
            if params.has_capacity is True:
                q_paged = q_paged.where(
                    func.coalesce(enroll_count_sq.c.cnt, 0) < Classroom.max_capacity
                )
            elif params.has_capacity is False:
                q_paged = q_paged.where(
                    func.coalesce(enroll_count_sq.c.cnt, 0) >= Classroom.max_capacity
                )

            rows = await self._s.execute(
                q_paged.order_by(Classroom.academic_year.desc(), Classroom.class_code.asc())
                       .offset(offset).limit(params.page_size)
            )
            return [(row.Classroom, row.enrollment_count) for row in rows], total
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_classrooms", reason=str(exc)) from exc

    async def update_classroom(self, obj: Classroom, data: ClassroomUpdateRequest) -> Classroom:
        try:
            update_data = data.model_dump(exclude_none=True, exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(obj, field):
                    setattr(obj, field, value)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except IntegrityError as exc:
            await self._s.rollback()
            raise DatabaseIntegrityException(constraint=str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="update_classroom", reason=str(exc)) from exc

    async def soft_delete_classroom(self, obj: Classroom) -> Classroom:
        try:
            obj.is_active = False
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="soft_delete_classroom", reason=str(exc)) from exc

    async def update_classroom_status(self, obj: Classroom, is_active: bool) -> Classroom:
        """Toggle classroom active flag."""
        try:
            obj.is_active = is_active
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(
                operation="update_classroom_status", reason=str(exc)
            ) from exc

    async def exists_by_code(self, class_code: str) -> bool:
        try:
            result = await self._s.execute(
                select(func.count(Classroom.id)).where(Classroom.class_code == class_code)
            )
            return (result.scalar_one() or 0) > 0
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="exists_classroom_by_code", reason=str(exc)) from exc

    # ------------------------------------------------------------------
    # StudentClassEnrollment CRUD
    # ------------------------------------------------------------------

    async def create_enrollment(self, obj: StudentClassEnrollment) -> StudentClassEnrollment:
        try:
            self._s.add(obj)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except IntegrityError as exc:
            await self._s.rollback()
            raise DatabaseIntegrityException(constraint=str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="create_enrollment", reason=str(exc)) from exc

    async def get_enrollment_by_id(self, enrollment_id: int) -> Optional[StudentClassEnrollment]:
        try:
            result = await self._s.execute(
                select(StudentClassEnrollment).where(
                    StudentClassEnrollment.id == enrollment_id,
                    StudentClassEnrollment.is_active == True,
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_enrollment_by_id", reason=str(exc)) from exc

    async def get_enrollment(
        self,
        student_id: int,
        classroom_id: int,
        enrollment_type: EnrollmentType,
    ) -> Optional[StudentClassEnrollment]:
        """Get specific enrollment (for duplicate check)."""
        try:
            result = await self._s.execute(
                select(StudentClassEnrollment).where(
                    StudentClassEnrollment.student_id == student_id,
                    StudentClassEnrollment.classroom_id == classroom_id,
                    StudentClassEnrollment.enrollment_type == enrollment_type,
                    StudentClassEnrollment.is_active == True,
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_enrollment", reason=str(exc)) from exc

    async def get_active_primary_enrollment(self, student_id: int) -> Optional[StudentClassEnrollment]:
        """Check if student already has an active PRIMARY enrollment."""
        try:
            result = await self._s.execute(
                select(StudentClassEnrollment).where(
                    StudentClassEnrollment.student_id == student_id,
                    StudentClassEnrollment.enrollment_type == EnrollmentType.PRIMARY,
                    StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
                    StudentClassEnrollment.is_active == True,
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_active_primary_enrollment", reason=str(exc)
            ) from exc

    async def list_enrollments_by_classroom(
        self,
        classroom_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[StudentClassEnrollment], int]:
        try:
            q = select(StudentClassEnrollment).where(
                StudentClassEnrollment.classroom_id == classroom_id,
                StudentClassEnrollment.is_active == True,
            )
            count_result = await self._s.execute(select(func.count()).select_from(q.subquery()))
            total = count_result.scalar_one()
            offset = (page - 1) * page_size
            rows = await self._s.execute(
                q.order_by(StudentClassEnrollment.id.asc()).offset(offset).limit(page_size)
            )
            return list(rows.scalars().all()), total
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="list_enrollments_by_classroom", reason=str(exc)
            ) from exc

    async def list_enrollments_by_student(
        self,
        student_id: int,
    ) -> List[StudentClassEnrollment]:
        try:
            result = await self._s.execute(
                select(StudentClassEnrollment).where(
                    StudentClassEnrollment.student_id == student_id,
                    StudentClassEnrollment.is_active == True,
                )
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="list_enrollments_by_student", reason=str(exc)
            ) from exc

    async def update_enrollment(
        self,
        obj: StudentClassEnrollment,
        data: EnrollmentUpdateRequest,
    ) -> StudentClassEnrollment:
        try:
            update_data = data.model_dump(exclude_none=True, exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(obj, field):
                    setattr(obj, field, value)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="update_enrollment", reason=str(exc)) from exc

    async def update_enrollment_status(
        self,
        obj: StudentClassEnrollment,
        new_status: EnrollmentStatus,
        left_date=None,
        notes: Optional[str] = None,
    ) -> StudentClassEnrollment:
        try:
            obj.status = new_status
            if left_date:
                obj.left_date = left_date
            if notes:
                obj.notes = notes
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(
                operation="update_enrollment_status", reason=str(exc)
            ) from exc

    async def count_active_enrollments(self, classroom_id: int) -> int:
        """Count current active enrollments in a classroom."""
        try:
            result = await self._s.execute(
                select(func.count(StudentClassEnrollment.id)).where(
                    StudentClassEnrollment.classroom_id == classroom_id,
                    StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
                    StudentClassEnrollment.is_active == True,
                )
            )
            return result.scalar_one() or 0
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="count_active_enrollments", reason=str(exc)
            ) from exc
