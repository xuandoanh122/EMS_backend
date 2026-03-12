"""
Teacher Service – business logic layer.

Responsibilities:
  - Orchestrate CRUD operations using TeacherRepository.
  - Enforce business rules:
      * Uniqueness of teacher_code, email, national_id.
      * Valid employment status transitions.
  - Raise domain-specific exceptions from app.core.exceptions.teacher.
  - Never access the database directly (always via repository).
"""

import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.teacher import (
    TeacherAlreadyExistsException,
    TeacherNotFoundException,
    TeacherAssignmentException,
)
from app.modules.teacher.dto import (
    TeacherCreateRequest,
    TeacherListResponse,
    TeacherQueryParams,
    TeacherResponse,
    TeacherStatusUpdateRequest,
    TeacherUpdateRequest,
)
from app.modules.teacher.entity import Teacher, VALID_TEACHER_STATUS_TRANSITIONS
from app.modules.teacher.repository import TeacherRepository


class TeacherService:
    """
    Handles all business logic for teacher management.
    Injected with an AsyncSession and creates its own Repository instance.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = TeacherRepository(session)

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def create_teacher(self, data: TeacherCreateRequest) -> TeacherResponse:
        """
        Create a new teacher profile.

        Business rules:
          - teacher_code must be globally unique (even among soft-deleted records).
          - email must be unique among active teachers (if provided).
          - national_id must be unique if provided.
        """
        if await self._repo.exists_by_teacher_code(data.teacher_code):
            raise TeacherAlreadyExistsException(identifier=data.teacher_code)

        if data.email:
            existing_email = await self._repo.get_by_email(str(data.email))
            if existing_email:
                raise TeacherAlreadyExistsException(
                    identifier=f"email:{data.email}"
                )

        if data.national_id:
            existing_nid = await self._repo.get_by_national_id(data.national_id)
            if existing_nid:
                raise TeacherAlreadyExistsException(
                    identifier=f"national_id:{data.national_id}"
                )

        teacher = Teacher(
            teacher_code=data.teacher_code,
            full_name=data.full_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            national_id=data.national_id,
            email=str(data.email) if data.email else None,
            phone_number=data.phone_number,
            address=data.address,
            specialization=data.specialization,
            qualification=data.qualification,
            join_date=data.join_date,
            employment_status=data.employment_status,
            department=data.department,
        )

        created = await self._repo.create(teacher)
        return TeacherResponse.model_validate(created)

    # ------------------------------------------------------------------
    # READ – single
    # ------------------------------------------------------------------

    async def get_teacher(self, teacher_code: str) -> TeacherResponse:
        """
        Retrieve a single active teacher by business code.
        Raises TeacherNotFoundException if not found.
        """
        teacher = await self._repo.get_by_teacher_code(teacher_code)
        if not teacher:
            raise TeacherNotFoundException(teacher_id=teacher_code)
        return TeacherResponse.model_validate(teacher)

    # ------------------------------------------------------------------
    # READ – list
    # ------------------------------------------------------------------

    async def list_teachers(self, params: TeacherQueryParams) -> TeacherListResponse:
        """Return a paginated, filtered list of active teachers."""
        teachers, total = await self._repo.list_teachers(params)
        total_pages = math.ceil(total / params.page_size) if total > 0 else 1
        return TeacherListResponse(
            items=[TeacherResponse.model_validate(t) for t in teachers],
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

    # ------------------------------------------------------------------
    # UPDATE – partial profile update
    # ------------------------------------------------------------------

    async def update_teacher(
        self, teacher_code: str, data: TeacherUpdateRequest
    ) -> TeacherResponse:
        """
        Partially update a teacher profile (PATCH semantics).

        Business rules:
          - teacher must exist and be active.
          - If email changes, new email must not be taken by another teacher.
        """
        teacher = await self._repo.get_by_teacher_code(teacher_code)
        if not teacher:
            raise TeacherNotFoundException(teacher_id=teacher_code)

        if data.email and str(data.email) != teacher.email:
            existing_email = await self._repo.get_by_email(str(data.email))
            if existing_email and existing_email.id != teacher.id:
                raise TeacherAlreadyExistsException(
                    identifier=f"email:{data.email}"
                )

        updated = await self._repo.update(teacher, data)
        return TeacherResponse.model_validate(updated)

    # ------------------------------------------------------------------
    # UPDATE – status transition
    # ------------------------------------------------------------------

    async def update_teacher_status(
        self, teacher_code: str, data: TeacherStatusUpdateRequest
    ) -> TeacherResponse:
        """
        Change the employment status of a teacher.

        Business rules:
          - Validates transition against VALID_TEACHER_STATUS_TRANSITIONS matrix.
          - resigned and retired are terminal states.
        """
        teacher = await self._repo.get_by_teacher_code(teacher_code)
        if not teacher:
            raise TeacherNotFoundException(teacher_id=teacher_code)

        current_status = teacher.employment_status
        new_status = data.new_status

        if current_status == new_status:
            return TeacherResponse.model_validate(teacher)

        allowed = VALID_TEACHER_STATUS_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise TeacherAssignmentException(
                teacher_id=teacher_code,
                reason=(
                    f"Cannot transition from '{current_status.value}' "
                    f"to '{new_status.value}'. "
                    f"Allowed: {[s.value for s in allowed] or 'none (terminal state)'}"
                ),
            )

        updated = await self._repo.update_status(teacher, new_status)
        return TeacherResponse.model_validate(updated)

    # ------------------------------------------------------------------
    # DELETE (soft)
    # ------------------------------------------------------------------

    async def delete_teacher(self, teacher_code: str) -> TeacherResponse:
        """
        Soft-delete a teacher (set is_active=False).
        Raises TeacherNotFoundException if not found.
        """
        teacher = await self._repo.get_by_teacher_code(teacher_code)
        if not teacher:
            raise TeacherNotFoundException(teacher_id=teacher_code)

        deleted = await self._repo.soft_delete(teacher)
        return TeacherResponse.model_validate(deleted)
