"""
Grading Repository – database access layer.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions.database import DatabaseIntegrityException, DatabaseQueryException
from app.modules.grading.dto import (
    ClassSubjectUpdateRequest,
    GradeComponentUpdateRequest,
    SubjectUpdateRequest,
)
from app.modules.grading.entity import (
    AcademicRank,
    ClassSubject,
    GradeAuditLog,
    GradeComponent,
    SemesterAverage,
    StudentGrade,
    Subject,
    _calc_rank,
)


class GradingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ------------------------------------------------------------------
    # Subject
    # ------------------------------------------------------------------

    async def create_subject(self, obj: Subject) -> Subject:
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
            raise DatabaseQueryException(operation="create_subject", reason=str(exc)) from exc

    async def get_subject_by_id(self, subject_id: int) -> Optional[Subject]:
        try:
            result = await self._s.execute(
                select(Subject).where(Subject.id == subject_id, Subject.is_active == True)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_subject_by_id", reason=str(exc)) from exc

    async def get_subject_by_code(self, subject_code: str) -> Optional[Subject]:
        try:
            result = await self._s.execute(
                select(Subject).where(Subject.subject_code == subject_code)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_subject_by_code", reason=str(exc)) from exc

    async def list_subjects(
        self, page: int = 1, page_size: int = 20, active_only: bool = True
    ) -> Tuple[List[Subject], int]:
        try:
            q = select(Subject)
            if active_only:
                q = q.where(Subject.is_active == True)
            count_result = await self._s.execute(select(func.count()).select_from(q.subquery()))
            total = count_result.scalar_one()
            offset = (page - 1) * page_size
            rows = await self._s.execute(
                q.order_by(Subject.subject_code.asc()).offset(offset).limit(page_size)
            )
            return list(rows.scalars().all()), total
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_subjects", reason=str(exc)) from exc

    async def update_subject(self, obj: Subject, data: SubjectUpdateRequest) -> Subject:
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
            raise DatabaseQueryException(operation="update_subject", reason=str(exc)) from exc

    # ------------------------------------------------------------------
    # ClassSubject
    # ------------------------------------------------------------------

    async def create_class_subject(self, obj: ClassSubject) -> ClassSubject:
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
            raise DatabaseQueryException(operation="create_class_subject", reason=str(exc)) from exc

    async def get_class_subject_by_id(self, cs_id: int) -> Optional[ClassSubject]:
        try:
            result = await self._s.execute(
                select(ClassSubject)
                .options(selectinload(ClassSubject.grade_components))
                .where(ClassSubject.id == cs_id, ClassSubject.is_active == True)
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_class_subject_by_id", reason=str(exc)) from exc

    async def get_class_subject(
        self,
        classroom_id: int,
        subject_id: int,
        semester: int,
        academic_year: str,
    ) -> Optional[ClassSubject]:
        try:
            result = await self._s.execute(
                select(ClassSubject).where(
                    ClassSubject.classroom_id == classroom_id,
                    ClassSubject.subject_id == subject_id,
                    ClassSubject.semester == semester,
                    ClassSubject.academic_year == academic_year,
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_class_subject", reason=str(exc)) from exc

    async def list_class_subjects(
        self,
        classroom_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        academic_year: Optional[str] = None,
        semester: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[ClassSubject], int]:
        try:
            q = select(ClassSubject).where(ClassSubject.is_active == True)
            if classroom_id:
                q = q.where(ClassSubject.classroom_id == classroom_id)
            if teacher_id:
                q = q.where(ClassSubject.teacher_id == teacher_id)
            if academic_year:
                q = q.where(ClassSubject.academic_year == academic_year)
            if semester:
                q = q.where(ClassSubject.semester == semester)
            count_result = await self._s.execute(select(func.count()).select_from(q.subquery()))
            total = count_result.scalar_one()
            offset = (page - 1) * page_size
            rows = await self._s.execute(
                q.order_by(ClassSubject.academic_year.desc(), ClassSubject.id.asc())
                 .offset(offset).limit(page_size)
            )
            return list(rows.scalars().all()), total
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="list_class_subjects", reason=str(exc)) from exc

    async def update_class_subject(
        self, obj: ClassSubject, data: ClassSubjectUpdateRequest
    ) -> ClassSubject:
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
            raise DatabaseQueryException(operation="update_class_subject", reason=str(exc)) from exc

    # ------------------------------------------------------------------
    # GradeComponent
    # ------------------------------------------------------------------

    async def create_grade_component(self, obj: GradeComponent) -> GradeComponent:
        try:
            self._s.add(obj)
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="create_grade_component", reason=str(exc)) from exc

    async def get_grade_component_by_id(self, gc_id: int) -> Optional[GradeComponent]:
        try:
            result = await self._s.execute(
                select(GradeComponent).where(
                    GradeComponent.id == gc_id, GradeComponent.is_active == True
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_grade_component_by_id", reason=str(exc)) from exc

    async def list_grade_components_by_class_subject(
        self, class_subject_id: int
    ) -> List[GradeComponent]:
        try:
            result = await self._s.execute(
                select(GradeComponent).where(
                    GradeComponent.class_subject_id == class_subject_id,
                    GradeComponent.is_active == True,
                )
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="list_grade_components_by_class_subject", reason=str(exc)
            ) from exc

    async def sum_weight_for_class_subject(
        self, class_subject_id: int, exclude_id: Optional[int] = None
    ) -> int:
        try:
            q = select(func.coalesce(func.sum(GradeComponent.weight_percent), 0)).where(
                GradeComponent.class_subject_id == class_subject_id,
                GradeComponent.is_active == True,
            )
            if exclude_id:
                q = q.where(GradeComponent.id != exclude_id)
            result = await self._s.execute(q)
            return result.scalar_one() or 0
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="sum_weight_for_class_subject", reason=str(exc)
            ) from exc

    async def update_grade_component(
        self, obj: GradeComponent, data: GradeComponentUpdateRequest
    ) -> GradeComponent:
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
            raise DatabaseQueryException(operation="update_grade_component", reason=str(exc)) from exc

    # ------------------------------------------------------------------
    # StudentGrade
    # ------------------------------------------------------------------

    async def create_student_grade(self, obj: StudentGrade) -> StudentGrade:
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
            raise DatabaseQueryException(operation="create_student_grade", reason=str(exc)) from exc

    async def bulk_create_student_grades(self, objs: List[StudentGrade]) -> List[StudentGrade]:
        try:
            self._s.add_all(objs)
            await self._s.commit()
            for obj in objs:
                await self._s.refresh(obj)
            return objs
        except IntegrityError as exc:
            await self._s.rollback()
            raise DatabaseIntegrityException(constraint=str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="bulk_create_student_grades", reason=str(exc)) from exc

    async def get_student_grade_by_id(self, grade_id: int) -> Optional[StudentGrade]:
        try:
            result = await self._s.execute(
                select(StudentGrade).where(
                    StudentGrade.id == grade_id, StudentGrade.is_active == True
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_student_grade_by_id", reason=str(exc)) from exc

    async def list_grades_by_class_subject(
        self,
        class_subject_id: int,
        grade_component_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Tuple[List[StudentGrade], int]:
        try:
            q = select(StudentGrade).where(
                StudentGrade.class_subject_id == class_subject_id,
                StudentGrade.is_active == True,
            )
            if grade_component_id:
                q = q.where(StudentGrade.grade_component_id == grade_component_id)
            count_result = await self._s.execute(select(func.count()).select_from(q.subquery()))
            total = count_result.scalar_one()
            offset = (page - 1) * page_size
            rows = await self._s.execute(
                q.order_by(StudentGrade.student_id.asc()).offset(offset).limit(page_size)
            )
            return list(rows.scalars().all()), total
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="list_grades_by_class_subject", reason=str(exc)
            ) from exc

    async def list_grades_by_student(
        self,
        student_id: int,
        class_subject_id: Optional[int] = None,
    ) -> List[StudentGrade]:
        try:
            q = select(StudentGrade).where(
                StudentGrade.student_id == student_id,
                StudentGrade.is_active == True,
            )
            if class_subject_id:
                q = q.where(StudentGrade.class_subject_id == class_subject_id)
            result = await self._s.execute(q)
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="list_grades_by_student", reason=str(exc)
            ) from exc

    async def update_student_grade(
        self,
        obj: StudentGrade,
        new_score: Decimal,
        modified_by: Optional[int],
        reason: str,
    ) -> StudentGrade:
        try:
            old_score = obj.score
            # Write audit log first
            audit = GradeAuditLog(
                student_grade_id=obj.id,
                old_score=old_score,
                new_score=new_score,
                changed_by=modified_by,
                reason=reason,
            )
            self._s.add(audit)
            # Update grade
            obj.score = new_score
            obj.last_modified_by = modified_by
            obj.last_modified_at = datetime.utcnow()
            await self._s.commit()
            await self._s.refresh(obj)
            return obj
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="update_student_grade", reason=str(exc)) from exc

    async def get_audit_logs_for_grade(self, student_grade_id: int) -> List[GradeAuditLog]:
        try:
            result = await self._s.execute(
                select(GradeAuditLog)
                .where(GradeAuditLog.student_grade_id == student_grade_id)
                .order_by(GradeAuditLog.changed_at.desc())
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="get_audit_logs_for_grade", reason=str(exc)
            ) from exc

    # ------------------------------------------------------------------
    # SemesterAverage
    # ------------------------------------------------------------------

    async def upsert_semester_average(
        self,
        student_id: int,
        class_subject_id: int,
        semester: int,
        academic_year: str,
        average_score: Decimal,
    ) -> SemesterAverage:
        """Insert or update semester average for a student-subject pair."""
        try:
            result = await self._s.execute(
                select(SemesterAverage).where(
                    SemesterAverage.student_id == student_id,
                    SemesterAverage.class_subject_id == class_subject_id,
                )
            )
            existing = result.scalars().first()
            rank = _calc_rank(float(average_score))
            if existing:
                existing.average_score = average_score
                existing.rank = rank
                existing.calculated_at = datetime.utcnow()
                await self._s.commit()
                await self._s.refresh(existing)
                return existing
            else:
                new_avg = SemesterAverage(
                    student_id=student_id,
                    class_subject_id=class_subject_id,
                    semester=semester,
                    academic_year=academic_year,
                    average_score=average_score,
                    rank=rank,
                )
                self._s.add(new_avg)
                await self._s.commit()
                await self._s.refresh(new_avg)
                return new_avg
        except SQLAlchemyError as exc:
            await self._s.rollback()
            raise DatabaseQueryException(operation="upsert_semester_average", reason=str(exc)) from exc

    async def get_semester_average(
        self, student_id: int, class_subject_id: int
    ) -> Optional[SemesterAverage]:
        try:
            result = await self._s.execute(
                select(SemesterAverage).where(
                    SemesterAverage.student_id == student_id,
                    SemesterAverage.class_subject_id == class_subject_id,
                )
            )
            return result.scalars().first()
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_semester_average", reason=str(exc)) from exc

    async def list_semester_averages_by_student(
        self, student_id: int, semester: Optional[int] = None, academic_year: Optional[str] = None
    ) -> List[SemesterAverage]:
        try:
            q = select(SemesterAverage).where(SemesterAverage.student_id == student_id)
            if semester:
                q = q.where(SemesterAverage.semester == semester)
            if academic_year:
                q = q.where(SemesterAverage.academic_year == academic_year)
            result = await self._s.execute(q)
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="list_semester_averages_by_student", reason=str(exc)
            ) from exc

    async def list_semester_averages_by_class_subject(
        self, class_subject_id: int
    ) -> List[SemesterAverage]:
        try:
            result = await self._s.execute(
                select(SemesterAverage).where(
                    SemesterAverage.class_subject_id == class_subject_id
                ).order_by(SemesterAverage.average_score.desc())
            )
            return list(result.scalars().all())
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(
                operation="list_semester_averages_by_class_subject", reason=str(exc)
            ) from exc

    async def get_grade_statistics(self, class_subject_id: int) -> Dict[str, Any]:
        """Return aggregate stats for a class-subject."""
        try:
            result = await self._s.execute(
                select(
                    func.count(SemesterAverage.id).label("total"),
                    func.avg(SemesterAverage.average_score).label("avg_score"),
                    func.max(SemesterAverage.average_score).label("max_score"),
                    func.min(SemesterAverage.average_score).label("min_score"),
                ).where(SemesterAverage.class_subject_id == class_subject_id)
            )
            row = result.one()
            # Count by rank
            rank_result = await self._s.execute(
                select(SemesterAverage.rank, func.count(SemesterAverage.id)).where(
                    SemesterAverage.class_subject_id == class_subject_id
                ).group_by(SemesterAverage.rank)
            )
            rank_dist = {r.value: 0 for r in AcademicRank}
            for rank, count in rank_result.all():
                rank_dist[rank.value] = count

            return {
                "total_students": row.total or 0,
                "avg_score": row.avg_score,
                "max_score": row.max_score,
                "min_score": row.min_score,
                "rank_distribution": rank_dist,
            }
        except SQLAlchemyError as exc:
            raise DatabaseQueryException(operation="get_grade_statistics", reason=str(exc)) from exc
