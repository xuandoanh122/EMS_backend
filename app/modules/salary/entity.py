"""
Salary (Payroll) entities – maps to tables in MSSQL.

Tables:
  - salary_grades           : bảng ngạch lương (bằng cấp × mốc thâm niên)
  - bonus_policies          : chính sách thưởng
  - monthly_payroll         : bảng lương tháng của từng giáo viên
  - payroll_bonus_details   : chi tiết các khoản thưởng trong 1 bảng lương

Business rules:
  - Ngạch lương xác định bởi (qualification_level × experience_tier).
  - Thâm niên được tính tự động từ teachers.join_date vào thời điểm
    generate bảng lương.
  - Mốc thâm niên: < 3 năm | 3–6 năm | 6–9 năm | > 9 năm.
  - net_salary = base_salary + teaching_allowance + total_bonus - deductions.
  - Luồng trạng thái bảng lương: draft → confirmed → paid.
"""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
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

class QualificationLevel(str, enum.Enum):
    CAO_DANG  = "cao_dang"   # Cao đẳng
    DAI_HOC   = "dai_hoc"    # Đại học
    THAC_SI   = "thac_si"    # Thạc sĩ
    TIEN_SI   = "tien_si"    # Tiến sĩ


class ExperienceTier(str, enum.Enum):
    UNDER_3Y  = "under_3y"   # Dưới 3 năm
    Y3_TO_6   = "3_to_6y"    # 3 đến dưới 6 năm
    Y6_TO_9   = "6_to_9y"    # 6 đến dưới 9 năm
    OVER_9Y   = "over_9y"    # Từ 9 năm trở lên


class BonusType(str, enum.Enum):
    FIXED      = "fixed"      # Số tiền cố định (VNĐ)
    PERCENTAGE = "percentage" # % trên lương cơ bản


class PayrollStatus(str, enum.Enum):
    DRAFT     = "draft"      # Bảng lương tạm tính, chưa duyệt
    CONFIRMED = "confirmed"  # Kế toán đã duyệt
    PAID      = "paid"       # Đã thanh toán


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _experience_tier_from_years(years: float) -> ExperienceTier:
    """
    Tính mốc thâm niên từ số năm kinh nghiệm.
    Dùng trong Service khi generate bảng lương.
    """
    if years < 3:
        return ExperienceTier.UNDER_3Y
    elif years < 6:
        return ExperienceTier.Y3_TO_6
    elif years < 9:
        return ExperienceTier.Y6_TO_9
    else:
        return ExperienceTier.OVER_9Y


# ---------------------------------------------------------------------------
# Table: salary_grades – Bảng ngạch lương
# ---------------------------------------------------------------------------

class SalaryGrade(Base):
    """
    Ngạch lương – xác định mức lương cơ bản theo bằng cấp và thâm niên.

    Columns:
        id                  – Auto-increment PK.
        grade_code          – Mã ngạch duy nhất (VD: 'THAC_SI_3_6NAM').
        qualification_level – Bằng cấp: cao_dang | dai_hoc | thac_si | tien_si.
        experience_tier     – Mốc thâm niên: under_3y | 3_to_6y | 6_to_9y | over_9y.
        base_salary         – Lương cơ bản (VNĐ/tháng).
        hourly_rate         – Đơn giá/tiết dạy (VNĐ).
        effective_from      – Áp dụng từ ngày.
        effective_to        – Hết hiệu lực (NULL = đang áp dụng).
        description         – Ghi chú.
        is_active           – Soft flag.
        created_at          – Auto timestamp.
        updated_at          – Auto timestamp.
    """

    __tablename__ = "salary_grades"

    # Mỗi tổ hợp (bằng cấp, mốc thâm niên) chỉ có 1 mức lương đang hiệu lực
    __table_args__ = (
        UniqueConstraint(
            "qualification_level", "experience_tier", "effective_from",
            name="uq_salary_grade_combo",
        ),
    )

    id                  = Column(Integer, primary_key=True, autoincrement=True, index=True)
    grade_code          = Column(String(30),   unique=True, nullable=False, index=True)
    qualification_level = Column(
        Enum(QualificationLevel),
        nullable=False,
        index=True,
    )
    experience_tier     = Column(
        Enum(ExperienceTier),
        nullable=False,
        index=True,
    )
    base_salary  = Column(Numeric(15, 2), nullable=False)   # VNĐ/tháng
    hourly_rate  = Column(Numeric(10, 2), nullable=False)   # VNĐ/tiết

    effective_from = Column(Date, nullable=False)
    effective_to   = Column(Date, nullable=True)  # NULL = đang hiệu lực

    description = Column(Unicode(300), nullable=True)
    is_active   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime, nullable=False, server_default=func.now())
    updated_at  = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────
    payrolls = relationship("MonthlyPayroll", back_populates="salary_grade", lazy="select")

    def __repr__(self) -> str:
        return (
            f"<SalaryGrade id={self.id} code='{self.grade_code}' "
            f"qual='{self.qualification_level}' tier='{self.experience_tier}' "
            f"base={self.base_salary}>"
        )


