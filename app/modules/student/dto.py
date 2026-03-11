"""
Student DTOs (Data Transfer Objects) – Pydantic schemas.

Defines:
  - StudentCreateRequest   : payload for POST /students
  - StudentUpdateRequest   : payload for PATCH /students/{student_code}
  - StudentStatusUpdateRequest : payload for PATCH /students/{student_code}/status
  - StudentResponse        : single student returned to client
  - StudentListResponse    : paginated list wrapper
  - StudentQueryParams     : query filters for listing students
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.student.entity import StudentStatus


# ---------------------------------------------------------------------------
# Shared base – fields used by both Create and Update
# ---------------------------------------------------------------------------

class _StudentBase(BaseModel):
    full_name: Optional[str] = Field(
        None, max_length=150, description="Full name of the student"
    )
    date_of_birth: Optional[date] = Field(None, description="Date of birth (YYYY-MM-DD)")
    gender: Optional[str] = Field(None, description="'male' | 'female' | 'other'")
    national_id: Optional[str] = Field(
        None, max_length=20, description="National ID / CCCD number"
    )
    email: Optional[EmailStr] = Field(None, description="Student email address")
    phone_number: Optional[str] = Field(
        None, max_length=20, description="Student phone number"
    )
    address: Optional[str] = Field(None, description="Permanent address")
    class_name: Optional[str] = Field(
        None, max_length=50, description="Class assignment (e.g. '12A1')"
    )
    program_name: Optional[str] = Field(
        None, max_length=200, description="Study program / curriculum name"
    )
    parent_full_name: Optional[str] = Field(
        None, max_length=150, description="Guardian / parent full name"
    )
    parent_phone: Optional[str] = Field(
        None, max_length=20, description="Guardian / parent phone number"
    )
    parent_email: Optional[EmailStr] = Field(
        None, description="Guardian / parent email address"
    )
    medical_notes: Optional[str] = Field(
        None, description="Free-text medical history or health notes"
    )

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("male", "female", "other"):
            raise ValueError("gender must be 'male', 'female', or 'other'")
        return v


# ---------------------------------------------------------------------------
# Create Request
# ---------------------------------------------------------------------------

class StudentCreateRequest(_StudentBase):
    """Payload for POST /students – create a new student profile."""

    student_code: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Unique student business code (e.g. 'SV2024001')",
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Full name of the student (required on create)",
    )
    enrollment_date: Optional[date] = Field(
        None, description="Date of first enrollment"
    )
    academic_status: StudentStatus = Field(
        default=StudentStatus.ACTIVE,
        description="Initial academic status",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "student_code": "SV2024001",
                "full_name": "Nguyen Van An",
                "date_of_birth": "2006-05-15",
                "gender": "male",
                "email": "an.nguyen@student.edu.vn",
                "phone_number": "0901234567",
                "enrollment_date": "2024-09-01",
                "class_name": "12A1",
                "program_name": "Công nghệ thông tin",
                "parent_full_name": "Nguyen Van Binh",
                "parent_phone": "0912345678",
            }
        }


# ---------------------------------------------------------------------------
# Update Request  (all fields optional – PATCH semantics)
# ---------------------------------------------------------------------------

class StudentUpdateRequest(_StudentBase):
    """
    Payload for PATCH /students/{student_code} – partial update.
    Only fields provided will be updated (None fields are skipped in service).
    """

    enrollment_date: Optional[date] = None

    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "0909999888",
                "address": "123 Nguyen Hue, Q1, TP.HCM",
                "class_name": "12A2",
            }
        }


# ---------------------------------------------------------------------------
# Status Update Request
# ---------------------------------------------------------------------------

class StudentStatusUpdateRequest(BaseModel):
    """Payload for PATCH /students/{student_code}/status – change academic status."""

    new_status: StudentStatus = Field(..., description="Target academic status")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for the status change (optional but recommended)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "new_status": "preserved",
                "reason": "Student requested leave of absence for personal reasons",
            }
        }


# ---------------------------------------------------------------------------
# Response Schema  (what the API returns to the client)
# ---------------------------------------------------------------------------

class StudentResponse(BaseModel):
    """Single student response DTO."""

    id: int
    student_code: str
    full_name: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    national_id: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    address: Optional[str]
    enrollment_date: Optional[date]
    academic_status: StudentStatus
    class_name: Optional[str]
    program_name: Optional[str]
    parent_full_name: Optional[str]
    parent_phone: Optional[str]
    parent_email: Optional[str]
    medical_notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Paginated List Response
# ---------------------------------------------------------------------------

class StudentListResponse(BaseModel):
    """Paginated list of students."""

    items: List[StudentResponse]
    total: int = Field(..., description="Total number of matching records")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


# ---------------------------------------------------------------------------
# Query Parameters for listing students
# ---------------------------------------------------------------------------

class StudentQueryParams(BaseModel):
    """Filters and pagination for GET /students."""

    search: Optional[str] = Field(
        None,
        description="Search by student_code, full_name, or email",
    )
    academic_status: Optional[StudentStatus] = Field(
        None, description="Filter by academic status"
    )
    class_name: Optional[str] = Field(None, description="Filter by class name")
    program_name: Optional[str] = Field(None, description="Filter by program name")
    page: int = Field(default=1, ge=1, description="Page number (starts at 1)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Items per page (max 100)"
    )
