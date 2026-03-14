"""
Lookup Controller - lightweight endpoints for dropdowns/selectors.

RBAC: admin only.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import require_role
from app.core.response import APIResponse
from app.modules.lookups.dto import (
    ClassroomLookupListResponse,
    StudentLookupListResponse,
    SubjectLookupListResponse,
    TeacherLookupListResponse,
)
from app.modules.lookups.service import LookupsService

router = APIRouter(dependencies=[Depends(require_role("admin"))])


def get_service(session: AsyncSession = Depends(get_async_session)) -> LookupsService:
    return LookupsService(session)


@router.get("/teachers", status_code=200, summary="Lookup teachers")
async def lookup_teachers(
    search: Optional[str] = Query(None, description="Search by teacher_code or full_name"),
    service: LookupsService = Depends(get_service),
) -> APIResponse[TeacherLookupListResponse]:
    result = await service.list_teachers(search)
    return APIResponse.success(data=result.model_dump(), detail="Teacher lookup list")


@router.get("/classrooms", status_code=200, summary="Lookup classrooms")
async def lookup_classrooms(
    search: Optional[str] = Query(None, description="Search by class_code or class_name"),
    service: LookupsService = Depends(get_service),
) -> APIResponse[ClassroomLookupListResponse]:
    result = await service.list_classrooms(search)
    return APIResponse.success(data=result.model_dump(), detail="Classroom lookup list")


@router.get("/students", status_code=200, summary="Lookup students")
async def lookup_students(
    search: Optional[str] = Query(None, description="Search by student_code or full_name"),
    service: LookupsService = Depends(get_service),
) -> APIResponse[StudentLookupListResponse]:
    result = await service.list_students(search)
    return APIResponse.success(data=result.model_dump(), detail="Student lookup list")


@router.get("/subjects", status_code=200, summary="Lookup subjects")
async def lookup_subjects(
    search: Optional[str] = Query(None, description="Search by subject_code or subject_name"),
    service: LookupsService = Depends(get_service),
) -> APIResponse[SubjectLookupListResponse]:
    result = await service.list_subjects(search)
    return APIResponse.success(data=result.model_dump(), detail="Subject lookup list")
