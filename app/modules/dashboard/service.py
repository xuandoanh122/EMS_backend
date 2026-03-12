"""
Dashboard Service – aggregates stats from multiple modules.

Queries run concurrently with asyncio.gather for minimal latency.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.student.entity import Student, StudentStatus
from app.modules.teacher.entity import Teacher, TeacherStatus
from app.modules.classroom.entity import Classroom


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def get_stats(self) -> Dict[str, Any]:
        """
        Collect all dashboard stats concurrently.

        Returns:
            {
                total_students: int,
                total_teachers: int,
                total_classrooms: int,
                active_students: int,
                active_teachers: int,
                recent_students: [...],   # 5 newest
                recent_teachers: [...],   # 5 newest
            }
        """
        (
            total_students,
            total_teachers,
            total_classrooms,
            active_students,
            active_teachers,
            recent_students,
            recent_teachers,
        ) = await asyncio.gather(
            self._count_students(),
            self._count_teachers(),
            self._count_classrooms(),
            self._count_active_students(),
            self._count_active_teachers(),
            self._recent_students(limit=5),
            self._recent_teachers(limit=5),
        )

        return {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_classrooms": total_classrooms,
            "active_students": active_students,
            "active_teachers": active_teachers,
            "recent_students": recent_students,
            "recent_teachers": recent_teachers,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _count_students(self) -> int:
        result = await self._session.execute(
            select(func.count(Student.id)).where(Student.is_active == True)
        )
        return result.scalar_one() or 0

    async def _count_teachers(self) -> int:
        result = await self._session.execute(
            select(func.count(Teacher.id)).where(Teacher.is_active == True)
        )
        return result.scalar_one() or 0

    async def _count_classrooms(self) -> int:
        result = await self._session.execute(
            select(func.count(Classroom.id)).where(Classroom.is_active == True)
        )
        return result.scalar_one() or 0

    async def _count_active_students(self) -> int:
        result = await self._session.execute(
            select(func.count(Student.id)).where(
                Student.is_active == True,
                Student.academic_status == StudentStatus.ACTIVE,
            )
        )
        return result.scalar_one() or 0

    async def _count_active_teachers(self) -> int:
        result = await self._session.execute(
            select(func.count(Teacher.id)).where(
                Teacher.is_active == True,
                Teacher.employment_status == TeacherStatus.ACTIVE,
            )
        )
        return result.scalar_one() or 0

    async def _recent_students(self, limit: int = 5) -> List[Dict[str, Any]]:
        result = await self._session.execute(
            select(
                Student.id,
                Student.student_code,
                Student.full_name,
                Student.academic_status,
                Student.class_name,
                Student.enrollment_date,
                Student.created_at,
            )
            .where(Student.is_active == True)
            .order_by(Student.created_at.desc())
            .limit(limit)
        )
        rows = result.fetchall()
        return [
            {
                "id": r.id,
                "student_code": r.student_code,
                "full_name": r.full_name,
                "academic_status": r.academic_status.value if r.academic_status else None,
                "class_name": r.class_name,
                "enrollment_date": r.enrollment_date.isoformat() if r.enrollment_date else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    async def _recent_teachers(self, limit: int = 5) -> List[Dict[str, Any]]:
        result = await self._session.execute(
            select(
                Teacher.id,
                Teacher.teacher_code,
                Teacher.full_name,
                Teacher.employment_status,
                Teacher.department,
                Teacher.specialization,
                Teacher.join_date,
                Teacher.created_at,
            )
            .where(Teacher.is_active == True)
            .order_by(Teacher.created_at.desc())
            .limit(limit)
        )
        rows = result.fetchall()
        return [
            {
                "id": r.id,
                "teacher_code": r.teacher_code,
                "full_name": r.full_name,
                "employment_status": r.employment_status.value if r.employment_status else None,
                "department": r.department,
                "specialization": r.specialization,
                "join_date": r.join_date.isoformat() if r.join_date else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
