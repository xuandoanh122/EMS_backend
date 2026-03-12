"""
Grading Controller – FastAPI router.

Endpoints:
  Subjects:
    POST   /grading/subjects                             – Create subject
    GET    /grading/subjects                             – List subjects
    GET    /grading/subjects/{subject_code}              – Get subject
    PATCH  /grading/subjects/{subject_code}              – Update subject

  ClassSubjects (Phân công):
    POST   /grading/class-subjects                       – Assign subject to class
    GET    /grading/class-subjects                       – List (filter: classroom/teacher/year)
    GET    /grading/class-subjects/{id}                  – Get
    PATCH  /grading/class-subjects/{id}                  – Update (assign teacher)

  GradeComponents:
    POST   /grading/grade-components                     – Create component
    GET    /grading/grade-components/{class_subject_id}  – List for class-subject
    PATCH  /grading/grade-components/{id}                – Update

  StudentGrades:
    POST   /grading/grades                               – Enter single grade
    POST   /grading/grades/bulk                          – Bulk enter grades
    GET    /grading/grades/{grade_id}                    – Get grade
    PATCH  /grading/grades/{grade_id}                    – Update grade (with audit)
    GET    /grading/grades/{grade_id}/audit-logs         – Grade history
    GET    /grading/class-subjects/{id}/grades           – All grades for class-subject

  Reports & Statistics:
    GET    /grading/students/{student_id}/report         – Student semester report
    GET    /grading/class-subjects/{id}/statistics       – Class statistics & charts
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.response import APIResponse
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
from app.modules.grading.service import GradingService

router = APIRouter()


def get_service(session: AsyncSession = Depends(get_async_session)) -> GradingService:
    return GradingService(session)


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

@router.post("/subjects", status_code=201, summary="Tạo môn học")
async def create_subject(
    data: SubjectCreateRequest,
    service: GradingService = Depends(get_service),
) -> APIResponse[SubjectResponse]:
    result = await service.create_subject(data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Subject Created",
        detail=f"Subject '{result.subject_code}' created",
    )


@router.get("/subjects", status_code=200, summary="Danh sách môn học")
async def list_subjects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    service: GradingService = Depends(get_service),
) -> APIResponse[SubjectListResponse]:
    result = await service.list_subjects(page, page_size, active_only)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} subject(s)",
    )


@router.get("/subjects/{subject_code}", status_code=200, summary="Chi tiết môn học")
async def get_subject(
    subject_code: str,
    service: GradingService = Depends(get_service),
) -> APIResponse[SubjectResponse]:
    result = await service.get_subject(subject_code)
    return APIResponse.success(data=result.model_dump())


@router.patch("/subjects/{subject_code}", status_code=200, summary="Cập nhật môn học")
async def update_subject(
    subject_code: str,
    data: SubjectUpdateRequest,
    service: GradingService = Depends(get_service),
) -> APIResponse[SubjectResponse]:
    result = await service.update_subject(subject_code, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Subject '{subject_code}' updated",
    )


# ---------------------------------------------------------------------------
# ClassSubjects
# ---------------------------------------------------------------------------

@router.post("/class-subjects", status_code=201,
             summary="Phân công môn học cho lớp + giáo viên")
async def create_class_subject(
    data: ClassSubjectCreateRequest,
    service: GradingService = Depends(get_service),
) -> APIResponse[ClassSubjectResponse]:
    result = await service.create_class_subject(data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Class Subject Created",
        detail=f"Class-subject assignment id={result.id} created",
    )


@router.get("/class-subjects", status_code=200,
            summary="Danh sách phân công môn (lọc theo lớp/GV/năm học/HK)")
async def list_class_subjects(
    classroom_id: Optional[int] = Query(None),
    teacher_id: Optional[int] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None, ge=1, le=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    service: GradingService = Depends(get_service),
) -> APIResponse[ClassSubjectListResponse]:
    result = await service.list_class_subjects(
        classroom_id, teacher_id, academic_year, semester, page, page_size
    )
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} class-subject(s)",
    )


@router.get("/class-subjects/{cs_id}", status_code=200, summary="Chi tiết phân công môn")
async def get_class_subject(
    cs_id: int,
    service: GradingService = Depends(get_service),
) -> APIResponse[ClassSubjectResponse]:
    result = await service.get_class_subject(cs_id)
    return APIResponse.success(data=result.model_dump())


@router.patch("/class-subjects/{cs_id}", status_code=200,
              summary="Cập nhật phân công môn (gán/thay giáo viên)")
async def update_class_subject(
    cs_id: int,
    data: ClassSubjectUpdateRequest,
    service: GradingService = Depends(get_service),
) -> APIResponse[ClassSubjectResponse]:
    result = await service.update_class_subject(cs_id, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Class-subject {cs_id} updated",
    )


# ---------------------------------------------------------------------------
# Grade Components
# ---------------------------------------------------------------------------

@router.post("/grade-components", status_code=201,
             summary="Tạo thành phần điểm (miệng/15p/1tiết/HK)")
async def create_grade_component(
    data: GradeComponentCreateRequest,
    service: GradingService = Depends(get_service),
) -> APIResponse[GradeComponentResponse]:
    result = await service.create_grade_component(data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Grade Component Created",
        detail=f"Grade component '{result.component_name}' ({result.weight_percent}%) created",
    )


@router.get("/grade-components/{class_subject_id}", status_code=200,
            summary="Danh sách thành phần điểm của 1 class-subject")
async def list_grade_components(
    class_subject_id: int,
    service: GradingService = Depends(get_service),
) -> APIResponse:
    result = await service.list_grade_components(class_subject_id)
    return APIResponse.success(
        data=[r.model_dump() for r in result],
        detail=f"Retrieved {len(result)} grade component(s)",
    )


@router.patch("/grade-components/{gc_id}", status_code=200,
              summary="Cập nhật thành phần điểm")
async def update_grade_component(
    gc_id: int,
    data: GradeComponentUpdateRequest,
    service: GradingService = Depends(get_service),
) -> APIResponse[GradeComponentResponse]:
    result = await service.update_grade_component(gc_id, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Grade component {gc_id} updated",
    )


# ---------------------------------------------------------------------------
# StudentGrades
# ---------------------------------------------------------------------------

@router.post("/grades", status_code=201, summary="Nhập điểm cho 1 học sinh")
async def enter_grade(
    data: StudentGradeCreateRequest,
    service: GradingService = Depends(get_service),
) -> APIResponse[StudentGradeResponse]:
    result = await service.enter_grade(data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Grade Entered",
        detail=f"Grade {result.score} entered for student {result.student_id}",
    )


@router.post("/grades/bulk", status_code=201,
             summary="Nhập điểm hàng loạt (1 cột điểm, nhiều học sinh)")
async def bulk_enter_grades(
    data: StudentGradeBulkCreateRequest,
    service: GradingService = Depends(get_service),
) -> APIResponse:
    results = await service.bulk_enter_grades(data)
    return APIResponse.created(
        data=[r.model_dump() for r in results],
        message="Bulk Grades Entered",
        detail=f"{len(results)} grade(s) entered for class-subject {data.class_subject_id}",
    )


@router.get("/grades/{grade_id}", status_code=200, summary="Chi tiết 1 cột điểm")
async def get_grade(
    grade_id: int,
    service: GradingService = Depends(get_service),
) -> APIResponse[StudentGradeResponse]:
    result = await service.get_grade(grade_id)
    return APIResponse.success(data=result.model_dump())


@router.patch("/grades/{grade_id}", status_code=200,
              summary="Sửa điểm (bắt buộc có lý do – ghi audit log)")
async def update_grade(
    grade_id: int,
    data: StudentGradeUpdateRequest,
    service: GradingService = Depends(get_service),
) -> APIResponse[StudentGradeResponse]:
    result = await service.update_grade(grade_id, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Grade {grade_id} updated to {result.score}",
    )


@router.get("/grades/{grade_id}/audit-logs", status_code=200,
            summary="Lịch sử thay đổi điểm")
async def get_grade_audit_logs(
    grade_id: int,
    service: GradingService = Depends(get_service),
) -> APIResponse:
    results = await service.get_audit_logs(grade_id)
    return APIResponse.success(
        data=[r.model_dump() for r in results],
        detail=f"Retrieved {len(results)} audit log(s) for grade {grade_id}",
    )


@router.get("/class-subjects/{cs_id}/grades", status_code=200,
            summary="Tất cả điểm trong 1 class-subject")
async def list_grades_by_class_subject(
    cs_id: int,
    grade_component_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    service: GradingService = Depends(get_service),
) -> APIResponse[StudentGradeListResponse]:
    result = await service.list_grades_by_class_subject(
        cs_id, grade_component_id, page, page_size
    )
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} grade(s) for class-subject {cs_id}",
    )


# ---------------------------------------------------------------------------
# Reports & Statistics
# ---------------------------------------------------------------------------

@router.get("/students/{student_id}/report", status_code=200,
            summary="Báo cáo điểm của học sinh theo học kỳ")
async def get_student_report(
    student_id: int,
    semester: Optional[int] = Query(None, ge=1, le=2),
    academic_year: Optional[str] = Query(None),
    service: GradingService = Depends(get_service),
) -> APIResponse[StudentReportResponse]:
    result = await service.get_student_report(student_id, semester, academic_year)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Report for student {student_id}",
    )


@router.get("/class-subjects/{cs_id}/statistics", status_code=200,
            summary="Thống kê điểm lớp: phân bố xếp loại, điểm TB/max/min")
async def get_class_statistics(
    cs_id: int,
    service: GradingService = Depends(get_service),
) -> APIResponse[GradeStatisticsResponse]:
    result = await service.get_class_statistics(cs_id)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Statistics for class-subject {cs_id}",
    )
