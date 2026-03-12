"""
Classroom entities – maps to tables in MSSQL.

Tables:
  - classrooms                  : lớp học (cơ bản / Cambridge)
  - student_class_enrollments   : học sinh đăng ký vào lớp (primary / supplementary)

Business rules:
  - class_type = 'standard'  : lớp cơ bản (chương trình Bộ GD&DT)
  - class_type = 'cambridge' : lớp nâng cao (Cambridge International)
  - Học sinh lớp standard có thể cross-enroll vào lớp cambridge và ngược lại
    thông qua enrollment_type = 'supplementary'.
  - Mỗi học sinh chỉ có đúng 1 enrollment 'primary' tại 1 thời điểm.
  - Số lượng enrollment 'supplementary' không giới hạn nhưng bị ràng buộc
    bởi max_capacity của lớp đó.
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
    ForeignKey,
    Integer,
    String,
    Unicode,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.modules.student.entity import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ClassType(str, enum.Enum):
    STANDARD  = "standard"   # Lớp cơ bản – chương trình Bộ GD&DT
    CAMBRIDGE = "cambridge"  # Lớp nâng cao – Cambridge International


class EnrollmentType(str, enum.Enum):
    PRIMARY       = "primary"       # Lớp chính (mỗi học sinh chỉ có 1 tại 1 thời điểm)
    SUPPLEMENTARY = "supplementary" # Lớp học thêm / cross-enrollment


class EnrollmentStatus(str, enum.Enum):
    ACTIVE      = "active"      # Đang học tại lớp này
    TRANSFERRED = "transferred" # Đã chuyển lớp
    WITHDRAWN   = "withdrawn"   # Rút khỏi lớp (tự nguyện / kỷ luật)
    COMPLETED   = "completed"   # Hoàn thành năm học tại lớp này


# ---------------------------------------------------------------------------
# Table: classrooms
# ---------------------------------------------------------------------------

class Classroom(Base):
    """
    Lớp học – đơn vị tổ chức học tập cơ bản.

    Columns:
        id                   – Auto-increment PK.
        class_code           – Mã lớp duy nhất (VD: '10A1-2024', 'CAM-10A-2024').
        class_name           – Tên hiển thị (VD: 'Lớp 10A1', 'Cambridge 10A').
        class_type           – 'standard' | 'cambridge'.
        academic_year        – Năm học (VD: '2024-2025').
        grade_level          – Khối lớp: 10 | 11 | 12.
        homeroom_teacher_id  – FK → teachers.id (giáo viên chủ nhiệm, nullable).
        max_capacity         – Sĩ số tối đa cho phép.
        room_number          – Phòng học được phân công.
        description          – Ghi chú thêm về lớp.
        is_active            – Soft-delete flag.
        created_at           – Auto timestamp on insert.
        updated_at           – Auto timestamp on update.
    """

    __tablename__ = "classrooms"

    id           = Column(Integer, primary_key=True, autoincrement=True, index=True)
    class_code   = Column(String(30),   unique=True, nullable=False, index=True)
    class_name   = Column(Unicode(100), nullable=False)
    class_type   = Column(
        Enum(ClassType),
        nullable=False,
        default=ClassType.STANDARD,
        index=True,
    )
    academic_year = Column(String(10),  nullable=False, index=True)  # VD: '2024-2025'
    grade_level   = Column(Integer,     nullable=False, index=True)  # 10 / 11 / 12

    # Giáo viên chủ nhiệm (nullable – lớp có thể chưa phân công GV)
    homeroom_teacher_id = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="NO ACTION"),
        nullable=True,
        index=True,
    )

    max_capacity = Column(Integer,      nullable=False, default=40)
    room_number  = Column(String(20),   nullable=True)
    description  = Column(Unicode(300), nullable=True)

    is_active  = Column(Boolean,  nullable=False, default=True,  index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────
    homeroom_teacher = relationship(
        "Teacher",
        foreign_keys=[homeroom_teacher_id],
        lazy="select",
    )
    enrollments = relationship(
        "StudentClassEnrollment",
        back_populates="classroom",
        lazy="select",
    )

    # ── Computed helper (không lưu DB – tính từ enrollments) ────────────
    @property
    def current_enrollment(self) -> int:
        """Số học sinh đang active trong lớp (primary + supplementary)."""
        return sum(
            1 for e in self.enrollments
            if e.is_active and e.status == EnrollmentStatus.ACTIVE
        )

    def __repr__(self) -> str:
        return (
            f"<Classroom id={self.id} code='{self.class_code}' "
            f"type='{self.class_type}' year='{self.academic_year}' "
            f"grade={self.grade_level}>"
        )


# ---------------------------------------------------------------------------
# Table: student_class_enrollments
# ---------------------------------------------------------------------------

class StudentClassEnrollment(Base):
    """
    Quan hệ học sinh – lớp học.

    Mỗi học sinh có đúng 1 enrollment PRIMARY tại 1 thời điểm (ràng buộc
    kiểm tra ở Service layer).
    Số lượng SUPPLEMENTARY không giới hạn (cross-enrollment giữa lớp
    cơ bản và Cambridge).

    Columns:
        id               – Auto-increment PK.
        student_id       – FK → students.id.
        classroom_id     – FK → classrooms.id.
        enrollment_type  – 'primary' | 'supplementary'.
        status           – Trạng thái hiện tại của enrollment.
        enrolled_date    – Ngày vào lớp.
        left_date        – Ngày rời lớp (NULL = đang học).
        notes            – Ghi chú (lý do chuyển lớp, rút khỏi lớp...).
        is_active        – Soft-delete flag.
        created_at       – Auto timestamp on insert.
        updated_at       – Auto timestamp on update.
    """

    __tablename__ = "student_class_enrollments"

    # Đảm bảo không duplicate cùng học sinh – lớp – enrollment_type đang active
    __table_args__ = (
        UniqueConstraint(
            "student_id", "classroom_id", "enrollment_type",
            name="uq_enrollment_student_class_type",
        ),
    )

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    student_id      = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    classroom_id    = Column(
        Integer,
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enrollment_type = Column(
        Enum(EnrollmentType),
        nullable=False,
        default=EnrollmentType.PRIMARY,
        index=True,
    )
    status = Column(
        Enum(EnrollmentStatus),
        nullable=False,
        default=EnrollmentStatus.ACTIVE,
        index=True,
    )
    enrolled_date = Column(Date,         nullable=False, default=func.current_date())
    left_date     = Column(Date,         nullable=True)   # NULL = đang học
    notes         = Column(Unicode(300), nullable=True)

    is_active  = Column(Boolean,  nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────
    student = relationship(
        "Student",
        foreign_keys=[student_id],
        lazy="select",
    )
    classroom = relationship(
        "Classroom",
        back_populates="enrollments",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<StudentClassEnrollment id={self.id} "
            f"student_id={self.student_id} classroom_id={self.classroom_id} "
            f"type='{self.enrollment_type}' status='{self.status}'>"
        )


# ---------------------------------------------------------------------------
# Valid enrollment status transitions
# ---------------------------------------------------------------------------

VALID_ENROLLMENT_STATUS_TRANSITIONS: dict[EnrollmentStatus, set[EnrollmentStatus]] = {
    EnrollmentStatus.ACTIVE: {
        EnrollmentStatus.TRANSFERRED,
        EnrollmentStatus.WITHDRAWN,
        EnrollmentStatus.COMPLETED,
    },
    EnrollmentStatus.TRANSFERRED: set(),  # Terminal
    EnrollmentStatus.WITHDRAWN:   set(),  # Terminal
    EnrollmentStatus.COMPLETED:   set(),  # Terminal
}