# ---------------------------------------------------------------------------
# Table: bonus_policies – Chính sách thưởng
# ---------------------------------------------------------------------------

class BonusPolicy(Base):
    """
    Chính sách thưởng – định nghĩa các loại thưởng và cách tính.

    Các loại thưởng điển hình:
      - Thưởng đạt mốc thâm niên 3/6/9 năm (fixed)
      - Thưởng cuối năm theo xếp loại KPI: Xuất sắc 150% / Tốt 100% / Khá 50%
      - Thưởng lớp Cambridge đạt tỷ lệ pass cao (fixed)
      - Thưởng tiết dạy ngoài giờ / dạy thay (fixed per tiết)

    Columns:
        id                    – Auto-increment PK.
        policy_code           – Mã chính sách duy nhất.
        policy_name           – Tên chính sách (hiển thị).
        bonus_type            – 'fixed' | 'percentage'.
        bonus_value           – Giá trị (VNĐ nếu fixed, % nếu percentage).
        condition_description – Mô tả điều kiện áp dụng.
        is_active             – Soft flag.
        created_at / updated_at.
    """

    __tablename__ = "bonus_policies"

    id          = Column(Integer, primary_key=True, autoincrement=True, index=True)
    policy_code = Column(String(30), unique=True, nullable=False, index=True)
    policy_name = Column(Unicode(200), nullable=False)
    bonus_type  = Column(
        Enum(BonusType),
        nullable=False,
        default=BonusType.FIXED,
    )
    bonus_value           = Column(Numeric(15, 2), nullable=False)
    condition_description = Column(Unicode(500),   nullable=True)

    is_active  = Column(Boolean,  nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────
    bonus_details = relationship(
        "PayrollBonusDetail",
        back_populates="bonus_policy",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<BonusPolicy id={self.id} code='{self.policy_code}' "
            f"type='{self.bonus_type}' value={self.bonus_value}>"
        )


# ---------------------------------------------------------------------------
# Table: monthly_payroll – Bảng lương tháng
# ---------------------------------------------------------------------------

class MonthlyPayroll(Base):
    """
    Bảng lương tháng của một giáo viên.

    Công thức:
        net_salary = base_salary + teaching_allowance + total_bonus - deductions

    Luồng trạng thái:
        draft  →  confirmed  →  paid
          (tạo tự động)  (kế toán duyệt)  (đã thanh toán)

    Columns:
        id                      – Auto-increment PK.
        teacher_id              – FK → teachers.id.
        salary_grade_id         – FK → salary_grades.id (ngạch áp dụng tháng này).
        payroll_month           – Tháng lương (lưu ngày 1 của tháng, VD: 2024-09-01).
        work_days_standard      – Số ngày công chuẩn trong tháng (VD: 22).
        work_days_actual        – Số ngày thực tế có mặt.
        teaching_hours_standard – Số tiết chuẩn theo hợp đồng/tháng.
        teaching_hours_actual   – Số tiết thực dạy trong tháng.
        base_salary             – Lương cơ bản (copy từ salary_grade tại thời điểm tính).
        teaching_allowance      – Phụ cấp tiết dạy vượt chuẩn.
        total_bonus             – Tổng tất cả khoản thưởng tháng này.
        deductions              – Tổng khấu trừ (nghỉ không phép, BHXH...).
        net_salary              – Thực lãnh.
        status                  – 'draft' | 'confirmed' | 'paid'.
        confirmed_by            – FK → teachers.id (kế toán/admin duyệt).
        confirmed_at            – Thời điểm duyệt.
        paid_at                 – Thời điểm thanh toán.
        notes                   – Ghi chú kế toán.
        created_at / updated_at.
    """

    __tablename__ = "monthly_payroll"

    # Mỗi giáo viên chỉ có 1 bảng lương / tháng
    __table_args__ = (
        UniqueConstraint(
            "teacher_id", "payroll_month",
            name="uq_payroll_teacher_month",
        ),
    )

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    teacher_id      = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    salary_grade_id = Column(
        Integer,
        ForeignKey("salary_grades.id", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    payroll_month = Column(Date, nullable=False, index=True)  # Lưu 2024-09-01

    # Chấm công
    work_days_standard = Column(Integer, nullable=False, default=22)
    work_days_actual   = Column(Integer, nullable=False, default=0)

    # Tiết dạy
    teaching_hours_standard = Column(Integer, nullable=False, default=0)
    teaching_hours_actual   = Column(Integer, nullable=False, default=0)

    # Các khoản lương (VNĐ)
    base_salary        = Column(Numeric(15, 2), nullable=False, default=0)
    teaching_allowance = Column(Numeric(15, 2), nullable=False, default=0)
    total_bonus        = Column(Numeric(15, 2), nullable=False, default=0)
    deductions         = Column(Numeric(15, 2), nullable=False, default=0)
    net_salary         = Column(Numeric(15, 2), nullable=False, default=0)

    # Trạng thái
    status = Column(
        Enum(PayrollStatus),
        nullable=False,
        default=PayrollStatus.DRAFT,
        index=True,
    )
    confirmed_by = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="NO ACTION"),
        nullable=True,
    )
    confirmed_at = Column(DateTime, nullable=True)
    paid_at      = Column(DateTime, nullable=True)
    notes        = Column(Unicode(500), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────
    teacher = relationship(
        "Teacher",
        foreign_keys=[teacher_id],
        lazy="select",
    )
    confirmer = relationship(
        "Teacher",
        foreign_keys=[confirmed_by],
        lazy="select",
    )
    salary_grade  = relationship("SalaryGrade",  back_populates="payrolls", lazy="select")
    bonus_details = relationship(
        "PayrollBonusDetail",
        back_populates="payroll",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<MonthlyPayroll id={self.id} teacher_id={self.teacher_id} "
            f"month='{self.payroll_month}' net={self.net_salary} "
            f"status='{self.status}'>"
        )


# ---------------------------------------------------------------------------
# Table: payroll_bonus_details – Chi tiết khoản thưởng trong 1 bảng lương
# ---------------------------------------------------------------------------

class PayrollBonusDetail(Base):
    """
    Chi tiết từng khoản thưởng được áp dụng cho một bảng lương.

    Columns:
        id               – Auto-increment PK.
        payroll_id       – FK → monthly_payroll.id.
        bonus_policy_id  – FK → bonus_policies.id.
        amount           – Số tiền thưởng thực tế (đã tính từ policy).
        note             – Ghi chú cụ thể (VD: 'KPI Xuất sắc Q3/2024').
        created_at       – Auto timestamp.
    """

    __tablename__ = "payroll_bonus_details"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    payroll_id      = Column(
        Integer,
        ForeignKey("monthly_payroll.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bonus_policy_id = Column(
        Integer,
        ForeignKey("bonus_policies.id", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    amount     = Column(Numeric(15, 2), nullable=False)
    note       = Column(Unicode(300),  nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # ── Relationships ────────────────────────────────────────────────────
    payroll      = relationship("MonthlyPayroll",  back_populates="bonus_details", lazy="select")
    bonus_policy = relationship("BonusPolicy",     back_populates="bonus_details", lazy="select")

    def __repr__(self) -> str:
        return (
            f"<PayrollBonusDetail id={self.id} payroll_id={self.payroll_id} "
            f"policy_id={self.bonus_policy_id} amount={self.amount}>"
        )


# ---------------------------------------------------------------------------
# Valid payroll status transitions
# ---------------------------------------------------------------------------

VALID_PAYROLL_STATUS_TRANSITIONS: dict[PayrollStatus, set[PayrollStatus]] = {
    PayrollStatus.DRAFT:     {PayrollStatus.CONFIRMED},
    PayrollStatus.CONFIRMED: {PayrollStatus.PAID, PayrollStatus.DRAFT},  # Có thể hoàn về draft nếu sai
    PayrollStatus.PAID:      set(),  # Terminal – không thể hoàn tác
}
