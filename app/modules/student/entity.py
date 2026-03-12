"""
Student entity – maps directly to the 'students' table in MSSQL.
Uses SQLAlchemy declarative base from app.core.database.

Table design follows README:
- Profile: personal info, parent contact, medical history, academic status.
- Status values: 'active' | 'preserved' | 'suspended' | 'graduated'
- All column names are English per convention (student_code, full_name, etc.)

Two tables are defined:
  - Student        → 'students'        (primary table)
  - StudentBackup  → 'students_backup' (snapshot/fallback table)
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
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


# ---------------------------------------------------------------------------
# Declarative Base  (shared across all entities in the project)
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enum – Student academic status
# ---------------------------------------------------------------------------

class StudentStatus(str, enum.Enum):
    ACTIVE    = "active"      # Đang học
    PRESERVED = "preserved"   # Bảo lưu
    SUSPENDED = "suspended"   # Đình chỉ
    GRADUATED = "graduated"   # Đã tốt nghiệp


# ---------------------------------------------------------------------------
# Valid status transitions
# key = current status → value = set of allowed next statuses
# ---------------------------------------------------------------------------

VALID_STATUS_TRANSITIONS: dict[StudentStatus, set[StudentStatus]] = {
    StudentStatus.ACTIVE: {
        StudentStatus.PRESERVED,
        StudentStatus.SUSPENDED,
        StudentStatus.GRADUATED,
    },
    StudentStatus.PRESERVED: {
        StudentStatus.ACTIVE,     # Quay lại học
        StudentStatus.SUSPENDED,
    },
    StudentStatus.SUSPENDED: {
        StudentStatus.ACTIVE,     # Phục hồi
    },
    StudentStatus.GRADUATED: set(),   # Terminal state – no transitions allowed
}


# ---------------------------------------------------------------------------
# Primary table: students
# ---------------------------------------------------------------------------

class Student(Base):
    """
    Core student profile entity.

    Columns:
        id                  – Auto-increment PK (internal use only).
        student_code        – Unique business identifier (e.g. 'SV2024001').
        full_name           – Full name of the student.
        date_of_birth       – Date of birth.
        gender              – 'male' | 'female' | 'other'.
        national_id         – National identification number (CCCD/CMND).
        email               – Student email (unique).
        phone_number        – Student phone number.
        address             – Permanent address.
        enrollment_date     – Date of first enrollment.
        academic_status     – Current academic status (StudentStatus enum).
        class_name          – Current class assignment (e.g. '12A1').
        program_name        – Study program/curriculum (e.g. 'Công nghệ thông tin').
        parent_full_name    – Guardian/parent name.
        parent_phone        – Guardian/parent contact number.
        parent_email        – Guardian/parent email.
        medical_notes       – Free-text medical history / health notes.
        is_active           – Soft-delete flag (False = deleted record).
        created_at          – Auto timestamp on insert.
        updated_at          – Auto timestamp on update.
    """

    __tablename__ = "students"

    id            = Column(Integer, primary_key=True, autoincrement=True, index=True)
    student_code  = Column(String(20),   unique=True, nullable=False, index=True)
    full_name     = Column(Unicode(150), nullable=False)
    date_of_birth = Column(Date,         nullable=True)
    gender        = Column(String(10),   nullable=True)
    national_id   = Column(String(20),   unique=True, nullable=True, index=True)
    email         = Column(String(200),  unique=True, nullable=True, index=True)
    phone_number  = Column(String(20),   nullable=True)
    address       = Column(UnicodeText,  nullable=True)

    enrollment_date = Column(Date, nullable=True)
    academic_status = Column(
        Enum(StudentStatus),
        nullable=False,
        default=StudentStatus.ACTIVE,
        index=True,
    )
    class_name   = Column(Unicode(50),  nullable=True, index=True)
    program_name = Column(Unicode(200), nullable=True)

    # Parent / Guardian contact
    parent_full_name = Column(Unicode(150), nullable=True)
    parent_phone     = Column(String(20),   nullable=True)
    parent_email     = Column(String(200),  nullable=True)

    # Medical history
    medical_notes = Column(UnicodeText, nullable=True)

    # Soft-delete & audit timestamps
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
            f"<Student id={self.id} code='{self.student_code}' "
            f"name='{self.full_name}' status='{self.academic_status}' "
            f"active={self.is_active}>"
        )


# ---------------------------------------------------------------------------
# Backup table: students_backup
#
# Purpose:
#   - Automatic snapshot when PRIMARY (MSSQL) is unreachable and the system
#     switches to the SQLite fallback – data written to SQLite is later
#     synced back to MSSQL and a backup row is kept for audit.
#   - Manual snapshot before large batch imports / bulk updates.
#
# Design notes:
#   - 'backup_id'     : own PK, independent of students.id.
#   - 'id'            : the original students.id value (no FK – intentional,
#                       allows keeping orphaned backup rows after deletion).
#   - 'backup_reason' : free-text tag (e.g. 'primary_db_offline', 'pre_import').
#   - 'backed_up_at'  : when the snapshot was taken.
#   - All student columns are nullable so partial snapshots are valid.
# ---------------------------------------------------------------------------

class StudentBackup(Base):
    """Snapshot/fallback table for student records."""

    __tablename__ = "students_backup"

    backup_id     = Column(Integer, primary_key=True, autoincrement=True)
    backup_reason = Column(Unicode(200), nullable=True)
    backed_up_at  = Column(DateTime, nullable=False,
                           server_default=func.now(), index=True)

    # ── Mirrored student columns (all nullable for flexibility) ──────────
    id            = Column(Integer,      nullable=True, index=True)
    student_code  = Column(String(20),   nullable=True, index=True)
    full_name     = Column(Unicode(150), nullable=True)
    date_of_birth = Column(Date,         nullable=True)
    gender        = Column(String(10),   nullable=True)
    national_id   = Column(String(20),   nullable=True)
    email         = Column(String(200),  nullable=True)
    phone_number  = Column(String(20),   nullable=True)
    address       = Column(UnicodeText,  nullable=True)

    enrollment_date = Column(Date, nullable=True)
    academic_status = Column(
        Enum(StudentStatus),
        nullable=True,
    )
    class_name   = Column(Unicode(50),  nullable=True)
    program_name = Column(Unicode(200), nullable=True)

    parent_full_name = Column(Unicode(150), nullable=True)
    parent_phone     = Column(String(20),   nullable=True)
    parent_email     = Column(String(200),  nullable=True)
    medical_notes    = Column(UnicodeText,  nullable=True)

    is_active  = Column(Boolean,  nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<StudentBackup backup_id={self.backup_id} "
            f"student_code='{self.student_code}' "
            f"backed_up_at='{self.backed_up_at}' "
            f"reason='{self.backup_reason}'>"
        )

    @classmethod
    def from_student(
        cls,
        student: "Student",
        reason: Optional[str] = None,
    ) -> "StudentBackup":
        """
        Convenience factory – create a backup row from an existing Student.

        Usage:
            backup = StudentBackup.from_student(student, reason="pre_import")
            session.add(backup)
            await session.commit()
        """
        return cls(
            backup_reason=reason,
            id=student.id,
            student_code=student.student_code,
            full_name=student.full_name,
            date_of_birth=student.date_of_birth,
            gender=student.gender,
            national_id=student.national_id,
            email=student.email,
            phone_number=student.phone_number,
            address=student.address,
            enrollment_date=student.enrollment_date,
            academic_status=student.academic_status,
            class_name=student.class_name,
            program_name=student.program_name,
            parent_full_name=student.parent_full_name,
            parent_phone=student.parent_phone,
            parent_email=student.parent_email,
            medical_notes=student.medical_notes,
            is_active=student.is_active,
            created_at=student.created_at,
            updated_at=student.updated_at,
        )
