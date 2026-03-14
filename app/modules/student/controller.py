"""
Student Controller – FastAPI router layer.

Defines all REST endpoints for student management:
  POST   /students                         – Create student
  GET    /students                         – List students (paginated + filter)
  GET    /students/{student_code}          – Get single student
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
    summary="Create a new student",
    response_description="The created student profile",
)
async def create_student(
    data: StudentCreateRequest,
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentResponse]:
    """
    Create a new student profile.

    - **student_code** must be unique.
    - **email** must be unique if provided.
    - **national_id** must be unique if provided.
    """
    student = await service.create_student(data)
    return APIResponse.created(
        data=student.model_dump(),
        message="Student Created",
        detail=f"Student '{student.student_code}' has been created successfully",
    )


# ---------------------------------------------------------------------------
# GET /students  – List (paginated + filters)
# ---------------------------------------------------------------------------

@router.get(
    "",
    status_code=200,
    summary="List students with filters and pagination",
    response_description="Paginated list of students",
)
async def list_students(
    search: Optional[str] = Query(
        None, description="Search by student_code, full_name, or email"
    ),
    academic_status: Optional[StudentStatus] = Query(
        None, description="Filter by academic status"
    ),
    class_name: Optional[str] = Query(None, description="Filter by class name"),
    program_name: Optional[str] = Query(None, description="Filter by program name"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentListResponse]:
    params = StudentQueryParams(
        search=search,
        academic_status=academic_status,
        class_name=class_name,
        program_name=program_name,
        page=page,
        page_size=page_size,
    )
    result = await service.list_students(params)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} student(s) – page {page}/{result.total_pages}",
    )


# ---------------------------------------------------------------------------
# GET /students/{student_code}  – Get single
# ---------------------------------------------------------------------------

@router.get(
    "/{student_code}",
    status_code=200,
    summary="Get a single student by student code",
    response_description="Student profile",
)
async def get_student(
    student_code: str,
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentResponse]:
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
    summary="Partially update a student's profile",
    response_description="Updated student profile",
)
async def update_student(
    student_code: str,
    data: StudentUpdateRequest,
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentResponse]:
    """
    Update one or more fields of a student's profile.
    Fields not included in the request body are left unchanged.
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
    summary="Update a student's academic status",
    response_description="Student with updated academic status",
)
async def update_student_status(
    student_code: str,
    data: StudentStatusUpdateRequest,
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentResponse]:
    """
    Change the academic status of a student.

    Valid transitions:
    - **active** → preserved | suspended | graduated
    - **preserved** → active | suspended
    - **suspended** → active
    - **graduated** → *(no transitions – terminal state)*
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
    summary="Soft-delete a student",
    response_description="Confirmation of deletion",
)
async def delete_student(
    student_code: str,
    service: StudentService = Depends(get_student_service),
) -> APIResponse[StudentResponse]:
    """
    Soft-delete a student by setting `is_active = False`.
    The record is kept in the database for audit and historical reporting.
    """
    student = await service.delete_student(student_code)
    return APIResponse.success(
        data=student.model_dump(),
        detail=f"Student '{student_code}' has been deactivated",
    )
