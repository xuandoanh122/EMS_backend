"""
Salary Repository – database access layer.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions.database import DatabaseIntegrityException, DatabaseQueryException
from app.modules.salary.dto import (
    BonusPolicyUpdateRequest,
    PayrollQueryParams,
    PayrollUpdateRequest,
    SalaryGradeUpdateRequest,
)
from app.modules.salary.entity import (
    BonusPolicy,
    ExperienceTier,
    MonthlyPayroll,
    PayrollBonusDetail,
    PayrollStatus,
    QualificationLevel,
    SalaryGrade,
)


class SalaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ------------------------------------------------------------------
    # SalaryGrade
    # ------------------------------------------------------------------

    async def create_salary_grade(self, obj: SalaryGrade) -> SalaryGrade:
        try:
            self._s.add(obj)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except IntegrityError as exc:
            await self._s.rollback()
            raise DatabaseIntegrityException(constraint=str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="create_salary_grade", reason=str(exc)) from exc

    async def get_salary_grade_by_id(self, grade_id: int) -> Optional[SalaryGrade]:
        try:
            result = await self._s.execute(
                select(SalaryGrade).where(SalaryGrade.id == grade_id)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_salary_grade_by_id", reason=str(exc)) from exc

    async def get_salary_grade_by_code(self, grade_code: str) -> Optional[SalaryGrade]:
        try:
            result = await self._s.execute(
                select(SalaryGrade).where(SalaryGrade.grade_code == grade_code)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_salary_grade_by_code", reason=str(exc)) from exc

    async def find_matching_grade(
        self,
        qualification_level: QualificationLevel,
        experience_tier: ExperienceTier,
        reference_date: date,
    ) -> Optional[SalaryGrade]:
        """Find an active salary grade for given qualification + experience tier."""
        try:
            q = select(SalaryGrade).where(
                SalaryGrade.qualification_level == qualification_level,
                SalaryGrade.experience_tier == experience_tier,
                SalaryGrade.is_active == True,
                SalaryGrade.effective_from <= reference_date,
            )
            # Prefer not-yet-expired, then most recently effective
            result = await self._s.execute(
                q.order_by(SalaryGrade.effective_from.desc()).limit(1)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="find_matching_grade", reason=str(exc)) from exc

    async def list_salary_grades(
        self, page: int = 1, page_size: int = 20, active_only: bool = True
    ) -> Tuple[List[SalaryGrade], int]:
        try:
            q = select(SalaryGrade)
            if active_only:
                q = q.where(SalaryGrade.is_active == True)
            count_result = await self._s.execute(select(func.count()).select_from(q.subquery()))
            total = count_result.scalar_one()
            offset = (page - 1) * page_size
            rows = await self._s.execute(
                q.order_by(
                    SalaryGrade.qualification_level.asc(),
                    SalaryGrade.experience_tier.asc(),
                ).offset(offset).limit(page_size)
            )
            return list(rows.scalars().all()), total
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_salary_grades", reason=str(exc)) from exc

    async def update_salary_grade(
        self, obj: SalaryGrade, data: SalaryGradeUpdateRequest
    ) -> SalaryGrade:
        try:
            update_data = data.model_dump(exclude_none=True, exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(obj, field):
                    setattr(obj, field, value)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="update_salary_grade", reason=str(exc)) from exc

    # ------------------------------------------------------------------
    # BonusPolicy
    # ------------------------------------------------------------------

    async def create_bonus_policy(self, obj: BonusPolicy) -> BonusPolicy:
        try:
            self._s.add(obj)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except IntegrityError as exc:
            await self._s.rollback()
            raise DatabaseIntegrityException(constraint=str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="create_bonus_policy", reason=str(exc)) from exc

    async def get_bonus_policy_by_id(self, policy_id: int) -> Optional[BonusPolicy]:
        try:
            result = await self._s.execute(
                select(BonusPolicy).where(BonusPolicy.id == policy_id)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_bonus_policy_by_id", reason=str(exc)) from exc

    async def get_bonus_policy_by_code(self, policy_code: str) -> Optional[BonusPolicy]:
        try:
            result = await self._s.execute(
                select(BonusPolicy).where(BonusPolicy.policy_code == policy_code)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_bonus_policy_by_code", reason=str(exc)) from exc

    async def list_bonus_policies(
        self, page: int = 1, page_size: int = 20, active_only: bool = True
    ) -> Tuple[List[BonusPolicy], int]:
        try:
            q = select(BonusPolicy)
            if active_only:
                q = q.where(BonusPolicy.is_active == True)
            count_result = await self._s.execute(select(func.count()).select_from(q.subquery()))
            total = count_result.scalar_one()
            offset = (page - 1) * page_size
            rows = await self._s.execute(
                q.order_by(BonusPolicy.policy_code.asc()).offset(offset).limit(page_size)
            )
            return list(rows.scalars().all()), total
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_bonus_policies", reason=str(exc)) from exc

    async def update_bonus_policy(
        self, obj: BonusPolicy, data: BonusPolicyUpdateRequest
    ) -> BonusPolicy:
        try:
            update_data = data.model_dump(exclude_none=True, exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(obj, field):
                    setattr(obj, field, value)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="update_bonus_policy", reason=str(exc)) from exc

    # ------------------------------------------------------------------
    # MonthlyPayroll
    # ------------------------------------------------------------------

    async def create_payroll(self, obj: MonthlyPayroll) -> MonthlyPayroll:
        try:
            self._s.add(obj)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except IntegrityError as exc:
            await self._s.rollback()
            raise DatabaseIntegrityException(constraint=str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="create_payroll", reason=str(exc)) from exc

    async def get_payroll_by_id(self, payroll_id: int) -> Optional[MonthlyPayroll]:
        try:
            result = await self._s.execute(
                select(MonthlyPayroll)
                .options(selectinload(MonthlyPayroll.bonus_details))
                .where(MonthlyPayroll.id == payroll_id)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_payroll_by_id", reason=str(exc)) from exc

    async def get_payroll_by_teacher_month(
        self, teacher_id: int, payroll_month: date
    ) -> Optional[MonthlyPayroll]:
        try:
            result = await self._s.execute(
                select(MonthlyPayroll)
                .options(selectinload(MonthlyPayroll.bonus_details))
                .where(
                    MonthlyPayroll.teacher_id == teacher_id,
                    MonthlyPayroll.payroll_month == payroll_month,
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_payroll_by_teacher_month", reason=str(exc)
            ) from exc

    async def list_payrolls(self, params: PayrollQueryParams) -> Tuple[List[MonthlyPayroll], int]:
        try:
            q = select(MonthlyPayroll).options(selectinload(MonthlyPayroll.bonus_details))
            if params.teacher_id:
                q = q.where(MonthlyPayroll.teacher_id == params.teacher_id)
            if params.status:
                q = q.where(MonthlyPayroll.status == params.status)
            if params.month_from:
                q = q.where(MonthlyPayroll.payroll_month >= params.month_from)
            if params.month_to:
                q = q.where(MonthlyPayroll.payroll_month <= params.month_to)

            count_result = await self._s.execute(select(func.count()).select_from(q.subquery()))
            total = count_result.scalar_one()
            offset = (params.page - 1) * params.page_size
            rows = await self._s.execute(
                q.order_by(MonthlyPayroll.payroll_month.desc(), MonthlyPayroll.teacher_id.asc())
                 .offset(offset).limit(params.page_size)
            )
            return list(rows.scalars().all()), total
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_payrolls", reason=str(exc)) from exc

    async def update_payroll(
        self, obj: MonthlyPayroll, data: PayrollUpdateRequest
    ) -> MonthlyPayroll:
        try:
            update_data = data.model_dump(exclude_none=True, exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(obj, field):
                    setattr(obj, field, value)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="update_payroll", reason=str(exc)) from exc

    async def update_payroll_status(
        self,
        obj: MonthlyPayroll,
        new_status: PayrollStatus,
        confirmed_by: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> MonthlyPayroll:
        from datetime import datetime
        try:
            obj.status = new_status
            if new_status == PayrollStatus.CONFIRMED:
                obj.confirmed_by = confirmed_by
                obj.confirmed_at = datetime.utcnow()
            elif new_status == PayrollStatus.PAID:
                obj.paid_at = datetime.utcnow()
            if notes:
                obj.notes = notes
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="update_payroll_status", reason=str(exc)) from exc

    async def add_bonus_detail(self, obj: PayrollBonusDetail) -> PayrollBonusDetail:
        try:
            self._s.add(obj)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="add_bonus_detail", reason=str(exc)) from exc

    async def recalculate_net_salary(self, obj: MonthlyPayroll) -> MonthlyPayroll:
        """Recompute total_bonus and net_salary from bonus_details."""
        try:
            # Reload bonus_details
            result = await self._s.execute(
                select(MonthlyPayroll)
                .options(selectinload(MonthlyPayroll.bonus_details))
                .where(MonthlyPayroll.id == obj.id)
            )
            obj = result.scalars().first()
            total_bonus = sum(d.amount for d in obj.bonus_details)
            obj.total_bonus = total_bonus
            obj.net_salary = (
                obj.base_salary
                + obj.teaching_allowance
                + total_bonus
                - obj.deductions
            )
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="recalculate_net_salary", reason=str(exc)) from exc
