"""
Teacher entity – maps to the 'teachers' table in MSSQL.

Table design:
  - Profile: personal info, contact, qualifications, employment info.
  - Employment status: 'active' | 'on_leave' | 'resigned' | 'retired'
  - All column names are English per convention.
"""

import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    Unicode,
    UnicodeText,
)
from sqlalchemy.sql import func

from app.modules.student.entity import Base


# ---------------------------------------------------------------------------
# Enum – Teacher employment status
# ---------------------------------------------------------------------------

class TeacherStatus(str, enum.Enum):
    ACTIVE    = "active"     # Đang công tác
    ON_LEAVE  = "on_leave"   # Đang nghỉ phép / bảo lưu
    RESIGNED  = "resigned"   # Đã nghỉ việc
    RETIRED   = "retired"    # Đã nghỉ hưu


# ---------------------------------------------------------------------------
# Valid status transitions
# key = current status → value = set of allowed next statuses
# ---------------------------------------------------------------------------

VALID_TEACHER_STATUS_TRANSITIONS: dict[TeacherStatus, set[TeacherStatus]] = {
    TeacherStatus.ACTIVE: {
        TeacherStatus.ON_LEAVE,
        TeacherStatus.RESIGNED,
        TeacherStatus.RETIRED,
    },
    TeacherStatus.ON_LEAVE: {
        TeacherStatus.ACTIVE,    # Quay lại làm việc
        TeacherStatus.RESIGNED,
    },
    TeacherStatus.RESIGNED: set(),   # Terminal – không thể chuyển
    TeacherStatus.RETIRED:  set(),   # Terminal – không thể chuyển
}


# ---------------------------------------------------------------------------
# Primary table: teachers
# ---------------------------------------------------------------------------

class Teacher(Base):
    """
    Core teacher profile entity.

    Columns:
        id                  – Auto-increment PK.
        teacher_code        – Unique business identifier (e.g. 'GV2024001').
        full_name           – Full name.
        date_of_birth       – Date of birth.
        gender              – 'male' | 'female' | 'other'.
        national_id         – National ID / CCCD (unique).
        email               – Work email (unique).
        phone_number        – Contact phone.
        address             – Permanent address.
        specialization      – Subject / field of expertise.
        qualification       – Highest academic qualification.
        join_date           – Date joined the institution.
        employment_status   – Current employment status (TeacherStatus enum).
        department          – Department name.
        is_active           – Soft-delete flag.
        created_at          – Auto timestamp on insert.
        updated_at          – Auto timestamp on update.
    """

    __tablename__ = "teachers"

    id           = Column(Integer, primary_key=True, autoincrement=True, index=True)
    teacher_code = Column(String(20),   unique=True, nullable=False, index=True)
    full_name    = Column(Unicode(150), nullable=False)
    date_of_birth = Column(Date,        nullable=True)
    gender       = Column(String(10),   nullable=True)
    national_id  = Column(String(20),   unique=True, nullable=True, index=True)
    email        = Column(String(200),  unique=True, nullable=True, index=True)
    phone_number = Column(String(20),   nullable=True)
    address      = Column(UnicodeText,  nullable=True)

    specialization    = Column(Unicode(200), nullable=True)
    qualification     = Column(Unicode(200), nullable=True)
    join_date         = Column(Date,         nullable=True)
    employment_status = Column(
        Enum(TeacherStatus),
        nullable=False,
        default=TeacherStatus.ACTIVE,
        index=True,
    )
    department = Column(Unicode(200), nullable=True, index=True)

    is_active  = Column(Boolean,  nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<Teacher id={self.id} code='{self.teacher_code}' "
            f"name='{self.full_name}' status='{self.employment_status}' "
            f"active={self.is_active}>"
        )
