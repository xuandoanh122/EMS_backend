"""
Teacher Portal DTOs.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.modules.teacher_portal.entity import AttendanceStatus


class TeacherAssignmentResponse(BaseModel):
    class_subject_id: int
    classroom_id: int
    class_code: str
    class_name: str
    subject_id: int
    subject_code: str
    subject_name: str
    semester: int
    academic_year: str
    student_count: int


class TeacherAssignmentListResponse(BaseModel):
    items: List[TeacherAssignmentResponse]


class StudentMiniResponse(BaseModel):
    student_id: int
    student_code: str
    full_name: str
    absence_rate: Optional[float] = None


class ClassroomStudentsResponse(BaseModel):
    items: List[StudentMiniResponse]


class GradeComponentMini(BaseModel):
    grade_component_id: int
    name: str
    weight_percent: int
    min_count: int


class GradeScoreEntry(BaseModel):
    student_id: int
    grade_component_id: int
    score: Decimal
    exam_date: Optional[date] = None


class GradeAverageEntry(BaseModel):
    student_id: int
    average_score: Decimal
    rank: str


class RoundingRule(BaseModel):
    scale: str = Field(default="standard")
    precision: int = Field(default=1)
    rule: str = Field(default="round_half_up")


class GradebookMatrixResponse(BaseModel):
    class_subject_id: int
    rounding: RoundingRule
    components: List[GradeComponentMini]
    students: List[StudentMiniResponse]
    scores: List[GradeScoreEntry]
    averages: List[GradeAverageEntry]


class GradebookEntryItem(BaseModel):
    student_id: int
    grade_component_id: int
    score: Decimal = Field(..., ge=0, le=10)
    exam_date: Optional[date] = None


class GradebookBatchUpdateRequest(BaseModel):
    class_subject_id: int
    items: List[GradebookEntryItem]


class GradebookBatchUpdateResponse(BaseModel):
    created: int
    updated: int


class AttendanceRecordEntry(BaseModel):
    student_id: int
    date: date
    status: AttendanceStatus
    note: Optional[str] = None


class AttendanceMatrixResponse(BaseModel):
    classroom_id: int
    date_from: date
    date_to: date
    cycle_order: List[AttendanceStatus]
    students: List[StudentMiniResponse]
    records: List[AttendanceRecordEntry]


class AttendanceEntryItem(BaseModel):
    student_id: int
    date: date
    status: AttendanceStatus
    note: Optional[str] = Field(None, max_length=300)


class AttendanceBatchUpdateRequest(BaseModel):
    classroom_id: int
    items: List[AttendanceEntryItem]


class AttendanceBatchUpdateResponse(BaseModel):
    created: int
    updated: int


class TimetableEntryResponse(BaseModel):
    id: int
    start: datetime
    end: datetime
    classroom_id: Optional[int]
    class_name: Optional[str]
    subject_name: Optional[str]
    room_number: Optional[str]


class TimetableListResponse(BaseModel):
    items: List[TimetableEntryResponse]


class UpcomingLessonResponse(BaseModel):
    id: int
    start: datetime
    end: datetime
    class_name: Optional[str]
    subject_name: Optional[str]
    room_number: Optional[str]


class TeacherDashboardResponse(BaseModel):
    assignments_count: int
    classrooms_count: int
    subjects_count: int
    upcoming_lessons: List[UpcomingLessonResponse]


class TimetableCreateRequest(BaseModel):
    teacher_id: int
    classroom_id: Optional[int] = None
    class_subject_id: Optional[int] = None
    subject_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    room_number: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = Field(None, max_length=300)


class TimetableUpdateRequest(BaseModel):
    teacher_id: Optional[int] = None
    classroom_id: Optional[int] = None
    class_subject_id: Optional[int] = None
    subject_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    room_number: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = Field(None, max_length=300)
    is_active: Optional[bool] = None


class TimetableAdminResponse(BaseModel):
    id: int
    teacher_id: int
    start: datetime
    end: datetime
    classroom_id: Optional[int]
    class_name: Optional[str]
    subject_name: Optional[str]
    room_number: Optional[str]
    note: Optional[str]


class TimetableAdminListResponse(BaseModel):
    items: List[TimetableAdminResponse]


class AdminAttendanceBatchUpdateRequest(BaseModel):
    classroom_id: int
    recorded_by: Optional[int] = None
    items: List[AttendanceEntryItem]
