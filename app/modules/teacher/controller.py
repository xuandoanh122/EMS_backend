"""
Teacher Controller – FastAPI router layer.

Endpoints:
  POST   /teachers                          – Create teacher
  GET    /teachers                          – List teachers (paginated + filter)
  GET    /teachers/{teacher_code}           – Get single teacher
  PATCH  /teachers/{teacher_code}           – Partial update teacher profile
  PATCH  /teachers/{teacher_code}/status    – Update employment status
  DELETE /teachers/{teacher_code}           – Soft-delete teacher
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.response import APIResponse
from app.modules.teacher.dto import (
    TeacherCreateRequest,
    TeacherListResponse,
    TeacherQueryParams,
    TeacherResponse,
    TeacherStatusUpdateRequest,
    TeacherUpdateRequest,
)
from app.modules.teacher.entity import TeacherStatus
from app.modules.teacher.service import TeacherService

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_teacher_service(
    session: AsyncSession = Depends(get_async_session),
) -> TeacherService:
    return TeacherService(session)


# ---------------------------------------------------------------------------
# POST /teachers  – Create
# ---------------------------------------------------------------------------

@router.post(
    "",
    status_code=201,
    summary="Create a new teacher",
    response_description="The created teacher profile",
)
async def create_teacher(
    data: TeacherCreateRequest,
    service: TeacherService = Depends(get_teacher_service),
) -> APIResponse[TeacherResponse]:
    """
    Create a new teacher profile.

    - **teacher_code** must be unique.
    - **email** must be unique if provided.
    - **national_id** must be unique if provided.
    """
    teacher = await service.create_teacher(data)
    return APIResponse.created(
        data=teacher.model_dump(),
        message="Teacher Created",
        detail=f"Teacher '{teacher.teacher_code}' has been created successfully",
    )


# ---------------------------------------------------------------------------
# GET /teachers  – List
# ---------------------------------------------------------------------------

@router.get(
    "",
    status_code=200,
    summary="List teachers with filters and pagination",
    response_description="Paginated list of teachers",
)
async def list_teachers(
    search: Optional[str] = Query(
        None, description="Search by teacher_code, full_name, or email"
    ),
    employment_status: Optional[TeacherStatus] = Query(
        None, description="Filter by employment status"
    ),
    department: Optional[str] = Query(None, description="Filter by department"),
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    service: TeacherService = Depends(get_teacher_service),
) -> APIResponse[TeacherListResponse]:
    params = TeacherQueryParams(
        search=search,
        employment_status=employment_status,
        department=department,
        specialization=specialization,
        page=page,
        page_size=page_size,
    )
    result = await service.list_teachers(params)
    return APIResponse.success(
        data=result.model_dump(),
        detail=f"Retrieved {result.total} teacher(s) – page {page}/{result.total_pages}",
    )


# ---------------------------------------------------------------------------
# GET /teachers/{teacher_code}  – Get single
# ---------------------------------------------------------------------------

@router.get(
    "/{teacher_code}",
    status_code=200,
    summary="Get a single teacher by teacher code",
    response_description="Teacher profile",
)
async def get_teacher(
    teacher_code: str,
    service: TeacherService = Depends(get_teacher_service),
) -> APIResponse[TeacherResponse]:
    teacher = await service.get_teacher(teacher_code)
    return APIResponse.success(
        data=teacher.model_dump(),
        detail=f"Retrieved teacher '{teacher_code}' successfully",
    )


# ---------------------------------------------------------------------------
# PATCH /teachers/{teacher_code}  – Partial update
# ---------------------------------------------------------------------------

@router.patch(
    "/{teacher_code}",
    status_code=200,
    summary="Partially update a teacher's profile",
    response_description="Updated teacher profile",
)
async def update_teacher(
    teacher_code: str,
    data: TeacherUpdateRequest,
    service: TeacherService = Depends(get_teacher_service),
) -> APIResponse[TeacherResponse]:
    """Update one or more fields of a teacher's profile. Fields not included are left unchanged."""
    teacher = await service.update_teacher(teacher_code, data)
    return APIResponse.success(
        data=teacher.model_dump(),
        detail=f"Teacher '{teacher_code}' profile updated successfully",
    )


# ---------------------------------------------------------------------------
# PATCH /teachers/{teacher_code}/status  – Status transition
# ---------------------------------------------------------------------------

@router.patch(
    "/{teacher_code}/status",
    status_code=200,
    summary="Update a teacher's employment status",
    response_description="Teacher with updated employment status",
)
async def update_teacher_status(
    teacher_code: str,
    data: TeacherStatusUpdateRequest,
    service: TeacherService = Depends(get_teacher_service),
) -> APIResponse[TeacherResponse]:
    """
    Change the employment status of a teacher.

    Valid transitions:
    - **active** → on_leave | resigned | retired
    - **on_leave** → active | resigned
    - **resigned** → *(terminal state)*
    - **retired** → *(terminal state)*
    """
    teacher = await service.update_teacher_status(teacher_code, data)
    return APIResponse.success(
        data=teacher.model_dump(),
        detail=f"Teacher '{teacher_code}' status updated to '{data.new_status.value}'",
    )


# ---------------------------------------------------------------------------
# DELETE /teachers/{teacher_code}  – Soft delete
# ---------------------------------------------------------------------------

@router.delete(
    "/{teacher_code}",
    status_code=200,
    summary="Soft-delete a teacher",
    response_description="Confirmation of deletion",
)
async def delete_teacher(
    teacher_code: str,
    service: TeacherService = Depends(get_teacher_service),
) -> APIResponse[TeacherResponse]:
    """Soft-delete a teacher by setting `is_active = False`."""
    teacher = await service.delete_teacher(teacher_code)
    return APIResponse.success(
        data=teacher.model_dump(),
        detail=f"Teacher '{teacher_code}' has been deactivated",
    )
