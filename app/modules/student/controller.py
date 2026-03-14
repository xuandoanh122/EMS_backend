"""
Student Controller – FastAPI router layer.

Defines all REST endpoints for student management:
  POST   /students                         – Create student (auto-generate code + optional enroll)
  GET    /students                         – List students (paginated + filter)
  GET    /students/{student_code}          – Get single student with enrollments
  PATCH  /students/{student_code}          – Partial update student profile
  PATCH  /students/{student_code}/status   – Update academic status
  DELETE /students/{student_code}          – Soft-delete student

Controller responsibilities:
  - Receive HTTP requests and validate input via Pydantic DTOs.
  - Call StudentService (never Repository directly).
  - Return standardized APIResponse.
  - No business logic here.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import require_role
from app.core.response import APIResponse
from app.modules.student.dto import (
    StudentCreateRequest,
    StudentCreateResponse,
    StudentDetailResponse,
    StudentListResponse,
    StudentQueryParams,
    StudentResponse,
    StudentStatusUpdateRequest,
    StudentUpdateRequest,
)
from app.modules.student.entity import StudentStatus
from app.modules.student.service import StudentService

router = APIRouter(dependencies=[Depends(require_role("admin"))])


# ---------------------------------------------------------------------------
# Dependency – DB Session
# ---------------------------------------------------------------------------

def get_student_service(
    session: AsyncSession = Depends(get_async_session),
) -> StudentService:
    """Dependency that provides a StudentService with an injected session."""
    return StudentService(session)


# ---------------------------------------------------------------------------
# POST /students  – Create
# ---------------------------------------------------------------------------

@router.post(
    "",
    status_code=201,
    summary="Tạo học sinh mới (student_code tự sinh – FE không cần gửi)",
    response_description="Học sinh vừa tạo kèm kết quả xếp lớp",
)
async def create_student(
    data: StudentCreateRequest,
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentCreateResponse]:
    """
    Tạo học sinh mới.

    - **student_code** được BE tự sinh theo format `StudYYMMxxx` – FE không gửi field này.
    - **class_ids** (optional): Danh sách classroom ID để enroll ngay khi tạo.
      Nếu bỏ qua, học sinh ở trạng thái "chờ xếp lớp".
    - Toàn bộ (tạo HS + xếp lớp) được bọc trong 1 DB Transaction.
    - Nếu 1 lớp bị đầy → ghi lỗi partial vào response, KHÔNG rollback toàn bộ.
    """
    result = await service.create_student(data)
    return APIResponse.created(
        data=result.model_dump(),
        message="Tạo học sinh thành công",
        detail=f"Học sinh '{result.student_code}' đã được tạo",
    )


# ---------------------------------------------------------------------------
# GET /students  – List (paginated + filters)
# ---------------------------------------------------------------------------

@router.get(
    "",
    status_code=200,
    summary="Danh sách học sinh (phân trang + lọc)",
    response_description="Paginated list of students",
)
async def list_students(
    search: Optional[str] = Query(
        None, description="Tìm theo student_code, full_name, hoặc email"
    ),
    academic_status: Optional[StudentStatus] = Query(
        None, description="Lọc theo trạng thái học vụ"
    ),
    has_enrollment: Optional[bool] = Query(
        None,
        description="true = đang có lớp, false = chưa có lớp (chờ xếp lớp)",
    ),
    classroom_id: Optional[int] = Query(
        None, description="Lọc học sinh trong 1 lớp cụ thể (theo classroom ID)"
    ),
    page: int = Query(1, ge=1, description="Số trang (bắt đầu từ 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Số item mỗi trang (tối đa 100)"),
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentListResponse]:
    params = StudentQueryParams(
        search=search,
        academic_status=academic_status,
        has_enrollment=has_enrollment,
        classroom_id=classroom_id,
        page=page,
        page_size=page_size,
    )
    result = await service.list_students(params)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} student(s) – page {page}/{result.total_pages}",
    )


# ---------------------------------------------------------------------------
# GET /students/{student_code}  – Get single (with enrollments)
# ---------------------------------------------------------------------------

@router.get(
    "/{student_code}",
    status_code=200,
    summary="Chi tiết 1 học sinh (bao gồm danh sách lớp đang học)",
    response_description="Student profile with current enrollments",
)
async def get_student(
    student_code: str,
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentDetailResponse]:
    student = await service.get_student(student_code)
    return APIResponse.success(
        data=student.model_dump(),
        detail=f"Retrieved student '{student_code}' successfully",
    )


# ---------------------------------------------------------------------------
# PATCH /students/{student_code}  – Partial update
# ---------------------------------------------------------------------------

@router.patch(
    "/{student_code}",
    status_code=200,
    summary="Cập nhật thông tin học sinh (partial update)",
    response_description="Updated student profile",
)
async def update_student(
    student_code: str,
    data: StudentUpdateRequest,
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentResponse]:
    """
    Cập nhật một hoặc nhiều field của học sinh.
    Các field không gửi sẽ được giữ nguyên.
    Lưu ý: KHÔNG cho phép sửa student_code. Thay đổi lớp học phải qua Enrollment API.
    """
    student = await service.update_student(student_code, data)
    return APIResponse.success(
        data=student.model_dump(),
        detail=f"Student '{student_code}' profile updated successfully",
    )


# ---------------------------------------------------------------------------
# PATCH /students/{student_code}/status  – Status transition
# ---------------------------------------------------------------------------

@router.patch(
    "/{student_code}/status",
    status_code=200,
    summary="Thay đổi trạng thái học vụ",
    response_description="Student with updated academic status",
)
async def update_student_status(
    student_code: str,
    data: StudentStatusUpdateRequest,
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentResponse]:
    """
    Chuyển trạng thái học vụ của học sinh.

    Các transition hợp lệ:
    - **active** → preserved | suspended | graduated
    - **preserved** → active | suspended
    - **suspended** → active
    - **graduated** → *(terminal – không chuyển được)*
    """
    student = await service.update_student_status(student_code, data)
    return APIResponse.success(
        data=student.model_dump(),
        detail=(
            f"Student '{student_code}' status updated to '{data.new_status.value}'"
        ),
    )


# ---------------------------------------------------------------------------
# DELETE /students/{student_code}  – Soft delete
# ---------------------------------------------------------------------------

@router.delete(
    "/{student_code}",
    status_code=200,
    summary="Soft-delete học sinh (is_active = false)",
    response_description="Confirmation of deletion",
)
async def delete_student(
    student_code: str,
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentResponse]:
    """
    Soft-delete học sinh bằng cách set `is_active = False`.
    Dữ liệu vẫn được giữ lại trong DB để audit / báo cáo lịch sử.
    """
    student = await service.delete_student(student_code)
    return APIResponse.success(
        data=student.model_dump(),
        detail=f"Student '{student_code}' has been deactivated",
    )
