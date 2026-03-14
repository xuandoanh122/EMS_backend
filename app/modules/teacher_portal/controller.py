"""
Teacher Portal Controller – FastAPI router.
"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import AuthContext, require_role
from app.core.response import APIResponse
from app.core.exceptions.teacher_portal import TeacherPortalValidationException
from app.modules.teacher_portal.dto import (
    AdminAttendanceBatchUpdateRequest,
    AttendanceBatchUpdateRequest,
    AttendanceBatchUpdateResponse,
    AttendanceMatrixResponse,
    ClassroomStudentsResponse,
    GradebookBatchUpdateRequest,
    GradebookBatchUpdateResponse,
    GradebookMatrixResponse,
    TeacherAssignmentListResponse,
    TeacherDashboardResponse,
    TimetableAdminListResponse,
    TimetableAdminResponse,
    TimetableCreateRequest,
    TimetableListResponse,
    TimetableUpdateRequest,
)
from app.modules.teacher_portal.service import TeacherPortalService

router = APIRouter()
admin_router = APIRouter()


def get_service(session: AsyncSession = Depends(get_async_session)) -> TeacherPortalService:
    return TeacherPortalService(session)


def get_teacher_context(user: AuthContext = Depends(require_role("teacher"))) -> AuthContext:
    if not user.teacher_id:
        raise TeacherPortalValidationException(detail="teacher_id is missing in token")
    return user


@router.get("/dashboard", status_code=200, summary="Teacher dashboard")
async def get_teacher_dashboard(
    user: AuthContext = Depends(get_teacher_context),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[TeacherDashboardResponse]:
    result = await service.get_dashboard(user.teacher_id)
    return APIResponse.success(data=result.model_dump(), detail="Teacher dashboard data")


@router.get("/assignments", status_code=200, summary="Teacher assignments")
async def list_assignments(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None, ge=1, le=2),
    user: AuthContext = Depends(get_teacher_context),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[TeacherAssignmentListResponse]:
    result = await service.list_assignments(user.teacher_id, academic_year, semester)
    return APIResponse.success(data=result.model_dump(), detail="Teacher assignments")


@router.get("/classrooms/{classroom_id}/students", status_code=200, summary="Classroom students")
async def list_classroom_students(
    classroom_id: int,
    user: AuthContext = Depends(get_teacher_context),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[ClassroomStudentsResponse]:
    result = await service.list_classroom_students(user.teacher_id, classroom_id)
    return APIResponse.success(data=result.model_dump(), detail="Classroom students")


@router.get("/gradebook/matrix", status_code=200, summary="Gradebook matrix")
async def get_gradebook_matrix(
    class_subject_id: int = Query(...),
    user: AuthContext = Depends(get_teacher_context),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[GradebookMatrixResponse]:
    result = await service.get_gradebook_matrix(user.teacher_id, class_subject_id)
    return APIResponse.success(data=result.model_dump(), detail="Gradebook matrix")


@router.patch("/gradebook/entries", status_code=200, summary="Gradebook batch upsert")
async def update_gradebook_entries(
    data: GradebookBatchUpdateRequest,
    user: AuthContext = Depends(get_teacher_context),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[GradebookBatchUpdateResponse]:
    result = await service.upsert_gradebook_entries(user.teacher_id, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Gradebook updated: +{result.created} created, {result.updated} updated",
    )


@router.get("/attendance/matrix", status_code=200, summary="Attendance matrix")
async def get_attendance_matrix(
    classroom_id: int = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    user: AuthContext = Depends(get_teacher_context),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[AttendanceMatrixResponse]:
    result = await service.get_attendance_matrix(user.teacher_id, classroom_id, date_from, date_to)
    return APIResponse.success(data=result.model_dump(), detail="Attendance matrix")


@router.patch("/attendance/entries", status_code=200, summary="Attendance batch update")
async def update_attendance_entries(
    data: AttendanceBatchUpdateRequest,
    user: AuthContext = Depends(get_teacher_context),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[AttendanceBatchUpdateResponse]:
    result = await service.upsert_attendance_entries(user.teacher_id, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Attendance updated: +{result.created} created, {result.updated} updated",
    )


@router.get("/timetable", status_code=200, summary="Teacher timetable")
async def get_timetable(
    from_date: datetime = Query(..., alias="from"),
    to_date: datetime = Query(..., alias="to"),
    view: Optional[str] = Query(None, description="week | month"),
    user: AuthContext = Depends(get_teacher_context),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[TimetableListResponse]:
    _ = view
    result = await service.list_timetable(user.teacher_id, from_date, to_date)
    return APIResponse.success(data=result.model_dump(), detail="Timetable")


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@admin_router.get("/timetable", status_code=200, summary="Admin list timetable")
async def admin_list_timetable(
    from_date: datetime = Query(..., alias="from"),
    to_date: datetime = Query(..., alias="to"),
    teacher_id: Optional[int] = Query(None),
    _: AuthContext = Depends(require_role("admin")),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[TimetableAdminListResponse]:
    result = await service.admin_list_timetable(from_date, to_date, teacher_id)
    return APIResponse.success(data=result.model_dump(), detail="Admin timetable list")


@admin_router.post("/timetable", status_code=201, summary="Admin create timetable")
async def admin_create_timetable(
    data: TimetableCreateRequest,
    _: AuthContext = Depends(require_role("admin")),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[TimetableAdminResponse]:
    result = await service.admin_create_timetable(data)
    return APIResponse.created(data=result.model_dump(), detail="Timetable created")


@admin_router.patch("/timetable/{entry_id}", status_code=200, summary="Admin update timetable")
async def admin_update_timetable(
    entry_id: int,
    data: TimetableUpdateRequest,
    _: AuthContext = Depends(require_role("admin")),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[TimetableAdminResponse]:
    result = await service.admin_update_timetable(entry_id, data)
    return APIResponse.success(data=result.model_dump(), detail="Timetable updated")


@admin_router.delete("/timetable/{entry_id}", status_code=200, summary="Admin delete timetable")
async def admin_delete_timetable(
    entry_id: int,
    _: AuthContext = Depends(require_role("admin")),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[TimetableAdminResponse]:
    result = await service.admin_delete_timetable(entry_id)
    return APIResponse.success(data=result.model_dump(), detail="Timetable deleted")


@admin_router.get("/attendance/matrix", status_code=200, summary="Admin attendance matrix")
async def admin_attendance_matrix(
    classroom_id: int = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    _: AuthContext = Depends(require_role("admin")),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[AttendanceMatrixResponse]:
    result = await service.admin_get_attendance_matrix(classroom_id, date_from, date_to)
    return APIResponse.success(data=result.model_dump(), detail="Admin attendance matrix")


@admin_router.patch("/attendance/entries", status_code=200, summary="Admin attendance batch update")
async def admin_attendance_entries(
    data: AdminAttendanceBatchUpdateRequest,
    _: AuthContext = Depends(require_role("admin")),
    service: TeacherPortalService = Depends(get_service),
) -> APIResponse[AttendanceBatchUpdateResponse]:
    result = await service.admin_upsert_attendance_entries(data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Attendance updated: +{result.created} created, {result.updated} updated",
    )
