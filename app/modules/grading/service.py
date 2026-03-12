"""
Grading Service – business logic layer.
"""

import math
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.grading import (
    ClassSubjectAlreadyExistsException,
    ClassSubjectNotFoundException,
    GradeComponentNotFoundException,
    GradeScoreOutOfRangeException,
    GradeWeightSumException,
    StudentGradeNotFoundException,
    SubjectAlreadyExistsException,
    SubjectNotFoundException,
    UnauthorizedGradeEntryException,
)
from app.modules.grading.dto import (
    ClassSubjectCreateRequest,
    ClassSubjectListResponse,
    ClassSubjectResponse,
    ClassSubjectUpdateRequest,
    GradeAuditLogResponse,
    GradeComponentCreateRequest,
    GradeComponentResponse,
    GradeComponentUpdateRequest,
    GradeStatisticsResponse,
    SemesterAverageResponse,
    StudentGradeBulkCreateRequest,
    StudentGradeCreateRequest,
    StudentGradeListResponse,
    StudentGradeResponse,
    StudentGradeUpdateRequest,
    StudentReportResponse,
    SubjectCreateRequest,
    SubjectListResponse,
    SubjectResponse,
    SubjectUpdateRequest,
)
from app.modules.grading.entity import (
    ClassSubject,
    GradeComponent,
    StudentGrade,
    Subject,
    _calc_rank,
)
from app.modules.grading.repository import GradingRepository


