"""
Teacher Portal Service – business logic layer.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Tuple, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.teacher_portal import (
    TeacherAccessDeniedException,
    TeacherAssignmentNotFoundException,
    TeacherPortalValidationException,
)
from app.modules.grading.entity import GradeAuditLog, StudentGrade
from app.modules.teacher_portal.dto import (
    AdminAttendanceBatchUpdateRequest,
    AttendanceBatchUpdateRequest,
    AttendanceBatchUpdateResponse,
    AttendanceMatrixResponse,
    AttendanceRecordEntry,
    ClassroomStudentsResponse,
    GradeAverageEntry,
    GradebookBatchUpdateRequest,
    GradebookBatchUpdateResponse,
    GradebookMatrixResponse,
    GradeComponentMini,
    GradeScoreEntry,
    RoundingRule,
    StudentMiniResponse,
    TeacherAssignmentListResponse,
    TeacherAssignmentResponse,
    TeacherDashboardResponse,
    TimetableEntryResponse,
    TimetableListResponse,
    TimetableAdminListResponse,
    TimetableAdminResponse,
    TimetableCreateRequest,
    TimetableUpdateRequest,
    UpcomingLessonResponse,
)
from app.modules.teacher_portal.entity import AttendanceRecord, AttendanceStatus, TimetableEntry
from app.modules.teacher_portal.repository import TeacherPortalRepository


ATTENDANCE_CYCLE_ORDER = [
    AttendanceStatus.PRESENT,
    AttendanceStatus.LATE,
    AttendanceStatus.ABSENT_EXCUSED,
    AttendanceStatus.ABSENT_UNEXCUSED,
]


class TeacherPortalService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = TeacherPortalRepository(session)

    # ------------------------------------------------------------------
    # Dashboard & Assignments
    # ------------------------------------------------------------------

    async def get_dashboard(self, teacher_id: int) -> TeacherDashboardResponse:
        assignments = await self._repo.list_teacher_assignments(teacher_id)
        classroom_ids = {cs.classroom_id for cs, _, _, _ in assignments}
        subject_ids = {cs.subject_id for cs, _, _, _ in assignments}

        now = datetime.utcnow()
        upcoming = await self._repo.list_upcoming_timetable_entries(
            teacher_id=teacher_id,
            date_from=now,
            date_to=now + timedelta(days=7),
        )
        class_map, subject_map = await self._load_timetable_refs(upcoming)
        upcoming_items = [
            UpcomingLessonResponse(
                id=entry.id,
                start=entry.start_time,
                end=entry.end_time,
                class_name=class_map.get(entry.classroom_id),
                subject_name=subject_map.get(entry.subject_id),
                room_number=entry.room_number,
            )
            for entry in upcoming
        ]

        return TeacherDashboardResponse(
            assignments_count=len(assignments),
            classrooms_count=len(classroom_ids),
            subjects_count=len(subject_ids),
            upcoming_lessons=upcoming_items,
        )

    async def list_assignments(
        self,
        teacher_id: int,
        academic_year: str | None = None,
        semester: int | None = None,
    ) -> TeacherAssignmentListResponse:
        rows = await self._repo.list_teacher_assignments(
            teacher_id=teacher_id,
            academic_year=academic_year,
            semester=semester,
        )
        items = [
            TeacherAssignmentResponse(
                class_subject_id=cs.id,
                classroom_id=classroom.id,
                class_code=classroom.class_code,
                class_name=classroom.class_name,
                subject_id=subject.id,
                subject_code=subject.subject_code,
                subject_name=subject.subject_name,
                semester=cs.semester,
                academic_year=cs.academic_year,
                student_count=student_count or 0,
            )
            for cs, classroom, subject, student_count in rows
        ]
        return TeacherAssignmentListResponse(items=items)

    async def list_classroom_students(
        self, teacher_id: int, classroom_id: int
    ) -> ClassroomStudentsResponse:
        await self._ensure_teacher_classroom(teacher_id, classroom_id)
        students = await self._repo.list_classroom_students(classroom_id)
        return ClassroomStudentsResponse(
            items=[
                StudentMiniResponse(
                    student_id=s.id,
                    student_code=s.student_code,
                    full_name=s.full_name,
                )
                for s in students
            ]
        )

    # ------------------------------------------------------------------
    # Gradebook
    # ------------------------------------------------------------------

    async def get_gradebook_matrix(
        self, teacher_id: int, class_subject_id: int
    ) -> GradebookMatrixResponse:
        class_subject = await self._ensure_teacher_class_subject(teacher_id, class_subject_id)
        components = await self._repo.list_grade_components(class_subject_id)
        students = await self._repo.list_classroom_students(class_subject.classroom_id)
        scores = await self._repo.list_student_grades(class_subject_id)
        averages = await self._repo.list_semester_averages(class_subject_id)

        return GradebookMatrixResponse(
            class_subject_id=class_subject_id,
            rounding=RoundingRule(),
            components=[
                GradeComponentMini(
                    grade_component_id=c.id,
                    name=c.component_name,
                    weight_percent=c.weight_percent,
                    min_count=c.min_count,
                )
                for c in components
            ],
            students=[
                StudentMiniResponse(
                    student_id=s.id,
                    student_code=s.student_code,
                    full_name=s.full_name,
                )
                for s in students
            ],
            scores=[
                GradeScoreEntry(
                    student_id=g.student_id,
                    grade_component_id=g.grade_component_id,
                    score=g.score,
                    exam_date=g.exam_date,
                )
                for g in scores
            ],
            averages=[
                GradeAverageEntry(
                    student_id=a.student_id,
                    average_score=a.average_score,
                    rank=a.rank.value if hasattr(a.rank, "value") else str(a.rank),
                )
                for a in averages
            ],
        )

    async def upsert_gradebook_entries(
        self, teacher_id: int, data: GradebookBatchUpdateRequest
    ) -> GradebookBatchUpdateResponse:
        class_subject = await self._ensure_teacher_class_subject(
            teacher_id, data.class_subject_id
        )
        components = await self._repo.list_grade_components(data.class_subject_id)
        component_ids = {c.id for c in components}
        students = await self._repo.list_classroom_students(class_subject.classroom_id)
        student_ids = {s.id for s in students}

        item_map: Dict[Tuple[int, int], Any] = {}
        for item in data.items:
            if item.grade_component_id not in component_ids:
                raise TeacherPortalValidationException(
                    detail=f"grade_component_id {item.grade_component_id} is not in class_subject"
                )
            if item.student_id not in student_ids:
                raise TeacherPortalValidationException(
                    detail=f"student_id {item.student_id} is not in classroom"
                )
            item_map[(item.student_id, item.grade_component_id)] = item

        keys = list(item_map.keys())
        existing_map = await self._repo.get_existing_grades(data.class_subject_id, keys)

        new_grades: List[StudentGrade] = []
        updated_grades: List[StudentGrade] = []
        audit_logs: List[GradeAuditLog] = []
        created = 0
        updated = 0

        for key, item in item_map.items():
            existing = existing_map.get(key)
            if existing:
                changed = False
                if Decimal(item.score) != existing.score:
                    audit_logs.append(
                        GradeAuditLog(
                            student_grade_id=existing.id,
                            old_score=existing.score,
                            new_score=item.score,
                            changed_by=teacher_id,
                            reason="Teacher portal batch update",
                        )
                    )
                    existing.score = item.score
                    changed = True
                if item.exam_date != existing.exam_date:
                    existing.exam_date = item.exam_date
                    changed = True
                if changed:
                    existing.last_modified_by = teacher_id
                    existing.last_modified_at = datetime.utcnow()
                    updated_grades.append(existing)
                    updated += 1
            else:
                new_grades.append(
                    StudentGrade(
                        student_id=item.student_id,
                        class_subject_id=data.class_subject_id,
                        grade_component_id=item.grade_component_id,
                        score=item.score,
                        exam_date=item.exam_date,
                        entered_by=teacher_id,
                    )
                )
                created += 1

        await self._repo.save_grade_entries(new_grades, updated_grades, audit_logs)
        return GradebookBatchUpdateResponse(created=created, updated=updated)

    # ------------------------------------------------------------------
    # Attendance
    # ------------------------------------------------------------------

    async def get_attendance_matrix(
        self,
        teacher_id: int,
        classroom_id: int,
        date_from: date,
        date_to: date,
    ) -> AttendanceMatrixResponse:
        if date_from > date_to:
            raise TeacherPortalValidationException(detail="date_from must be <= date_to")
        await self._ensure_teacher_classroom(teacher_id, classroom_id)
        students = await self._repo.list_classroom_students(classroom_id)
        records = await self._repo.list_attendance_records(classroom_id, date_from, date_to)

        total_by_student: Dict[int, int] = {}
        absent_by_student: Dict[int, int] = {}
        for record in records:
            total_by_student[record.student_id] = total_by_student.get(record.student_id, 0) + 1
            if record.status in (AttendanceStatus.ABSENT_EXCUSED, AttendanceStatus.ABSENT_UNEXCUSED):
                absent_by_student[record.student_id] = absent_by_student.get(record.student_id, 0) + 1

        student_items = []
        for s in students:
            total = total_by_student.get(s.id, 0)
            absent = absent_by_student.get(s.id, 0)
            absence_rate = round(absent / total, 4) if total else 0.0
            student_items.append(
                StudentMiniResponse(
                    student_id=s.id,
                    student_code=s.student_code,
                    full_name=s.full_name,
                    absence_rate=absence_rate,
                )
            )

        return AttendanceMatrixResponse(
            classroom_id=classroom_id,
            date_from=date_from,
            date_to=date_to,
            cycle_order=ATTENDANCE_CYCLE_ORDER,
            students=student_items,
            records=[
                AttendanceRecordEntry(
                    student_id=r.student_id,
                    date=r.attendance_date,
                    status=r.status,
                    note=r.note,
                )
                for r in records
            ],
        )

    async def upsert_attendance_entries(
        self, teacher_id: int, data: AttendanceBatchUpdateRequest
    ) -> AttendanceBatchUpdateResponse:
        await self._ensure_teacher_classroom(teacher_id, data.classroom_id)
        students = await self._repo.list_classroom_students(data.classroom_id)
        student_ids = {s.id for s in students}

        item_map: Dict[Tuple[int, date], Any] = {}
        for item in data.items:
            if item.student_id not in student_ids:
                raise TeacherPortalValidationException(
                    detail=f"student_id {item.student_id} is not in classroom"
                )
            item_map[(item.student_id, item.date)] = item

        keys = list(item_map.keys())
        existing_map = await self._repo.get_existing_attendance(data.classroom_id, keys)

        new_records: List[AttendanceRecord] = []
        updated_records: List[AttendanceRecord] = []
        created = 0
        updated = 0

        for key, item in item_map.items():
            existing = existing_map.get(key)
            if existing:
                changed = False
                if existing.status != item.status:
                    existing.status = item.status
                    changed = True
                if item.note != existing.note:
                    existing.note = item.note
                    changed = True
                if changed:
                    existing.recorded_by = teacher_id
                    updated_records.append(existing)
                    updated += 1
            else:
                new_records.append(
                    AttendanceRecord(
                        classroom_id=data.classroom_id,
                        student_id=item.student_id,
                        attendance_date=item.date,
                        status=item.status,
                        note=item.note,
                        recorded_by=teacher_id,
                    )
                )
                created += 1

        await self._repo.save_attendance_entries(new_records, updated_records)
        return AttendanceBatchUpdateResponse(created=created, updated=updated)

    # ------------------------------------------------------------------
    # Timetable
    # ------------------------------------------------------------------

    async def list_timetable(
        self,
        teacher_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> TimetableListResponse:
        if date_from > date_to:
            raise TeacherPortalValidationException(detail="from must be <= to")
        entries = await self._repo.list_timetable_entries(teacher_id, date_from, date_to)
        class_map, subject_map = await self._load_timetable_refs(entries)

        return TimetableListResponse(
            items=[
                TimetableEntryResponse(
                    id=e.id,
                    start=e.start_time,
                    end=e.end_time,
                    classroom_id=e.classroom_id,
                    class_name=class_map.get(e.classroom_id),
                    subject_name=subject_map.get(e.subject_id),
                    room_number=e.room_number,
                )
                for e in entries
            ]
        )

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Admin - Timetable
    # ------------------------------------------------------------------

    async def admin_list_timetable(
        self,
        date_from: datetime,
        date_to: datetime,
        teacher_id: Optional[int] = None,
    ) -> TimetableAdminListResponse:
        if date_from > date_to:
            raise TeacherPortalValidationException(detail="from must be <= to")
        entries = await self._repo.list_timetable_entries_admin(date_from, date_to, teacher_id)
        class_map, subject_map = await self._load_timetable_refs(entries)
        return TimetableAdminListResponse(
            items=[
                TimetableAdminResponse(
                    id=e.id,
                    teacher_id=e.teacher_id,
                    start=e.start_time,
                    end=e.end_time,
                    classroom_id=e.classroom_id,
                    class_name=class_map.get(e.classroom_id),
                    subject_name=subject_map.get(e.subject_id),
                    room_number=e.room_number,
                    note=e.note,
                )
                for e in entries
            ]
        )

    async def admin_create_timetable(self, data: TimetableCreateRequest) -> TimetableAdminResponse:
        if data.end_time <= data.start_time:
            raise TeacherPortalValidationException(detail="end_time must be after start_time")
        teacher = await self._repo.get_teacher_by_id(data.teacher_id)
        if not teacher:
            raise TeacherPortalValidationException(detail="teacher_id not found")

        classroom_id = data.classroom_id
        subject_id = data.subject_id
        if data.class_subject_id:
            class_subject = await self._repo.get_class_subject_by_id(data.class_subject_id)
            if not class_subject:
                raise TeacherPortalValidationException(detail="class_subject_id not found")
            if class_subject.teacher_id and class_subject.teacher_id != data.teacher_id:
                raise TeacherPortalValidationException(detail="class_subject does not belong to teacher")
            classroom_id = classroom_id or class_subject.classroom_id
            subject_id = subject_id or class_subject.subject_id

        entry = TimetableEntry(
            teacher_id=data.teacher_id,
            classroom_id=classroom_id,
            class_subject_id=data.class_subject_id,
            subject_id=subject_id,
            start_time=data.start_time,
            end_time=data.end_time,
            room_number=data.room_number,
            note=data.note,
        )
        entry = await self._repo.create_timetable_entry(entry)
        class_map, subject_map = await self._load_timetable_refs([entry])
        return TimetableAdminResponse(
            id=entry.id,
            teacher_id=entry.teacher_id,
            start=entry.start_time,
            end=entry.end_time,
            classroom_id=entry.classroom_id,
            class_name=class_map.get(entry.classroom_id),
            subject_name=subject_map.get(entry.subject_id),
            room_number=entry.room_number,
            note=entry.note,
        )

    async def admin_update_timetable(
        self,
        entry_id: int,
        data: TimetableUpdateRequest,
    ) -> TimetableAdminResponse:
        entry = await self._repo.get_timetable_entry_by_id(entry_id)
        if not entry:
            raise TeacherPortalValidationException(detail="timetable entry not found")

        update_data = data.model_dump(exclude_none=True)
        if "teacher_id" in update_data:
            teacher = await self._repo.get_teacher_by_id(update_data["teacher_id"])
            if not teacher:
                raise TeacherPortalValidationException(detail="teacher_id not found")

        if "class_subject_id" in update_data:
            class_subject = await self._repo.get_class_subject_by_id(update_data["class_subject_id"])
            if not class_subject:
                raise TeacherPortalValidationException(detail="class_subject_id not found")
            if "teacher_id" in update_data:
                if class_subject.teacher_id and class_subject.teacher_id != update_data["teacher_id"]:
                    raise TeacherPortalValidationException(detail="class_subject does not belong to teacher")
            update_data.setdefault("classroom_id", class_subject.classroom_id)
            update_data.setdefault("subject_id", class_subject.subject_id)

        start_time = update_data.get("start_time", entry.start_time)
        end_time = update_data.get("end_time", entry.end_time)
        if end_time <= start_time:
            raise TeacherPortalValidationException(detail="end_time must be after start_time")

        entry = await self._repo.update_timetable_entry(entry, update_data)
        class_map, subject_map = await self._load_timetable_refs([entry])
        return TimetableAdminResponse(
            id=entry.id,
            teacher_id=entry.teacher_id,
            start=entry.start_time,
            end=entry.end_time,
            classroom_id=entry.classroom_id,
            class_name=class_map.get(entry.classroom_id),
            subject_name=subject_map.get(entry.subject_id),
            room_number=entry.room_number,
            note=entry.note,
        )

    async def admin_delete_timetable(self, entry_id: int) -> TimetableAdminResponse:
        entry = await self._repo.get_timetable_entry_by_id(entry_id)
        if not entry:
            raise TeacherPortalValidationException(detail="timetable entry not found")
        entry = await self._repo.soft_delete_timetable_entry(entry)
        class_map, subject_map = await self._load_timetable_refs([entry])
        return TimetableAdminResponse(
            id=entry.id,
            teacher_id=entry.teacher_id,
            start=entry.start_time,
            end=entry.end_time,
            classroom_id=entry.classroom_id,
            class_name=class_map.get(entry.classroom_id),
            subject_name=subject_map.get(entry.subject_id),
            room_number=entry.room_number,
            note=entry.note,
        )

    # ------------------------------------------------------------------
    # Admin - Attendance
    # ------------------------------------------------------------------

    async def admin_get_attendance_matrix(
        self,
        classroom_id: int,
        date_from: date,
        date_to: date,
    ) -> AttendanceMatrixResponse:
        if date_from > date_to:
            raise TeacherPortalValidationException(detail="date_from must be <= date_to")
        students = await self._repo.list_classroom_students(classroom_id)
        records = await self._repo.list_attendance_records(classroom_id, date_from, date_to)

        total_by_student: Dict[int, int] = {}
        absent_by_student: Dict[int, int] = {}
        for record in records:
            total_by_student[record.student_id] = total_by_student.get(record.student_id, 0) + 1
            if record.status in (AttendanceStatus.ABSENT_EXCUSED, AttendanceStatus.ABSENT_UNEXCUSED):
                absent_by_student[record.student_id] = absent_by_student.get(record.student_id, 0) + 1

        student_items = []
        for s in students:
            total = total_by_student.get(s.id, 0)
            absent = absent_by_student.get(s.id, 0)
            absence_rate = round(absent / total, 4) if total else 0.0
            student_items.append(
                StudentMiniResponse(
                    student_id=s.id,
                    student_code=s.student_code,
                    full_name=s.full_name,
                    absence_rate=absence_rate,
                )
            )

        return AttendanceMatrixResponse(
            classroom_id=classroom_id,
            date_from=date_from,
            date_to=date_to,
            cycle_order=ATTENDANCE_CYCLE_ORDER,
            students=student_items,
            records=[
                AttendanceRecordEntry(
                    student_id=r.student_id,
                    date=r.attendance_date,
                    status=r.status,
                    note=r.note,
                )
                for r in records
            ],
        )

    async def admin_upsert_attendance_entries(
        self,
        data: AdminAttendanceBatchUpdateRequest,
    ) -> AttendanceBatchUpdateResponse:
        if data.recorded_by:
            teacher = await self._repo.get_teacher_by_id(data.recorded_by)
            if not teacher:
                raise TeacherPortalValidationException(detail="recorded_by teacher_id not found")

        students = await self._repo.list_classroom_students(data.classroom_id)
        student_ids = {s.id for s in students}

        item_map: Dict[Tuple[int, date], Any] = {}
        for item in data.items:
            if item.student_id not in student_ids:
                raise TeacherPortalValidationException(
                    detail=f"student_id {item.student_id} is not in classroom"
                )
            item_map[(item.student_id, item.date)] = item

        keys = list(item_map.keys())
        existing_map = await self._repo.get_existing_attendance(data.classroom_id, keys)

        new_records: List[AttendanceRecord] = []
        updated_records: List[AttendanceRecord] = []
        created = 0
        updated = 0

        for key, item in item_map.items():
            existing = existing_map.get(key)
            if existing:
                changed = False
                if existing.status != item.status:
                    existing.status = item.status
                    changed = True
                if item.note != existing.note:
                    existing.note = item.note
                    changed = True
                if changed:
                    if data.recorded_by is not None:
                        existing.recorded_by = data.recorded_by
                    updated_records.append(existing)
                    updated += 1
            else:
                new_records.append(
                    AttendanceRecord(
                        classroom_id=data.classroom_id,
                        student_id=item.student_id,
                        attendance_date=item.date,
                        status=item.status,
                        note=item.note,
                        recorded_by=data.recorded_by,
                    )
                )
                created += 1

        await self._repo.save_attendance_entries(new_records, updated_records)
        return AttendanceBatchUpdateResponse(created=created, updated=updated)

    # Internal helpers
    # ------------------------------------------------------------------

    async def _ensure_teacher_class_subject(self, teacher_id: int, class_subject_id: int):
        class_subject = await self._repo.get_class_subject_by_id(class_subject_id)
        if not class_subject or not class_subject.is_active:
            raise TeacherAssignmentNotFoundException(
                detail=f"class_subject_id {class_subject_id} not found"
            )
        if class_subject.teacher_id != teacher_id:
            raise TeacherAccessDeniedException(
                detail="You are not assigned to this class_subject"
            )
        return class_subject

    async def _ensure_teacher_classroom(self, teacher_id: int, classroom_id: int) -> None:
        has_access = await self._repo.teacher_has_classroom(teacher_id, classroom_id)
        if not has_access:
            raise TeacherAccessDeniedException(
                detail="You are not assigned to this classroom"
            )

    async def _load_timetable_refs(self, entries):
        classroom_ids = list({e.classroom_id for e in entries if e.classroom_id})
        subject_ids = list({e.subject_id for e in entries if e.subject_id})
        classrooms = await self._repo.get_classrooms_by_ids(classroom_ids)
        subjects = await self._repo.get_subjects_by_ids(subject_ids)
        class_map = {k: v.class_name for k, v in classrooms.items()}
        subject_map = {k: v.subject_name for k, v in subjects.items()}
        return class_map, subject_map

