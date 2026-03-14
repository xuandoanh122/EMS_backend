"""
Classroom Controller – FastAPI router.

Endpoints:
  POST   /classrooms                                         – Create classroom
  GET    /classrooms                                         – List classrooms
  GET    /classrooms/{class_code}                            – Get classroom
  PATCH  /classrooms/{class_code}                            – Update classroom
  DELETE /classrooms/{class_code}                            – Soft-delete classroom

  POST   /classrooms/{classroom_id}/enrollments              – Enroll student
  GET    /classrooms/{classroom_id}/enrollments              – List enrollments in class
  GET    /classrooms/enrollments/{enrollment_id}             – Get enrollment
  PATCH  /classrooms/enrollments/{enrollment_id}             – Update enrollment notes
  PATCH  /classrooms/enrollments/{enrollment_id}/status      – Update enrollment status
  GET    /classrooms/students/{student_id}/enrollments       – All enrollments of a student
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import require_role
from app.core.response import APIResponse
from app.modules.classroom.dto import (
    ClassroomCreateRequest,
    ClassroomListResponse,
    ClassroomQueryParams,
    ClassroomResponse,
    ClassroomStatusUpdateRequest,
    ClassroomUpdateRequest,
    EnrollmentCreateRequest,
    EnrollmentListResponse,
    EnrollmentResponse,
    EnrollmentStatusUpdateRequest,
    EnrollmentUpdateRequest,
)
from app.modules.classroom.entity import ClassType
from app.modules.classroom.service import ClassroomService

router = APIRouter(dependencies=[Depends(require_role("admin"))])


def get_service(session: AsyncSession = Depends(get_async_session)) -> ClassroomService:
    return ClassroomService(session)


# ---------------------------------------------------------------------------
# Classroom
# ---------------------------------------------------------------------------

@router.post("", status_code=201, summary="Tạo lớp học mới")
async def create_classroom(
    data: ClassroomCreateRequest,
    service: ClassroomService = Depends(get_service),
) -> APIResponse[ClassroomResponse]:
    result = await service.create_classroom(data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Classroom Created",
        detail=f"Classroom '{result.class_code}' created successfully",
    )


@router.get("", status_code=200, summary="Danh sách lớp học (có lọc + phân trang)")
async def list_classrooms(
    search: Optional[str] = Query(None, description="Tìm theo class_code hoặc class_name"),
    class_type: Optional[ClassType] = Query(None),
    academic_year: Optional[str] = Query(None),
    grade_level: Optional[int] = Query(None, ge=1, le=13),
    homeroom_teacher_id: Optional[int] = Query(None),
    has_capacity: Optional[bool] = Query(
        None, description="true = lớp chưa đầy, false = lớp đã đầy"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ClassroomService = Depends(get_service),
) -> APIResponse[ClassroomListResponse]:
    params = ClassroomQueryParams(
        search=search,
        class_type=class_type,
        academic_year=academic_year,
        grade_level=grade_level,
        homeroom_teacher_id=homeroom_teacher_id,
        has_capacity=has_capacity,
        page=page,
        page_size=page_size,
    )
    result = await service.list_classrooms(params)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} classroom(s) – page {page}/{result.total_pages}",
    )


@router.get("/students/{student_id}/enrollments", status_code=200,
            summary="Tất cả lớp mà học sinh đang/đã học")
async def list_student_enrollments(
    student_id: int,
    service: ClassroomService = Depends(get_service),
) -> APIResponse:
    result = await service.list_enrollments_by_student(student_id)
    return APIResponse.success(
        data=[r.model_dump() for r in result],
        detail=f"Retrieved {len(result)} enrollment(s) for student {student_id}",
    )


@router.get("/enrollments/{enrollment_id}", status_code=200, summary="Chi tiết enrollment")
async def get_enrollment(
    enrollment_id: int,
    service: ClassroomService = Depends(get_service),
) -> APIResponse[EnrollmentResponse]:
    result = await service.get_enrollment(enrollment_id)
    return APIResponse.success(data=result.model_dump())


@router.patch("/enrollments/{enrollment_id}", status_code=200,
              summary="Cập nhật ghi chú enrollment")
async def update_enrollment(
    enrollment_id: int,
    data: EnrollmentUpdateRequest,
    service: ClassroomService = Depends(get_service),
) -> APIResponse[EnrollmentResponse]:
    result = await service.update_enrollment(enrollment_id, data)
    return APIResponse.success(data=result.model_dump())


@router.patch("/enrollments/{enrollment_id}/status", status_code=200,
              summary="Đổi trạng thái enrollment (transferred/withdrawn/completed)")
async def update_enrollment_status(
    enrollment_id: int,
    data: EnrollmentStatusUpdateRequest,
    service: ClassroomService = Depends(get_service),
) -> APIResponse[EnrollmentResponse]:
    result = await service.update_enrollment_status(enrollment_id, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Enrollment {enrollment_id} status → '{data.new_status.value}'",
    )


# ---------------------------------------------------------------------------
# Enrollment (nested under classroom_id) – phải đứng TRƯỚC /{class_code}
# ---------------------------------------------------------------------------

@router.post("/{class_code}/enrollments", status_code=201,
             summary="Đăng ký học sinh vào lớp")
async def create_enrollment(
    class_code: str,
    data: EnrollmentCreateRequest,
    service: ClassroomService = Depends(get_service),
) -> APIResponse[EnrollmentResponse]:
    result = await service.create_enrollment_by_code(class_code, data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Enrollment Created",
        detail=f"Student {result.student_id} enrolled in classroom '{class_code}'",
    )


@router.get("/{class_code}/enrollments", status_code=200,
            summary="Danh sách học sinh trong lớp")
async def list_class_enrollments(
    class_code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="Lọc theo status enrollment"),
    service: ClassroomService = Depends(get_service),
) -> APIResponse[EnrollmentListResponse]:
    result = await service.list_enrollments_by_class_code(class_code, page, page_size)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} enrollment(s) in classroom '{class_code}'",
    )


@router.get("/{class_code}", status_code=200, summary="Chi tiết lớp học theo mã lớp")
async def get_classroom(
    class_code: str,
    service: ClassroomService = Depends(get_service),
) -> APIResponse[ClassroomResponse]:
    result = await service.get_classroom(class_code)
    return APIResponse.success(data=result.model_dump())


@router.patch("/{class_code}", status_code=200, summary="Cập nhật thông tin lớp học")
async def update_classroom(
    class_code: str,
    data: ClassroomUpdateRequest,
    service: ClassroomService = Depends(get_service),
) -> APIResponse[ClassroomResponse]:
    result = await service.update_classroom(class_code, data)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Classroom '{class_code}' updated",
    )


@router.patch("/{class_code}/status", status_code=200, summary="Cáº­p nháº­t tráº¡ng thÃ¡i lá»›p")
async def update_classroom_status(
    class_code: str,
    data: ClassroomStatusUpdateRequest,
    service: ClassroomService = Depends(get_service),
) -> APIResponse[ClassroomResponse]:
    result = await service.update_classroom_status(class_code, data)
    status_label = "active" if data.is_active else "inactive"
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Classroom '{class_code}' status â†’ {status_label}",
    )


@router.delete("/{class_code}", status_code=200, summary="Xóa mềm lớp học")
async def delete_classroom(
    class_code: str,
    service: ClassroomService = Depends(get_service),
) -> APIResponse[ClassroomResponse]:
    result = await service.delete_classroom(class_code)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Classroom '{class_code}' deactivated",
    )
