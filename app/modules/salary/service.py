"""
Salary Service – business logic layer.
"""

import math
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.salary import (
    BonusPolicyAlreadyExistsException,
    BonusPolicyNotFoundException,
    InvalidPayrollTransitionException,
    PayrollAlreadyExistsException,
    PayrollLockedEception,
    PayrollNotFoundException,
    SalaryGradeAlreadyExistsException,
    SalaryGradeNotFoundException,
)
from app.modules.salary.dto import (
    BonusPolicyCreateRequest,
    BonusPolicyListResponse,
    BonusPolicyResponse,
    BonusPolicyUpdateRequest,
    PayrollBonusDetailCreateRequest,
    PayrollBonusDetailResponse,
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
from app.modules.salary.entity import (
    BonusPolicy,
    MonthlyPayroll,
    PayrollBonusDetail,
    PayrollStatus,
    SalaryGrade,
    VALID_PAYROLL_STATUS_TRANSITIONS,
)
from app.modules.salary.repository import SalaryRepository


class SalaryService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SalaryRepository(session)

    # ------------------------------------------------------------------
    # SalaryGrade
    # ------------------------------------------------------------------

    async def create_salary_grade(self, data: SalaryGradeCreateRequest) -> SalaryGradeResponse:
        existing = await self._repo.get_salary_grade_by_code(data.grade_code)
        if existing:
            raise SalaryGradeAlreadyExistsException(identifier=data.grade_code)
        obj = SalaryGrade(
            grade_code=data.grade_code,
            qualification_level=data.qualification_level,
            experience_tier=data.experience_tier,
            base_salary=data.base_salary,
            hourly_rate=data.hourly_rate,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            description=data.description,
        )
        created = await self._repo.create_salary_grade(obj)
        return SalaryGradeResponse.model_validate(created)

    async def get_salary_grade(self, grade_code: str) -> SalaryGradeResponse:
        obj = await self._repo.get_salary_grade_by_code(grade_code)
        if not obj:
            raise SalaryGradeNotFoundException(identifier=grade_code)
        return SalaryGradeResponse.model_validate(obj)

    async def list_salary_grades(
        self, page: int = 1, page_size: int = 20, active_only: bool = True
    ) -> SalaryGradeListResponse:
        items, total = await self._repo.list_salary_grades(page, page_size, active_only)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return SalaryGradeListResponse(
            items=[SalaryGradeResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_salary_grade(
        self, grade_code: str, data: SalaryGradeUpdateRequest
    ) -> SalaryGradeResponse:
        obj = await self._repo.get_salary_grade_by_code(grade_code)
        if not obj:
            raise SalaryGradeNotFoundException(identifier=grade_code)
        updated = await self._repo.update_salary_grade(obj, data)
        return SalaryGradeResponse.model_validate(updated)

    # ------------------------------------------------------------------
    # BonusPolicy
    # ------------------------------------------------------------------

    async def create_bonus_policy(self, data: BonusPolicyCreateRequest) -> BonusPolicyResponse:
        existing = await self._repo.get_bonus_policy_by_code(data.policy_code)
        if existing:
            raise BonusPolicyAlreadyExistsException(identifier=data.policy_code)
        obj = BonusPolicy(
            policy_code=data.policy_code,
            policy_name=data.policy_name,
            bonus_type=data.bonus_type,
            bonus_value=data.bonus_value,
            condition_description=data.condition_description,
        )
        created = await self._repo.create_bonus_policy(obj)
        return BonusPolicyResponse.model_validate(created)

    async def get_bonus_policy(self, policy_code: str) -> BonusPolicyResponse:
        obj = await self._repo.get_bonus_policy_by_code(policy_code)
        if not obj:
            raise BonusPolicyNotFoundException(identifier=policy_code)
        return BonusPolicyResponse.model_validate(obj)

    async def list_bonus_policies(
        self, page: int = 1, page_size: int = 20, active_only: bool = True
    ) -> BonusPolicyListResponse:
        items, total = await self._repo.list_bonus_policies(page, page_size, active_only)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return BonusPolicyListResponse(
            items=[BonusPolicyResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_bonus_policy(
        self, policy_code: str, data: BonusPolicyUpdateRequest
    ) -> BonusPolicyResponse:
        obj = await self._repo.get_bonus_policy_by_code(policy_code)
        if not obj:
            raise BonusPolicyNotFoundException(identifier=policy_code)
        updated = await self._repo.update_bonus_policy(obj, data)
        return BonusPolicyResponse.model_validate(updated)

    # ------------------------------------------------------------------
    # MonthlyPayroll
    # ------------------------------------------------------------------

    async def create_payroll(self, data: PayrollCreateRequest) -> PayrollResponse:
        # Check duplicate
        existing = await self._repo.get_payroll_by_teacher_month(
            data.teacher_id, data.payroll_month
        )
        if existing:
            raise PayrollAlreadyExistsException(
                teacher_code=str(data.teacher_id),
                month=str(data.payroll_month),
            )
        # Validate salary grade exists
        sg = await self._repo.get_salary_grade_by_id(data.salary_grade_id)
        if not sg:
            raise SalaryGradeNotFoundException(identifier=str(data.salary_grade_id))

        # Calculate teaching allowance for excess hours
        excess_hours = max(0, data.teaching_hours_actual - data.teaching_hours_standard)
        teaching_allowance = data.teaching_allowance or Decimal(excess_hours) * sg.hourly_rate

        # Sum bonuses from request
        total_bonus = sum(b.amount for b in data.bonus_details)
        net_salary = data.base_salary + teaching_allowance + total_bonus - data.deductions

        obj = MonthlyPayroll(
            teacher_id=data.teacher_id,
            salary_grade_id=data.salary_grade_id,
            payroll_month=data.payroll_month,
            work_days_standard=data.work_days_standard,
            work_days_actual=data.work_days_actual,
            teaching_hours_standard=data.teaching_hours_standard,
            teaching_hours_actual=data.teaching_hours_actual,
            base_salary=data.base_salary,
            teaching_allowance=teaching_allowance,
            total_bonus=total_bonus,
            deductions=data.deductions,
            net_salary=net_salary,
            notes=data.notes,
        )
        created = await self._repo.create_payroll(obj)

        # Add bonus details
        for bd in data.bonus_details:
            detail = PayrollBonusDetail(
                payroll_id=created.id,
                bonus_policy_id=bd.bonus_policy_id,
                amount=bd.amount,
                note=bd.note,
            )
            await self._repo.add_bonus_detail(detail)

        # Reload with bonus_details
        final = await self._repo.get_payroll_by_id(created.id)
        return _to_payroll_response(final)

    async def get_payroll(self, payroll_id: int) -> PayrollResponse:
        obj = await self._repo.get_payroll_by_id(payroll_id)
        if not obj:
            raise PayrollNotFoundException(identifier=str(payroll_id))
        return _to_payroll_response(obj)

    async def list_payrolls(self, params: PayrollQueryParams) -> PayrollListResponse:
        items, total = await self._repo.list_payrolls(params)
        total_pages = math.ceil(total / params.page_size) if total > 0 else 1
        return PayrollListResponse(
            items=[_to_payroll_response(i) for i in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

    async def update_payroll(
        self, payroll_id: int, data: PayrollUpdateRequest
    ) -> PayrollResponse:
        obj = await self._repo.get_payroll_by_id(payroll_id)
        if not obj:
            raise PayrollNotFoundException(identifier=str(payroll_id))
        if obj.status == PayrollStatus.PAID:
            raise PayrollLockedEception(identifier=str(payroll_id))
        updated = await self._repo.update_payroll(obj, data)
        final = await self._repo.recalculate_net_salary(updated)
        return _to_payroll_response(final)

    async def update_payroll_status(
        self, payroll_id: int, data: PayrollStatusUpdateRequest
    ) -> PayrollResponse:
        obj = await self._repo.get_payroll_by_id(payroll_id)
        if not obj:
            raise PayrollNotFoundException(identifier=str(payroll_id))

        current = obj.status
        new_status = data.new_status
        if current == new_status:
            return _to_payroll_response(obj)

        allowed = VALID_PAYROLL_STATUS_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise InvalidPayrollTransitionException(
                current=current.value, target=new_status.value
            )
        updated = await self._repo.update_payroll_status(
            obj, new_status, data.confirmed_by, data.notes
        )
        return _to_payroll_response(updated)

    async def add_bonus_to_payroll(
        self, payroll_id: int, data: PayrollBonusDetailCreateRequest
    ) -> PayrollResponse:
        obj = await self._repo.get_payroll_by_id(payroll_id)
        if not obj:
            raise PayrollNotFoundException(identifier=str(payroll_id))
        if obj.status == PayrollStatus.PAID:
            raise PayrollLockedEception(identifier=str(payroll_id))
        detail = PayrollBonusDetail(
            payroll_id=payroll_id,
            bonus_policy_id=data.bonus_policy_id,
            amount=data.amount,
            note=data.note,
        )
        await self._repo.add_bonus_detail(detail)
        final = await self._repo.recalculate_net_salary(obj)
        return _to_payroll_response(final)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _to_payroll_response(obj: MonthlyPayroll) -> PayrollResponse:
    bonus_details = [
        PayrollBonusDetailResponse.model_validate(d)
        for d in (obj.bonus_details or [])
    ]
    data = PayrollResponse.model_validate(obj)
    data.bonus_details = bonus_details
    return data
