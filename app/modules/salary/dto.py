"""
Salary / Payroll DTOs – Pydantic schemas.

Covers:
  - SalaryGrade CRUD
  - BonusPolicy CRUD
  - MonthlyPayroll CRUD + status transition
  - PayrollBonusDetail
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.salary.entity import (
    BonusType,
    ExperienceTier,
    PayrollStatus,
    QualificationLevel,
)


# ---------------------------------------------------------------------------
# SalaryGrade
# ---------------------------------------------------------------------------

class SalaryGradeCreateRequest(BaseModel):
    grade_code: str = Field(..., min_length=1, max_length=30)
    qualification_level: QualificationLevel
    experience_tier: ExperienceTier
    base_salary: Decimal = Field(..., ge=0, description="Lương cơ bản VNĐ/tháng")
    hourly_rate: Decimal = Field(..., ge=0, description="Đơn giá VNĐ/tiết")
    effective_from: date
    effective_to: Optional[date] = None
    description: Optional[str] = Field(None, max_length=300)

    class Config:
        json_schema_extra = {
            "example": {
                "grade_code": "THAC_SI_3_6NAM",
                "qualification_level": "thac_si",
                "experience_tier": "3_to_6y",
                "base_salary": 8500000,
                "hourly_rate": 85000,
                "effective_from": "2024-01-01",
            }
        }


class SalaryGradeUpdateRequest(BaseModel):
    base_salary: Optional[Decimal] = Field(None, ge=0)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    effective_to: Optional[date] = None
    description: Optional[str] = Field(None, max_length=300)
    is_active: Optional[bool] = None


class SalaryGradeResponse(BaseModel):
    id: int
    grade_code: str
    qualification_level: QualificationLevel
    experience_tier: ExperienceTier
    base_salary: Decimal
    hourly_rate: Decimal
    effective_from: date
    effective_to: Optional[date]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SalaryGradeListResponse(BaseModel):
    items: List[SalaryGradeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# BonusPolicy
# ---------------------------------------------------------------------------

class BonusPolicyCreateRequest(BaseModel):
    policy_code: str = Field(..., min_length=1, max_length=30)
    policy_name: str = Field(..., min_length=1, max_length=200)
    bonus_type: BonusType = Field(default=BonusType.FIXED)
    bonus_value: Decimal = Field(..., ge=0)
    condition_description: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "policy_code": "THUONG_THAM_NIEN_3NAM",
                "policy_name": "Thưởng đạt mốc 3 năm thâm niên",
                "bonus_type": "fixed",
                "bonus_value": 500000,
                "condition_description": "Áp dụng khi giáo viên đạt đúng 3 năm công tác",
            }
        }


class BonusPolicyUpdateRequest(BaseModel):
    policy_name: Optional[str] = Field(None, max_length=200)
    bonus_type: Optional[BonusType] = None
    bonus_value: Optional[Decimal] = Field(None, ge=0)
    condition_description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class BonusPolicyResponse(BaseModel):
    id: int
    policy_code: str
    policy_name: str
    bonus_type: BonusType
    bonus_value: Decimal
    condition_description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BonusPolicyListResponse(BaseModel):
    items: List[BonusPolicyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# PayrollBonusDetail (sub-resource)
# ---------------------------------------------------------------------------

class PayrollBonusDetailCreateRequest(BaseModel):
    bonus_policy_id: int
    amount: Decimal = Field(..., ge=0)
    note: Optional[str] = Field(None, max_length=300)


class PayrollBonusDetailResponse(BaseModel):
    id: int
    payroll_id: int
    bonus_policy_id: int
    amount: Decimal
    note: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# MonthlyPayroll
# ---------------------------------------------------------------------------

class PayrollCreateRequest(BaseModel):
    teacher_id: int
    salary_grade_id: int
    payroll_month: date = Field(..., description="Lưu ngày 1 của tháng, VD: 2024-09-01")
    work_days_standard: int = Field(default=22, ge=1, le=31)
    work_days_actual: int = Field(default=0, ge=0, le=31)
    teaching_hours_standard: int = Field(default=0, ge=0)
    teaching_hours_actual: int = Field(default=0, ge=0)
    base_salary: Decimal = Field(default=Decimal("0"), ge=0)
    teaching_allowance: Decimal = Field(default=Decimal("0"), ge=0)
    deductions: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = Field(None, max_length=500)
    bonus_details: List[PayrollBonusDetailCreateRequest] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "teacher_id": 1,
                "salary_grade_id": 2,
                "payroll_month": "2024-09-01",
                "work_days_standard": 22,
                "work_days_actual": 21,
                "teaching_hours_standard": 80,
                "teaching_hours_actual": 90,
                "base_salary": 8500000,
                "teaching_allowance": 850000,
                "deductions": 0,
                "bonus_details": [{"bonus_policy_id": 1, "amount": 500000, "note": "Thưởng thâm niên"}],
            }
        }


class PayrollUpdateRequest(BaseModel):
    work_days_actual: Optional[int] = Field(None, ge=0, le=31)
    teaching_hours_actual: Optional[int] = Field(None, ge=0)
    teaching_allowance: Optional[Decimal] = Field(None, ge=0)
    deductions: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class PayrollStatusUpdateRequest(BaseModel):
    new_status: PayrollStatus
    confirmed_by: Optional[int] = Field(None, description="ID giáo viên/kế toán duyệt")
    notes: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {"new_status": "confirmed", "confirmed_by": 5, "notes": "Đã kiểm tra, duyệt chi"}
        }


class PayrollResponse(BaseModel):
    id: int
    teacher_id: int
    salary_grade_id: int
    payroll_month: date
    work_days_standard: int
    work_days_actual: int
    teaching_hours_standard: int
    teaching_hours_actual: int
    base_salary: Decimal
    teaching_allowance: Decimal
    total_bonus: Decimal
    deductions: Decimal
    net_salary: Decimal
    status: PayrollStatus
    confirmed_by: Optional[int]
    confirmed_at: Optional[datetime]
    paid_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    bonus_details: List[PayrollBonusDetailResponse] = []

    model_config = {"from_attributes": True}


class PayrollListResponse(BaseModel):
    items: List[PayrollResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PayrollQueryParams(BaseModel):
    teacher_id: Optional[int] = None
    status: Optional[PayrollStatus] = None
    month_from: Optional[date] = None
    month_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
