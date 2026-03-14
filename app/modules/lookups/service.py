"""
Lookup Service - orchestrates read-only lookup queries.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lookups.dto import (
    ClassroomLookupItem,
    ClassroomLookupListResponse,
    StudentLookupItem,
    StudentLookupListResponse,
    SubjectLookupItem,
    SubjectLookupListResponse,
    TeacherLookupItem,
    TeacherLookupListResponse,
)
from app.modules.lookups.repository import LookupsRepository


class LookupsService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = LookupsRepository(session)

    async def list_teachers(
        self, search: Optional[str] = None
    ) -> TeacherLookupListResponse:
        rows = await self._repo.list_teachers(search)
        items = [
            TeacherLookupItem(
                id=row.id,
                teacher_code=row.teacher_code,
                full_name=row.full_name,
            )
            for row in rows
        ]
        return TeacherLookupListResponse(items=items)

    async def list_classrooms(
        self, search: Optional[str] = None
    ) -> ClassroomLookupListResponse:
        rows = await self._repo.list_classrooms(search)
        items = [
            ClassroomLookupItem(
                id=row.id,
                class_code=row.class_code,
                class_name=row.class_name,
                grade_level=row.grade_level,
                academic_year=row.academic_year,
            )
            for row in rows
        ]
        return ClassroomLookupListResponse(items=items)

    async def list_students(
        self, search: Optional[str] = None
    ) -> StudentLookupListResponse:
        rows = await self._repo.list_students(search)
        items = [
            StudentLookupItem(
                id=row.id,
                student_code=row.student_code,
                full_name=row.full_name,
                class_name=row.class_name,
            )
            for row in rows
        ]
        return StudentLookupListResponse(items=items)

    async def list_subjects(
        self, search: Optional[str] = None
    ) -> SubjectLookupListResponse:
        rows = await self._repo.list_subjects(search)
        items = [
            SubjectLookupItem(
                id=row.id,
                subject_code=row.subject_code,
                subject_name=row.subject_name,
            )
            for row in rows
        ]
        return SubjectLookupListResponse(items=items)
