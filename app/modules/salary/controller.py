"""
Salary Controller – FastAPI router.

Endpoints:
  SalaryGrade:
    POST   /salary/grades                      – Create grade
    GET    /salary/grades                      – List grades
    GET    /salary/grades/{grade_code}         – Get grade
    PATCH  /salary/grades/{grade_code}         – Update grade

  BonusPolicy:
    POST   /salary/bonus-policies              – Create policy
    GET    /salary/bonus-policies              – List policies
    GET    /salary/bonus-policies/{code}       – Get policy
    PATCH  /salary/bonus-policies/{code}       – Update policy

  Payroll:
    POST   /salary/payrolls                    – Create payroll
    GET    /salary/payrolls                    – List payrolls
    GET    /salary/payrolls/{id}               – Get payroll
    PATCH  /salary/payrolls/{id}               – Update payroll
    PATCH  /salary/payrolls/{id}/status        – Transition status
    POST   /salary/payrolls/{id}/bonuses       – Add bonus to payroll
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.response import APIResponse
from app.modules.salary.dto import (
    BonusPolicyCreateRequest,
    BonusPolicyListResponse,
    BonusPolicyResponse,
    BonusPolicyUpdateRequest,
    PayrollBonusDetailCreateRequest,
    PayrollCreateRequest,
    PayrollListResponse,
    PayrollQueryParams,
    PayrollResponse,
    PayrollStatusUpdateRequest,
    PayrollUpdateRequest,
    SalaryGradeCreateRequest,
    SalaryGradeListResponse,
    SalaryGradeResponse,
    SalaryGradeUpdateRequest,
)
from app.modules.salary.entity import PayrollStatus
from app.modules.salary.service import SalaryService

router = APIRouter()


def get_service(session: AsyncSession = Depends(get_async_session)) -> SalaryService:
    return SalaryService(session)


# ---------------------------------------------------------------------------
# SalaryGrade
# ---------------------------------------------------------------------------

@router.post("/grades", status_code=201, summary="Tạo ngạch lương mới")
async def create_salary_grade(
    data: SalaryGradeCreateRequest,
    service: SalaryService = Depends(get_service),
) -> APIResponse[SalaryGradeResponse]:
    result = await service.create_salary_grade(data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Salary Grade Created",
        detail=f"Salary grade '{result.grade_code}' created",
    )


@router.get("/grades", status_code=200, summary="Danh sách ngạch lương")
async def list_salary_grades(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    service: SalaryService = Depends(get_service),
) -> APIResponse[SalaryGradeListResponse]:
    result = await service.list_salary_grades(page, page_size, active_only)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} salary grade(s)",
    )


@router.get("/grades/{grade_code}", status_code=200, summary="Chi tiết ngạch lương")
async def get_salary_grade(
    grade_code: str,
    service: SalaryService = Depends(get_service),
) -> APIResponse[SalaryGradeResponse]:
    result = await service.get_salary_grade(grade_code)
    return APIResponse.success(data=result.model_dump())


@router.patch("/grades/{grade_code}", status_code=200, summary="Cập nhật ngạch lương")
async def update_salary_grade(
    grade_code: str,
    data: SalaryGradeUpdateRequest,
    service: SalaryService = Depends(get_service),
) -> APIResponse[SalaryGradeResponse]:
    result = await service.update_salary_grade(grade_code, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Salary grade '{grade_code}' updated",
    )


# ---------------------------------------------------------------------------
# BonusPolicy
# ---------------------------------------------------------------------------

@router.post("/bonus-policies", status_code=201, summary="Tạo chính sách thưởng")
async def create_bonus_policy(
    data: BonusPolicyCreateRequest,
    service: SalaryService = Depends(get_service),
) -> APIResponse[BonusPolicyResponse]:
    result = await service.create_bonus_policy(data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Bonus Policy Created",
        detail=f"Bonus policy '{result.policy_code}' created",
    )


@router.get("/bonus-policies", status_code=200, summary="Danh sách chính sách thưởng")
async def list_bonus_policies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    service: SalaryService = Depends(get_service),
) -> APIResponse[BonusPolicyListResponse]:
    result = await service.list_bonus_policies(page, page_size, active_only)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} bonus polic(ies)",
    )


@router.get("/bonus-policies/{policy_code}", status_code=200,
            summary="Chi tiết chính sách thưởng")
async def get_bonus_policy(
    policy_code: str,
    service: SalaryService = Depends(get_service),
) -> APIResponse[BonusPolicyResponse]:
    result = await service.get_bonus_policy(policy_code)
    return APIResponse.success(data=result.model_dump())


@router.patch("/bonus-policies/{policy_code}", status_code=200,
              summary="Cập nhật chính sách thưởng")
async def update_bonus_policy(
    policy_code: str,
    data: BonusPolicyUpdateRequest,
    service: SalaryService = Depends(get_service),
) -> APIResponse[BonusPolicyResponse]:
    result = await service.update_bonus_policy(policy_code, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Bonus policy '{policy_code}' updated",
    )


# ---------------------------------------------------------------------------
# Payroll
# ---------------------------------------------------------------------------

@router.post("/payrolls", status_code=201, summary="Tạo bảng lương tháng")
async def create_payroll(
    data: PayrollCreateRequest,
    service: SalaryService = Depends(get_service),
) -> APIResponse[PayrollResponse]:
    result = await service.create_payroll(data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Payroll Created",
        detail=f"Payroll for teacher {result.teacher_id} month {result.payroll_month} created",
    )


@router.get("/payrolls", status_code=200, summary="Danh sách bảng lương (có lọc)")
async def list_payrolls(
    teacher_id: Optional[int] = Query(None),
    status: Optional[PayrollStatus] = Query(None),
    month_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    month_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: SalaryService = Depends(get_service),
) -> APIResponse[PayrollListResponse]:
    from datetime import date
    params = PayrollQueryParams(
        teacher_id=teacher_id,
        status=status,
        month_from=date.fromisoformat(month_from) if month_from else None,
        month_to=date.fromisoformat(month_to) if month_to else None,
        page=page,
        page_size=page_size,
    )
    result = await service.list_payrolls(params)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} payroll(s)",
    )


@router.get("/payrolls/{payroll_id}", status_code=200, summary="Chi tiết bảng lương")
async def get_payroll(
    payroll_id: int,
    service: SalaryService = Depends(get_service),
) -> APIResponse[PayrollResponse]:
    result = await service.get_payroll(payroll_id)
    return APIResponse.success(data=result.model_dump())


@router.patch("/payrolls/{payroll_id}", status_code=200,
              summary="Cập nhật bảng lương (chỉ khi chưa paid)")
async def update_payroll(
    payroll_id: int,
    data: PayrollUpdateRequest,
    service: SalaryService = Depends(get_service),
) -> APIResponse[PayrollResponse]:
    result = await service.update_payroll(payroll_id, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Payroll {payroll_id} updated. Net salary: {result.net_salary}",
    )


@router.patch("/payrolls/{payroll_id}/status", status_code=200,
              summary="Duyệt / thanh toán bảng lương (draft→confirmed→paid)")
async def update_payroll_status(
    payroll_id: int,
    data: PayrollStatusUpdateRequest,
    service: SalaryService = Depends(get_service),
) -> APIResponse[PayrollResponse]:
    result = await service.update_payroll_status(payroll_id, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Payroll {payroll_id} status → '{data.new_status.value}'",
    )


@router.post("/payrolls/{payroll_id}/bonuses", status_code=201,
             summary="Thêm khoản thưởng vào bảng lương")
async def add_bonus_to_payroll(
    payroll_id: int,
    data: PayrollBonusDetailCreateRequest,
    service: SalaryService = Depends(get_service),
) -> APIResponse[PayrollResponse]:
    result = await service.add_bonus_to_payroll(payroll_id, data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Bonus Added",
        detail=f"Bonus added to payroll {payroll_id}. New net: {result.net_salary}",
    )
