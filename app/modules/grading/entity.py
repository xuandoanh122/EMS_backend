"""
Grading entities – maps to tables in MSSQL.

Tables:
  - subjects              : danh mục môn học
  - class_subjects        : phân công môn học – lớp – giáo viên
  - grade_components      : cấu hình thành phần điểm (VD: miệng 10%, 15p 15%, 1 tiết 25%, cuối kỳ 50%)
  - student_grades        : điểm từng cột của từng học sinh
  - grade_audit_log       : lịch sử chỉnh sửa điểm (ai sửa, từ bao nhiêu, lý do)
  - semester_averages     : điểm trung bình học kỳ (materialized, tính lại khi có thay đổi)

Business rules:
  - Chỉ giáo viên được phân công môn đó tại lớp đó mới được nhập điểm.
  - Mọi chỉnh sửa điểm phải ghi vào grade_audit_log kèm lý do bắt buộc.
  - Tổng weight_percent của các grade_components trong 1 class_subject = 100.
  - semester_averages được tính lại mỗi khi có insert/update trên student_grades.
  - Xếp loại: >= 8.0 = 'Gioi' | >= 6.5 = 'Kha' | >= 5.0 = 'Trung binh' | < 5.0 = 'Yeu'
"""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
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

class SubjectType(str, enum.Enum):
    STANDARD  = "standard"   # Môn học chương trình chuẩn Bộ GD
    CAMBRIDGE = "cambridge"  # Môn học Cambridge International


class AcademicRank(str, enum.Enum):
    GIOI        = "Gioi"        # >= 8.0
    KHA         = "Kha"         # >= 6.5
    TRUNG_BINH  = "Trung binh"  # >= 5.0
    YEU         = "Yeu"         # < 5.0


def _calc_rank(average_score: float) -> AcademicRank:
    """Tính xếp loại học lực từ điểm trung bình."""
    if average_score >= 8.0:
        return AcademicRank.GIOI
    elif average_score >= 6.5:
        return AcademicRank.KHA
    elif average_score >= 5.0:
        return AcademicRank.TRUNG_BINH
    else:
        return AcademicRank.YEU


# ---------------------------------------------------------------------------
# Table: subjects – Danh mục môn học
# ---------------------------------------------------------------------------

