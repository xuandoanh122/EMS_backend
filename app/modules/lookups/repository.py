"""
Lookup Repository - read-only queries for lightweight selectors.
"""

from typing import Optional, Sequence, Tuple

from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database import DatabaseQueryException
from app.modules.classroom.entity import Classroom
from app.modules.grading.entity import Subject
from app.modules.student.entity import Student
from app.modules.teacher.entity import Teacher


class LookupsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list_teachers(
        self, search: Optional[str] = None
    ) -> Sequence[Tuple[int, str, str]]:
        try:
            q = select(Teacher.id, Teacher.teacher_code, Teacher.full_name).where(
                Teacher.is_active == True
            )
            if search:
                term = f"%{search}%"
                q = q.where(
                    or_(
                        Teacher.teacher_code.ilike(term),
                        Teacher.full_name.ilike(term),
                    )
                )
            q = q.order_by(Teacher.teacher_code.asc())
            rows = await self._s.execute(q)
            return rows.all()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="lookup_teachers", reason=str(exc)
            ) from exc

    async def list_classrooms(
        self, search: Optional[str] = None
    ) -> Sequence[Tuple[int, str, str, int, str]]:
        try:
            q = select(
                Classroom.id,
                Classroom.class_code,
                Classroom.class_name,
                Classroom.grade_level,
                Classroom.academic_year,
            ).where(Classroom.is_active == True)
            if search:
                term = f"%{search}%"
                q = q.where(
                    or_(
                        Classroom.class_code.ilike(term),
                        Classroom.class_name.ilike(term),
                    )
                )
            q = q.order_by(Classroom.academic_year.desc(), Classroom.class_code.asc())
            rows = await self._s.execute(q)
            return rows.all()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="lookup_classrooms", reason=str(exc)
            ) from exc

    async def list_students(
        self, search: Optional[str] = None
    ) -> Sequence[Tuple[int, str, str, Optional[str]]]:
        try:
            q = select(
                Student.id,
                Student.student_code,
                Student.full_name,
                Student.class_name,
            ).where(Student.is_active == True)
            if search:
                term = f"%{search}%"
                q = q.where(
                    or_(
                        Student.student_code.ilike(term),
                        Student.full_name.ilike(term),
                    )
                )
            q = q.order_by(Student.student_code.asc())
            rows = await self._s.execute(q)
            return rows.all()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="lookup_students", reason=str(exc)
            ) from exc

    async def list_subjects(
        self, search: Optional[str] = None
    ) -> Sequence[Tuple[int, str, str]]:
        try:
            q = select(
                Subject.id,
                Subject.subject_code,
                Subject.subject_name,
            ).where(Subject.is_active == True)
            if search:
                term = f"%{search}%"
                q = q.where(
                    or_(
                        Subject.subject_code.ilike(term),
                        Subject.subject_name.ilike(term),
                    )
                )
            q = q.order_by(Subject.subject_code.asc())
            rows = await self._s.execute(q)
            return rows.all()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="lookup_subjects", reason=str(exc)
            ) from exc