class GradingService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = GradingRepository(session)

    # ------------------------------------------------------------------
    # Subject
    # ------------------------------------------------------------------

    async def create_subject(self, data: SubjectCreateRequest) -> SubjectResponse:
        existing = await self._repo.get_subject_by_code(data.subject_code)
        if existing:
            raise SubjectAlreadyExistsException(identifier=data.subject_code)
        obj = Subject(
            subject_code=data.subject_code,
            subject_name=data.subject_name,
            subject_type=data.subject_type,
            credits=data.credits,
            description=data.description,
        )
        created = await self._repo.create_subject(obj)
        return SubjectResponse.model_validate(created)

    async def get_subject(self, subject_code: str) -> SubjectResponse:
        obj = await self._repo.get_subject_by_code(subject_code)
        if not obj:
            raise SubjectNotFoundException(identifier=subject_code)
        return SubjectResponse.model_validate(obj)

    async def list_subjects(
        self, page: int = 1, page_size: int = 20, active_only: bool = True
    ) -> SubjectListResponse:
        items, total = await self._repo.list_subjects(page, page_size, active_only)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return SubjectListResponse(
            items=[SubjectResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_subject(
        self, subject_code: str, data: SubjectUpdateRequest
    ) -> SubjectResponse:
        obj = await self._repo.get_subject_by_code(subject_code)
        if not obj:
            raise SubjectNotFoundException(identifier=subject_code)
        updated = await self._repo.update_subject(obj, data)
        return SubjectResponse.model_validate(updated)

    # ------------------------------------------------------------------
    # ClassSubject
    # ------------------------------------------------------------------

    async def create_class_subject(
        self, data: ClassSubjectCreateRequest
    ) -> ClassSubjectResponse:
        existing = await self._repo.get_class_subject(
            data.classroom_id, data.subject_id, data.semester, data.academic_year
        )
        if existing:
            raise ClassSubjectAlreadyExistsException(
                identifier=f"classroom={data.classroom_id} subject={data.subject_id} "
                           f"sem={data.semester} year={data.academic_year}"
            )
        obj = ClassSubject(
            classroom_id=data.classroom_id,
            subject_id=data.subject_id,
            teacher_id=data.teacher_id,
            semester=data.semester,
            academic_year=data.academic_year,
        )
        created = await self._repo.create_class_subject(obj)
        return ClassSubjectResponse.model_validate(created)

    async def get_class_subject(self, cs_id: int) -> ClassSubjectResponse:
        obj = await self._repo.get_class_subject_by_id(cs_id)
        if not obj:
            raise ClassSubjectNotFoundException(identifier=str(cs_id))
        return ClassSubjectResponse.model_validate(obj)

    async def list_class_subjects(
        self,
        classroom_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        academic_year: Optional[str] = None,
        semester: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> ClassSubjectListResponse:
        items, total = await self._repo.list_class_subjects(
            classroom_id, teacher_id, academic_year, semester, page, page_size
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return ClassSubjectListResponse(
            items=[ClassSubjectResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_class_subject(
        self, cs_id: int, data: ClassSubjectUpdateRequest
    ) -> ClassSubjectResponse:
        obj = await self._repo.get_class_subject_by_id(cs_id)
        if not obj:
            raise ClassSubjectNotFoundException(identifier=str(cs_id))
        updated = await self._repo.update_class_subject(obj, data)
        return ClassSubjectResponse.model_validate(updated)

    # ------------------------------------------------------------------
    # GradeComponent
    # ------------------------------------------------------------------

    async def create_grade_component(
        self, data: GradeComponentCreateRequest
    ) -> GradeComponentResponse:
        # Validate weight sum will not exceed 100
        existing_sum = await self._repo.sum_weight_for_class_subject(data.class_subject_id)
        if existing_sum + data.weight_percent > 100:
            raise GradeWeightSumException(current_sum=existing_sum + data.weight_percent)
        obj = GradeComponent(
            class_subject_id=data.class_subject_id,
            component_name=data.component_name,
            weight_percent=data.weight_percent,
            min_count=data.min_count,
        )
        created = await self._repo.create_grade_component(obj)
        return GradeComponentResponse.model_validate(created)

    async def get_grade_component(self, gc_id: int) -> GradeComponentResponse:
        obj = await self._repo.get_grade_component_by_id(gc_id)
        if not obj:
            raise GradeComponentNotFoundException(identifier=str(gc_id))
        return GradeComponentResponse.model_validate(obj)

    async def list_grade_components(
        self, class_subject_id: int
    ) -> List[GradeComponentResponse]:
        items = await self._repo.list_grade_components_by_class_subject(class_subject_id)
        return [GradeComponentResponse.model_validate(i) for i in items]

    async def update_grade_component(
        self, gc_id: int, data: GradeComponentUpdateRequest
    ) -> GradeComponentResponse:
        obj = await self._repo.get_grade_component_by_id(gc_id)
        if not obj:
            raise GradeComponentNotFoundException(identifier=str(gc_id))
        # If weight changes, validate sum
        if data.weight_percent is not None:
            existing_sum = await self._repo.sum_weight_for_class_subject(
                obj.class_subject_id, exclude_id=gc_id
            )
            if existing_sum + data.weight_percent > 100:
                raise GradeWeightSumException(
                    current_sum=existing_sum + data.weight_percent
                )
        updated = await self._repo.update_grade_component(obj, data)
        return GradeComponentResponse.model_validate(updated)

    # ------------------------------------------------------------------
    # StudentGrade
    # ------------------------------------------------------------------

    async def enter_grade(self, data: StudentGradeCreateRequest) -> StudentGradeResponse:
        # Validate score range
        if not (Decimal("0") <= data.score <= Decimal("10")):
            raise GradeScoreOutOfRangeException(score=float(data.score))

        # Validate class_subject exists
        cs = await self._repo.get_class_subject_by_id(data.class_subject_id)
        if not cs:
            raise ClassSubjectNotFoundException(identifier=str(data.class_subject_id))

        # Validate entered_by is the assigned teacher (if provided)
        if data.entered_by and cs.teacher_id and data.entered_by != cs.teacher_id:
            raise UnauthorizedGradeEntryException(
                teacher_id=str(data.entered_by),
                class_subject_id=str(data.class_subject_id),
            )

        obj = StudentGrade(
            student_id=data.student_id,
            class_subject_id=data.class_subject_id,
            grade_component_id=data.grade_component_id,
            score=data.score,
            exam_date=data.exam_date,
            entered_by=data.entered_by,
        )
        created = await self._repo.create_student_grade(obj)

        # Recalculate semester average
        await self._recalculate_average(data.student_id, data.class_subject_id, cs)

        return StudentGradeResponse.model_validate(created)

    async def bulk_enter_grades(
        self, data: StudentGradeBulkCreateRequest
    ) -> List[StudentGradeResponse]:
        cs = await self._repo.get_class_subject_by_id(data.class_subject_id)
        if not cs:
            raise ClassSubjectNotFoundException(identifier=str(data.class_subject_id))
        if data.entered_by and cs.teacher_id and data.entered_by != cs.teacher_id:
            raise UnauthorizedGradeEntryException(
                teacher_id=str(data.entered_by),
                class_subject_id=str(data.class_subject_id),
            )
        objs = []
        for g in data.grades:
            score = Decimal(str(g["score"]))
            if not (Decimal("0") <= score <= Decimal("10")):
                raise GradeScoreOutOfRangeException(score=float(score))
            objs.append(StudentGrade(
                student_id=g["student_id"],
                class_subject_id=data.class_subject_id,
                grade_component_id=data.grade_component_id,
                score=score,
                exam_date=data.exam_date,
                entered_by=data.entered_by,
            ))
        created_list = await self._repo.bulk_create_student_grades(objs)

        # Recalculate averages for all affected students
        student_ids = {g["student_id"] for g in data.grades}
        for sid in student_ids:
            await self._recalculate_average(sid, data.class_subject_id, cs)

        return [StudentGradeResponse.model_validate(g) for g in created_list]

    async def get_grade(self, grade_id: int) -> StudentGradeResponse:
        obj = await self._repo.get_student_grade_by_id(grade_id)
        if not obj:
            raise StudentGradeNotFoundException(identifier=str(grade_id))
        return StudentGradeResponse.model_validate(obj)

    async def list_grades_by_class_subject(
        self,
        class_subject_id: int,
        grade_component_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> StudentGradeListResponse:
        items, total = await self._repo.list_grades_by_class_subject(
            class_subject_id, grade_component_id, page, page_size
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return StudentGradeListResponse(
            items=[StudentGradeResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_grade(
        self, grade_id: int, data: StudentGradeUpdateRequest
    ) -> StudentGradeResponse:
        obj = await self._repo.get_student_grade_by_id(grade_id)
        if not obj:
            raise StudentGradeNotFoundException(identifier=str(grade_id))
        if not (Decimal("0") <= data.score <= Decimal("10")):
            raise GradeScoreOutOfRangeException(score=float(data.score))

        updated = await self._repo.update_student_grade(
            obj, data.score, data.modified_by, data.reason
        )
        # Recalculate average
        cs = await self._repo.get_class_subject_by_id(obj.class_subject_id)
        if cs:
            await self._recalculate_average(obj.student_id, obj.class_subject_id, cs)

        return StudentGradeResponse.model_validate(updated)

    async def get_audit_logs(self, grade_id: int) -> List[GradeAuditLogResponse]:
        logs = await self._repo.get_audit_logs_for_grade(grade_id)
        return [GradeAuditLogResponse.model_validate(l) for l in logs]

    # ------------------------------------------------------------------
    # SemesterAverage & Statistics
    # ------------------------------------------------------------------

    async def get_student_report(
        self,
        student_id: int,
        semester: Optional[int] = None,
        academic_year: Optional[str] = None,
    ) -> StudentReportResponse:
        avgs = await self._repo.list_semester_averages_by_student(
            student_id, semester, academic_year
        )
        avg_responses = [SemesterAverageResponse.model_validate(a) for a in avgs]
        overall_avg = None
        overall_rank = None
        if avgs:
            overall_avg = sum(a.average_score for a in avgs) / len(avgs)
            overall_rank = _calc_rank(float(overall_avg))
        return StudentReportResponse(
            student_id=student_id,
            semester=semester or 0,
            academic_year=academic_year or "",
            subjects=avg_responses,
            overall_average=overall_avg,
            overall_rank=overall_rank,
        )

    async def get_class_statistics(
        self, class_subject_id: int
    ) -> GradeStatisticsResponse:
        cs = await self._repo.get_class_subject_by_id(class_subject_id)
        if not cs:
            raise ClassSubjectNotFoundException(identifier=str(class_subject_id))
        stats = await self._repo.get_grade_statistics(class_subject_id)
        return GradeStatisticsResponse(
            class_subject_id=class_subject_id,
            classroom_id=cs.classroom_id,
            subject_id=cs.subject_id,
            semester=cs.semester,
            academic_year=cs.academic_year,
            total_students=stats["total_students"],
            avg_score=stats["avg_score"],
            max_score=stats["max_score"],
            min_score=stats["min_score"],
            rank_distribution=stats["rank_distribution"],
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _recalculate_average(
        self,
        student_id: int,
        class_subject_id: int,
        cs: ClassSubject,
    ) -> None:
        """Recalculate and upsert semester average for student-subject."""
        grades = await self._repo.list_grades_by_student(student_id, class_subject_id)
        components = await self._repo.list_grade_components_by_class_subject(class_subject_id)

        if not grades or not components:
            return

        # Map component_id -> weight_percent
        weight_map = {c.id: c.weight_percent for c in components}
        total_weight = sum(weight_map.values())
        if total_weight == 0:
            return

        # Weighted average
        weighted_sum = Decimal("0")
        weight_used = 0
        for g in grades:
            if g.grade_component_id in weight_map:
                w = weight_map[g.grade_component_id]
                weighted_sum += g.score * Decimal(w)
                weight_used += w

        if weight_used == 0:
            return

        average = weighted_sum / Decimal(weight_used)
        await self._repo.upsert_semester_average(
            student_id=student_id,
            class_subject_id=class_subject_id,
            semester=cs.semester,
            academic_year=cs.academic_year,
            average_score=average.quantize(Decimal("0.01")),
        )