class Subject(Base):
    """
    Môn học.

    Columns:
        id            – Auto-increment PK.
        subject_code  – Mã môn duy nhất (VD: 'TOAN', 'VAN', 'CAM-MATH').
        subject_name  – Tên môn (VD: 'Toán học', 'Cambridge Mathematics').
        subject_type  – 'standard' | 'cambridge'.
        credits       – Số tín chỉ / hệ số (dùng để tính điểm tổng kết).
        description   – Mô tả môn học.
        is_active     – Soft-delete flag.
        created_at / updated_at.
    """

    __tablename__ = "subjects"

    id           = Column(Integer, primary_key=True, autoincrement=True, index=True)
    subject_code = Column(String(20),   unique=True, nullable=False, index=True)
    subject_name = Column(Unicode(100), nullable=False)
    subject_type = Column(
        Enum(SubjectType),
        nullable=False,
        default=SubjectType.STANDARD,
        index=True,
    )
    credits     = Column(Integer,      nullable=False, default=1)
    description = Column(Unicode(300), nullable=True)

    is_active  = Column(Boolean,  nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────
    class_subjects = relationship("ClassSubject", back_populates="subject", lazy="select")

    def __repr__(self) -> str:
        return (
            f"<Subject id={self.id} code='{self.subject_code}' "
            f"name='{self.subject_name}' type='{self.subject_type}'>"
        )


# ---------------------------------------------------------------------------
# Table: class_subjects – Phân công môn học – lớp – giáo viên
# ---------------------------------------------------------------------------

class ClassSubject(Base):
    """
    Liên kết lớp học – môn học – giáo viên phụ trách, theo từng học kỳ/năm học.

    Columns:
        id             – Auto-increment PK.
        classroom_id   – FK → classrooms.id.
        subject_id     – FK → subjects.id.
        teacher_id     – FK → teachers.id (giáo viên dạy môn này tại lớp này).
        semester       – Học kỳ: 1 | 2.
        academic_year  – Năm học (VD: '2024-2025').
        is_active      – Soft-delete flag.
        created_at / updated_at.
    """

    __tablename__ = "class_subjects"

    # Mỗi (lớp, môn, học kỳ, năm học) chỉ có 1 record duy nhất
    __table_args__ = (
        UniqueConstraint(
            "classroom_id", "subject_id", "semester", "academic_year",
            name="uq_class_subject_semester",
        ),
    )

    id           = Column(Integer, primary_key=True, autoincrement=True, index=True)
    classroom_id = Column(
        Integer,
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id   = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    teacher_id   = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="NO ACTION"),
        nullable=True,   # Có thể chưa phân công giáo viên
        index=True,
    )
    semester      = Column(Integer,     nullable=False, index=True)   # 1 | 2
    academic_year = Column(String(10),  nullable=False, index=True)   # '2024-2025'

    is_active  = Column(Boolean,  nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────
    classroom        = relationship("Classroom",       lazy="select")
    subject          = relationship("Subject",         back_populates="class_subjects", lazy="select")
    teacher          = relationship("Teacher",         foreign_keys=[teacher_id], lazy="select")
    grade_components = relationship(
        "GradeComponent",
        back_populates="class_subject",
        cascade="all, delete-orphan",
        lazy="select",
    )
    student_grades   = relationship(
        "StudentGrade",
        back_populates="class_subject",
        lazy="select",
    )
    semester_averages = relationship(
        "SemesterAverage",
        back_populates="class_subject",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<ClassSubject id={self.id} classroom_id={self.classroom_id} "
            f"subject_id={self.subject_id} teacher_id={self.teacher_id} "
            f"semester={self.semester} year='{self.academic_year}'>"
        )


# ---------------------------------------------------------------------------
# Table: grade_components – Cấu hình thành phần điểm
# ---------------------------------------------------------------------------

class GradeComponent(Base):
    """
    Thành phần điểm của một môn học tại một lớp.

    VD cấu hình điểm Toán lớp 10A1 HK1:
      - Kiểm tra miệng:  10%  (min 2 cột)
      - Kiểm tra 15 phút: 15% (min 2 cột)
      - Kiểm tra 1 tiết:  25% (min 1 cột)
      - Thi cuối kỳ:      50% (min 1 cột)
      → Tổng = 100%

    Columns:
        id                – Auto-increment PK.
        class_subject_id  – FK → class_subjects.id.
        component_name    – Tên thành phần (VD: 'Kiểm tra miệng').
        weight_percent    – Hệ số % (tổng các thành phần trong 1 class_subject = 100).
        min_count         – Số cột tối thiểu bắt buộc phải có.
        is_active         – Soft flag.
        created_at / updated_at.
    """

    __tablename__ = "grade_components"

    id               = Column(Integer, primary_key=True, autoincrement=True, index=True)
    class_subject_id = Column(
        Integer,
        ForeignKey("class_subjects.id", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    component_name = Column(Unicode(100), nullable=False)
    weight_percent = Column(Integer, nullable=False)   # 1–100; tổng = 100
    min_count      = Column(Integer, nullable=False, default=1)

    is_active  = Column(Boolean,  nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────
    class_subject  = relationship("ClassSubject",  back_populates="grade_components", lazy="select")
    student_grades = relationship("StudentGrade",  back_populates="grade_component",  lazy="select")

    def __repr__(self) -> str:
        return (
            f"<GradeComponent id={self.id} class_subject_id={self.class_subject_id} "
            f"name='{self.component_name}' weight={self.weight_percent}%>"
        )


# ---------------------------------------------------------------------------
# Table: student_grades – Điểm từng học sinh
# ---------------------------------------------------------------------------

class StudentGrade(Base):
    """
    Một cột điểm của một học sinh trong một thành phần điểm.

    Columns:
        id                  – Auto-increment PK.
        student_id          – FK → students.id.
        class_subject_id    – FK → class_subjects.id.
        grade_component_id  – FK → grade_components.id.
        score               – Điểm số (0.00 – 10.00).
        exam_date           – Ngày kiểm tra / thi.
        entered_by          – FK → teachers.id (giáo viên nhập điểm).
        entered_at          – Thời điểm nhập.
        last_modified_by    – FK → teachers.id (người sửa lần cuối, NULL nếu chưa sửa).
        last_modified_at    – Thời điểm sửa lần cuối.
        is_active           – Soft-delete (False = hủy cột điểm sai, không xóa cứng).
        created_at / updated_at.
    """

    __tablename__ = "student_grades"

    id                 = Column(Integer, primary_key=True, autoincrement=True, index=True)
    student_id         = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_subject_id   = Column(
        Integer,
        ForeignKey("class_subjects.id", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    grade_component_id = Column(
        Integer,
        ForeignKey("grade_components.id", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    score      = Column(Numeric(4, 2), nullable=False)   # 0.00 – 10.00
    exam_date  = Column(Date,          nullable=True)

    entered_by       = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="NO ACTION"),
        nullable=True,
        index=True,
    )
    entered_at       = Column(DateTime, nullable=False, server_default=func.now())
    last_modified_by = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="NO ACTION"),
        nullable=True,
    )
    last_modified_at = Column(DateTime, nullable=True)

    is_active  = Column(Boolean,  nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────
    student         = relationship("Student",        foreign_keys=[student_id],   lazy="select")
    class_subject   = relationship("ClassSubject",   back_populates="student_grades", lazy="select")
    grade_component = relationship("GradeComponent", back_populates="student_grades", lazy="select")
    entered_teacher = relationship("Teacher",        foreign_keys=[entered_by],   lazy="select")
    modifier_teacher = relationship("Teacher",       foreign_keys=[last_modified_by], lazy="select")
    audit_logs      = relationship(
        "GradeAuditLog",
        back_populates="student_grade",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<StudentGrade id={self.id} student_id={self.student_id} "
            f"component_id={self.grade_component_id} score={self.score}>"
        )


# ---------------------------------------------------------------------------
# Table: grade_audit_log – Lịch sử chỉnh sửa điểm
# ---------------------------------------------------------------------------

class GradeAuditLog(Base):
    """
    Ghi lại mọi thay đổi điểm số (ai sửa, từ bao nhiêu → bao nhiêu, lý do).

    Columns:
        id                – Auto-increment PK.
        student_grade_id  – FK → student_grades.id.
        old_score         – Điểm trước khi sửa.
        new_score         – Điểm sau khi sửa.
        changed_by        – FK → teachers.id.
        changed_at        – Thời điểm sửa.
        reason            – Lý do bắt buộc phải điền.
    """

    __tablename__ = "grade_audit_log"

    id               = Column(Integer, primary_key=True, autoincrement=True, index=True)
    student_grade_id = Column(
        Integer,
        ForeignKey("student_grades.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_score  = Column(Numeric(4, 2), nullable=False)
    new_score  = Column(Numeric(4, 2), nullable=False)
    changed_by = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="NO ACTION"),
        nullable=True,
        index=True,
    )
    changed_at = Column(DateTime, nullable=False, server_default=func.now())
    reason     = Column(Unicode(300), nullable=False)   # Bắt buộc

    # ── Relationships ────────────────────────────────────────────────────
    student_grade = relationship("StudentGrade", back_populates="audit_logs", lazy="select")
    changed_by_teacher = relationship("Teacher", foreign_keys=[changed_by], lazy="select")

    def __repr__(self) -> str:
        return (
            f"<GradeAuditLog id={self.id} grade_id={self.student_grade_id} "
            f"{self.old_score} -> {self.new_score} by teacher_id={self.changed_by}>"
        )


# ---------------------------------------------------------------------------
# Table: semester_averages – Điểm trung bình học kỳ
# ---------------------------------------------------------------------------

class SemesterAverage(Base):
    """
    Điểm trung bình học kỳ của từng học sinh – từng môn (materialized).

    Được tính lại mỗi khi có thay đổi trên student_grades (Service layer).
    Dùng trực tiếp cho báo cáo / biểu đồ mà không cần tính lại từ đầu.

    Columns:
        id               – Auto-increment PK.
        student_id       – FK → students.id.
        class_subject_id – FK → class_subjects.id.
        semester         – Học kỳ: 1 | 2.
        academic_year    – Năm học.
        average_score    – Điểm trung bình (đã áp dụng weight_percent).
        rank             – Xếp loại học lực: Gioi | Kha | Trung binh | Yeu.
        calculated_at    – Thời điểm tính gần nhất.
    """

    __tablename__ = "semester_averages"

    __table_args__ = (
        UniqueConstraint(
            "student_id", "class_subject_id",
            name="uq_semester_avg_student_subject",
        ),
    )

    id               = Column(Integer, primary_key=True, autoincrement=True, index=True)
    student_id       = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_subject_id = Column(
        Integer,
        ForeignKey("class_subjects.id", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    semester      = Column(Integer,    nullable=False)
    academic_year = Column(String(10), nullable=False)
    average_score = Column(Numeric(4, 2), nullable=False, default=0)
    rank          = Column(
        Enum(AcademicRank),
        nullable=False,
        default=AcademicRank.YEU,
    )
    calculated_at = Column(DateTime, nullable=False, server_default=func.now())

    # ── Relationships ────────────────────────────────────────────────────
    student       = relationship("Student",      foreign_keys=[student_id],   lazy="select")
    class_subject = relationship("ClassSubject", back_populates="semester_averages", lazy="select")

    def __repr__(self) -> str:
        return (
            f"<SemesterAverage id={self.id} student_id={self.student_id} "
            f"class_subject_id={self.class_subject_id} avg={self.average_score} "
            f"rank='{self.rank}'>"
        )
