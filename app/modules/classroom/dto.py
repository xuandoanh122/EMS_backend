"""
Classroom DTOs – Pydantic schemas.

Covers:
  - Classroom CRUD
  - StudentClassEnrollment CRUD
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.classroom.entity import (
    ClassType,
    EnrollmentStatus,
    EnrollmentType,
)


# ---------------------------------------------------------------------------
# Classroom
# ---------------------------------------------------------------------------

class _ClassroomBase(BaseModel):
    class_name: Optional[str] = Field(None, max_length=100)
    class_type: Optional[ClassType] = None
    academic_year: Optional[str] = Field(None, max_length=10, description="VD: '2024-2025'")
    grade_level: Optional[int] = Field(None, ge=1, le=13)
    homeroom_teacher_id: Optional[int] = None
    max_capacity: Optional[int] = Field(None, ge=1, le=200)
    room_number: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=300)

    @field_validator("academic_year")
    @classmethod
    def validate_academic_year(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            import re
            if not re.match(r"^\d{4}-\d{4}$", v):
                raise ValueError("academic_year must be in format 'YYYY-YYYY' (e.g. '2024-2025')")
        return v


class ClassroomCreateRequest(_ClassroomBase):
    class_code: str = Field(..., min_length=1, max_length=30, description="Mã lớp duy nhất")
    class_name: str = Field(..., min_length=1, max_length=100)
    class_type: ClassType = Field(default=ClassType.STANDARD)
    academic_year: str = Field(..., description="VD: '2024-2025'")
    grade_level: int = Field(..., ge=1, le=13)
    max_capacity: int = Field(default=40, ge=1, le=200)

    class Config:
        json_schema_extra = {
            "example": {
                "class_code": "10A1-2024",
                "class_name": "Lớp 10A1",
                "class_type": "standard",
                "academic_year": "2024-2025",
                "grade_level": 10,
                "max_capacity": 40,
                "room_number": "P.201",
            }
        }


class ClassroomUpdateRequest(_ClassroomBase):
    class Config:
        json_schema_extra = {
            "example": {
                "room_number": "P.305",
                "max_capacity": 35,
                "homeroom_teacher_id": 3,
            }
        }


class ClassroomResponse(BaseModel):
    id: int
    class_code: str
    class_name: str
    class_type: ClassType
    academic_year: str
    grade_level: int
    homeroom_teacher_id: Optional[int]
    max_capacity: int
    current_enrollment: int = 0  # Tính từ enrollments (lazy-loaded @property)
    room_number: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClassroomListResponse(BaseModel):
    items: List[ClassroomResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ClassroomQueryParams(BaseModel):
    search: Optional[str] = Field(None, description="Tìm theo class_code hoặc class_name")
    class_type: Optional[ClassType] = None
    academic_year: Optional[str] = None
    grade_level: Optional[int] = Field(None, ge=1, le=13)
    homeroom_teacher_id: Optional[int] = None
    has_capacity: Optional[bool] = Field(
        None,
        description="true = lớp chưa đầy (current_enrollment < max_capacity)",
    )
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# StudentClassEnrollment
# ---------------------------------------------------------------------------

class EnrollmentCreateRequest(BaseModel):
    student_id: int = Field(..., description="ID học sinh")
    classroom_id: Optional[int] = Field(None, description="ID lớp học (được set từ path param)")
    enrollment_type: EnrollmentType = Field(default=EnrollmentType.PRIMARY)
    enrolled_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=300)

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": 1,
                "enrollment_type": "primary",
                "enrolled_date": "2026-03-01",
            }
        }


class EnrollmentUpdateRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=300)

    class Config:
        json_schema_extra = {"example": {"notes": "Học sinh chuyển đến từ trường khác"}}


class EnrollmentStatusUpdateRequest(BaseModel):
    new_status: EnrollmentStatus
    left_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=300)

    class Config:
        json_schema_extra = {
            "example": {
                "new_status": "transferred",
                "left_date": "2024-12-01",
                "notes": "Chuyển sang lớp 10A2",
            }
        }


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    classroom_id: int
    enrollment_type: EnrollmentType
    status: EnrollmentStatus
    enrolled_date: Optional[date]
    left_date: Optional[date]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnrollmentListResponse(BaseModel):
    items: List[EnrollmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
