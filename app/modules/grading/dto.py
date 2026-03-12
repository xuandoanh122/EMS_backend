"""
Grading DTOs – Pydantic schemas.

Covers:
  - Subject CRUD
  - ClassSubject (phân công môn – lớp – GV)
  - GradeComponent (cấu hình hệ số điểm)
  - StudentGrade (nhập/sửa điểm)
  - GradeAuditLog (chỉ read)
  - SemesterAverage (chỉ read + tính lại)
  - Statistics / báo cáo
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.grading.entity import AcademicRank, SubjectType


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------

class SubjectCreateRequest(BaseModel):
    subject_code: str = Field(..., min_length=1, max_length=20)
    subject_name: str = Field(..., min_length=1, max_length=100)
    subject_type: SubjectType = Field(default=SubjectType.STANDARD)
    credits: int = Field(default=1, ge=1, le=10)
    description: Optional[str] = Field(None, max_length=300)

    class Config:
        json_schema_extra = {
            "example": {
                "subject_code": "TOAN",
                "subject_name": "Toán học",
                "subject_type": "standard",
                "credits": 4,
            }
        }


class SubjectUpdateRequest(BaseModel):
    subject_name: Optional[str] = Field(None, max_length=100)
    credits: Optional[int] = Field(None, ge=1, le=10)
    description: Optional[str] = Field(None, max_length=300)
    is_active: Optional[bool] = None


class SubjectResponse(BaseModel):
    id: int
    subject_code: str
    subject_name: str
    subject_type: SubjectType
    credits: int
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubjectListResponse(BaseModel):
    items: List[SubjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# ClassSubject (Phân công môn – lớp – GV)
# ---------------------------------------------------------------------------

class ClassSubjectCreateRequest(BaseModel):
    classroom_id: int
    subject_id: int
    teacher_id: Optional[int] = None
    semester: int = Field(..., ge=1, le=2)
    academic_year: str = Field(..., description="VD: '2024-2025'")

    @field_validator("academic_year")
    @classmethod
    def validate_year(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{4}-\d{4}$", v):
            raise ValueError("academic_year must be 'YYYY-YYYY'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "classroom_id": 1,
                "subject_id": 2,
                "teacher_id": 3,
                "semester": 1,
                "academic_year": "2024-2025",
            }
        }


class ClassSubjectUpdateRequest(BaseModel):
    teacher_id: Optional[int] = None
    is_active: Optional[bool] = None


class ClassSubjectResponse(BaseModel):
    id: int
    classroom_id: int
    subject_id: int
    teacher_id: Optional[int]
    semester: int
    academic_year: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClassSubjectListResponse(BaseModel):
    items: List[ClassSubjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# GradeComponent (Cấu hình thành phần điểm)
# ---------------------------------------------------------------------------

class GradeComponentCreateRequest(BaseModel):
    class_subject_id: int
    component_name: str = Field(..., min_length=1, max_length=100)
    weight_percent: int = Field(..., ge=1, le=100)
    min_count: int = Field(default=1, ge=1)

    class Config:
        json_schema_extra = {
            "example": {
                "class_subject_id": 1,
                "component_name": "Kiểm tra miệng",
                "weight_percent": 10,
                "min_count": 2,
            }
        }


class GradeComponentUpdateRequest(BaseModel):
    component_name: Optional[str] = Field(None, max_length=100)
    weight_percent: Optional[int] = Field(None, ge=1, le=100)
    min_count: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class GradeComponentResponse(BaseModel):
    id: int
    class_subject_id: int
    component_name: str
    weight_percent: int
    min_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# StudentGrade (Nhập/sửa điểm)
# ---------------------------------------------------------------------------

class StudentGradeCreateRequest(BaseModel):
    student_id: int
    class_subject_id: int
    grade_component_id: int
    score: Decimal = Field(..., ge=0, le=10)
    exam_date: Optional[date] = None
    entered_by: Optional[int] = Field(None, description="ID giáo viên nhập điểm")

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": 1,
                "class_subject_id": 3,
                "grade_component_id": 2,
                "score": 8.5,
                "exam_date": "2024-11-10",
                "entered_by": 4,
            }
        }


class StudentGradeBulkCreateRequest(BaseModel):
    """Nhập điểm hàng loạt cho nhiều học sinh cùng 1 cột điểm."""
    class_subject_id: int
    grade_component_id: int
    exam_date: Optional[date] = None
    entered_by: Optional[int] = None
    grades: List[Dict[str, Any]] = Field(
        ...,
        description="List of {student_id: int, score: float}",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "class_subject_id": 3,
                "grade_component_id": 2,
                "exam_date": "2024-11-10",
                "entered_by": 4,
                "grades": [
                    {"student_id": 1, "score": 8.5},
                    {"student_id": 2, "score": 7.0},
                    {"student_id": 3, "score": 9.0},
                ],
            }
        }


class StudentGradeUpdateRequest(BaseModel):
    score: Decimal = Field(..., ge=0, le=10)
    reason: str = Field(..., min_length=1, max_length=300, description="Lý do sửa điểm (bắt buộc)")
    modified_by: Optional[int] = Field(None, description="ID giáo viên sửa điểm")

    class Config:
        json_schema_extra = {
            "example": {
                "score": 9.0,
                "reason": "Chấm sai, đã phúc tra lại",
                "modified_by": 4,
            }
        }


class StudentGradeResponse(BaseModel):
    id: int
    student_id: int
    class_subject_id: int
    grade_component_id: int
    score: Decimal
    exam_date: Optional[date]
    entered_by: Optional[int]
    entered_at: datetime
    last_modified_by: Optional[int]
    last_modified_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StudentGradeListResponse(BaseModel):
    items: List[StudentGradeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# GradeAuditLog (chỉ đọc)
# ---------------------------------------------------------------------------

class GradeAuditLogResponse(BaseModel):
    id: int
    student_grade_id: int
    old_score: Decimal
    new_score: Decimal
    changed_by: Optional[int]
    changed_at: datetime
    reason: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# SemesterAverage (chỉ đọc)
# ---------------------------------------------------------------------------

class SemesterAverageResponse(BaseModel):
    id: int
    student_id: int
    class_subject_id: int
    semester: int
    academic_year: str
    average_score: Decimal
    rank: AcademicRank
    calculated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Statistics / Báo cáo
# ---------------------------------------------------------------------------

class GradeStatisticsResponse(BaseModel):
    """Thống kê điểm cho 1 môn học tại 1 lớp, 1 học kỳ."""
    class_subject_id: int
    classroom_id: int
    subject_id: int
    semester: int
    academic_year: str
    total_students: int
    avg_score: Optional[Decimal]
    max_score: Optional[Decimal]
    min_score: Optional[Decimal]
    rank_distribution: Dict[str, int]  # {"Gioi": 10, "Kha": 15, ...}


class StudentReportResponse(BaseModel):
    """Báo cáo điểm của 1 học sinh trong 1 học kỳ."""
    student_id: int
    semester: int
    academic_year: str
    subjects: List[SemesterAverageResponse]
    overall_average: Optional[Decimal]
    overall_rank: Optional[AcademicRank]
