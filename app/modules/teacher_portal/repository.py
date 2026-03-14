"""
Teacher Portal Repository – database access layer.
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select, tuple_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database import DatabaseQueryException
from app.modules.classroom.entity import Classroom, StudentClassEnrollment, EnrollmentStatus
from app.modules.grading.entity import (
    ClassSubject,
    GradeAuditLog,
    GradeComponent,
    SemesterAverage,
    StudentGrade,
    Subject,
)
from app.modules.student.entity import Student
from app.modules.teacher.entity import Teacher
from app.modules.teacher_portal.entity import AttendanceRecord, TimetableEntry


class TeacherPortalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ------------------------------------------------------------------
    # Assignments & access
    # ------------------------------------------------------------------

    async def list_teacher_assignments(
        self,
        teacher_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[int] = None,
    ) -> List[Tuple[ClassSubject, Classroom, Subject, int]]:
        try:
            enrollment_count = (
                select(
                    StudentClassEnrollment.classroom_id.label("classroom_id"),
                    func.count(StudentClassEnrollment.id).label("student_count"),
                )
                .where(
                    StudentClassEnrollment.is_active == True,
                    StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
                )
                .group_by(StudentClassEnrollment.classroom_id)
                .subquery()
            )

            q = (
                select(
                    ClassSubject,
                    Classroom,
                    Subject,
                    func.coalesce(enrollment_count.c.student_count, 0),
                )
                .join(Classroom, ClassSubject.classroom_id == Classroom.id)
                .join(Subject, ClassSubject.subject_id == Subject.id)
                .outerjoin(
                    enrollment_count,
                    enrollment_count.c.classroom_id == Classroom.id,
                )
                .where(
                    ClassSubject.teacher_id == teacher_id,
                    ClassSubject.is_active == True,
                )
                .order_by(ClassSubject.academic_year.desc(), Classroom.class_name.asc())
            )
            if academic_year:
                q = q.where(ClassSubject.academic_year == academic_year)
            if semester:
                q = q.where(ClassSubject.semester == semester)

            result = await self._s.execute(q)
            return list(result.all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_teacher_assignments", reason=str(exc)) from exc

    async def get_class_subject_by_id(self, class_subject_id: int) -> Optional[ClassSubject]:
        try:
            result = await self._s.execute(
                select(ClassSubject).where(ClassSubject.id == class_subject_id)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_class_subject_by_id", reason=str(exc)) from exc

    async def teacher_has_classroom(self, teacher_id: int, classroom_id: int) -> bool:
        try:
            result = await self._s.execute(
                select(ClassSubject.id).where(
                    ClassSubject.teacher_id == teacher_id,
                    ClassSubject.classroom_id == classroom_id,
                    ClassSubject.is_active == True,
                )
            )
            return result.scalar() is not None
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="teacher_has_classroom", reason=str(exc)) from exc

    # ------------------------------------------------------------------
    # Students / Gradebook data
    # ------------------------------------------------------------------

    async def list_classroom_students(self, classroom_id: int) -> List[Student]:
        try:
            result = await self._s.execute(
                select(Student)
                .join(StudentClassEnrollment, StudentClassEnrollment.student_id == Student.id)
                .where(
                    StudentClassEnrollment.classroom_id == classroom_id,
                    StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
                    StudentClassEnrollment.is_active == True,
                    Student.is_active == True,
                )
                .order_by(Student.full_name.asc())
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_classroom_students", reason=str(exc)) from exc

    async def list_grade_components(self, class_subject_id: int) -> List[GradeComponent]:
        try:
            result = await self._s.execute(
                select(GradeComponent).where(
                    GradeComponent.class_subject_id == class_subject_id,
                    GradeComponent.is_active == True,
                )
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_grade_components", reason=str(exc)) from exc

    async def list_student_grades(self, class_subject_id: int) -> List[StudentGrade]:
        try:
            result = await self._s.execute(
                select(StudentGrade).where(
                    StudentGrade.class_subject_id == class_subject_id,
                    StudentGrade.is_active == True,
                )
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_student_grades", reason=str(exc)) from exc

    async def list_semester_averages(self, class_subject_id: int) -> List[SemesterAverage]:
        try:
            result = await self._s.execute(
                select(SemesterAverage).where(SemesterAverage.class_subject_id == class_subject_id)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_semester_averages", reason=str(exc)) from exc

    async def get_existing_grades(
        self,
        class_subject_id: int,
        keys: List[Tuple[int, int]],
    ) -> Dict[Tuple[int, int], StudentGrade]:
        if not keys:
            return {}
        try:
            result = await self._s.execute(
                select(StudentGrade).where(
                    StudentGrade.class_subject_id == class_subject_id,
                    StudentGrade.is_active == True,
                    tuple_(StudentGrade.student_id, StudentGrade.grade_component_id).in_(keys),
                )
            )
            return {(g.student_id, g.grade_component_id): g for g in result.scalars().all()}
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_existing_grades", reason=str(exc)) from exc

    async def save_grade_entries(
        self,
        new_grades: List[StudentGrade],
        updated_grades: List[StudentGrade],
        audit_logs: List[GradeAuditLog],
    ) -> None:
        try:
            if new_grades:
                self._s.add_all(new_grades)
            if updated_grades:
                for obj in updated_grades:
                    self._s.add(obj)
            if audit_logs:
                self._s.add_all(audit_logs)
            await self._s.commit()
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="save_grade_entries", reason=str(exc)) from exc

    # ------------------------------------------------------------------
    # Attendance
    # ------------------------------------------------------------------

    async def list_attendance_records(
        self,
        classroom_id: int,
        date_from: date,
        date_to: date,
    ) -> List[AttendanceRecord]:
        try:
            result = await self._s.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.classroom_id == classroom_id,
                    AttendanceRecord.attendance_date >= date_from,
                    AttendanceRecord.attendance_date <= date_to,
                    AttendanceRecord.is_active == True,
                )
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_attendance_records", reason=str(exc)) from exc

    async def get_existing_attendance(
        self,
        classroom_id: int,
        keys: List[Tuple[int, date]],
    ) -> Dict[Tuple[int, date], AttendanceRecord]:
        if not keys:
            return {}
        try:
            result = await self._s.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.classroom_id == classroom_id,
                    AttendanceRecord.is_active == True,
                    tuple_(AttendanceRecord.student_id, AttendanceRecord.attendance_date).in_(keys),
                )
            )
            return {(r.student_id, r.attendance_date): r for r in result.scalars().all()}
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_existing_attendance", reason=str(exc)) from exc

    async def save_attendance_entries(
        self,
        new_records: List[AttendanceRecord],
        updated_records: List[AttendanceRecord],
    ) -> None:
        try:
            if new_records:
                self._s.add_all(new_records)
            if updated_records:
                for obj in updated_records:
                    self._s.add(obj)
            await self._s.commit()
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="save_attendance_entries", reason=str(exc)) from exc

    # ------------------------------------------------------------------
    # Timetable helpers
    # ------------------------------------------------------------------

    async def list_timetable_entries(
        self,
        teacher_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> List[TimetableEntry]:
        try:
            result = await self._s.execute(
                select(TimetableEntry).where(
                    TimetableEntry.teacher_id == teacher_id,
                    TimetableEntry.is_active == True,
                    TimetableEntry.start_time >= date_from,
                    TimetableEntry.end_time <= date_to,
                ).order_by(TimetableEntry.start_time.asc())
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_timetable_entries", reason=str(exc)) from exc

    async def list_upcoming_timetable_entries(
        self,
        teacher_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> List[TimetableEntry]:
        try:
            result = await self._s.execute(
                select(TimetableEntry).where(
                    TimetableEntry.teacher_id == teacher_id,
                    TimetableEntry.is_active == True,
                    TimetableEntry.start_time >= date_from,
                    TimetableEntry.start_time <= date_to,
                ).order_by(TimetableEntry.start_time.asc())
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_upcoming_timetable_entries", reason=str(exc)) from exc

    async def get_classrooms_by_ids(self, ids: List[int]) -> Dict[int, Classroom]:
        if not ids:
            return {}
        try:
            result = await self._s.execute(
                select(Classroom).where(Classroom.id.in_(ids))
            )
            return {c.id: c for c in result.scalars().all()}
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_classrooms_by_ids", reason=str(exc)) from exc

    async def get_subjects_by_ids(self, ids: List[int]) -> Dict[int, Subject]:
        if not ids:
            return {}
        try:
            result = await self._s.execute(
                select(Subject).where(Subject.id.in_(ids))
            )
            return {s.id: s for s in result.scalars().all()}
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_subjects_by_ids", reason=str(exc)) from exc

    async def get_teacher_by_id(self, teacher_id: int) -> Optional[Teacher]:
        try:
            result = await self._s.execute(
                select(Teacher).where(Teacher.id == teacher_id)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_teacher_by_id", reason=str(exc)) from exc

    async def create_timetable_entry(self, entry: TimetableEntry) -> TimetableEntry:
        try:
            self._s.add(entry)
            await self._s.commit()
            await self._s.refresh(entry)
            return entry
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="create_timetable_entry", reason=str(exc)) from exc

    async def get_timetable_entry_by_id(self, entry_id: int) -> Optional[TimetableEntry]:
        try:
            result = await self._s.execute(
                select(TimetableEntry).where(TimetableEntry.id == entry_id, TimetableEntry.is_active == True)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_timetable_entry_by_id", reason=str(exc)) from exc

    async def update_timetable_entry(self, entry: TimetableEntry, data: dict) -> TimetableEntry:
        try:
            for field, value in data.items():
                if hasattr(entry, field):
                    setattr(entry, field, value)
            await self._s.commit()
            await self._s.refresh(entry)
            return entry
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="update_timetable_entry", reason=str(exc)) from exc

    async def soft_delete_timetable_entry(self, entry: TimetableEntry) -> TimetableEntry:
        try:
            entry.is_active = False
            await self._s.commit()
            await self._s.refresh(entry)
            return entry
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="soft_delete_timetable_entry", reason=str(exc)) from exc

    async def list_timetable_entries_admin(
        self,
        date_from: datetime,
        date_to: datetime,
        teacher_id: Optional[int] = None,
    ) -> List[TimetableEntry]:
        try:
            q = select(TimetableEntry).where(
                TimetableEntry.is_active == True,
                TimetableEntry.start_time >= date_from,
                TimetableEntry.end_time <= date_to,
            )
            if teacher_id:
                q = q.where(TimetableEntry.teacher_id == teacher_id)
            result = await self._s.execute(q.order_by(TimetableEntry.start_time.asc()))
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_timetable_entries_admin", reason=str(exc)) from exc
