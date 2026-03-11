"""
Student Service – business logic layer.

Responsibilities:
  - Orchestrate CRUD operations using StudentRepository.
  - Enforce business rules:
      * Uniqueness of student_code, email, national_id.
      * Valid status transitions (e.g. graduated → active is forbidden).
      * Preservation-return curriculum change check.
  - Raise domain-specific exceptions from app.core.exceptions.student.
  - Never access the database directly (always via repository).
"""

import math
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.student import (
    PreservationReturnException,
    StudentAlreadyExistsException,
    StudentNotFoundException,
    StudentStatusTransitionException,
)
from app.modules.student.dto import (
    StudentCreateRequest,
    StudentListResponse,
    StudentQueryParams,
    StudentResponse,
    StudentStatusUpdateRequest,
    StudentUpdateRequest,
)
from app.modules.student.entity import Student, StudentStatus, VALID_STATUS_TRANSITIONS
from app.modules.student.repository import StudentRepository


class StudentService:
    """
    Handles all business logic for student management.
    Injected with an AsyncSession and creates its own Repository instance.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = StudentRepository(session)

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def create_student(self, data: StudentCreateRequest) -> StudentResponse:
        """
        Create a new student profile.

        Business rules:
          - student_code must be globally unique (even among soft-deleted records).
          - email must be unique among active students (if provided).
          - national_id must be unique if provided.
        """
        # Check for duplicate student_code (include soft-deleted to prevent recycling)
        if await self._repo.exists_by_student_code(data.student_code):
            raise StudentAlreadyExistsException(student_code=data.student_code)

        # Check for duplicate email among active students
        if data.email:
            existing_email = await self._repo.get_by_email(str(data.email))
            if existing_email:
                raise StudentAlreadyExistsException(
                    student_code=f"email:{data.email}"
                )

        # Check for duplicate national_id
        if data.national_id:
            existing_nid = await self._repo.get_by_national_id(data.national_id)
            if existing_nid:
                raise StudentAlreadyExistsException(
                    student_code=f"national_id:{data.national_id}"
                )

        student = Student(
            student_code=data.student_code,
            full_name=data.full_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            national_id=data.national_id,
            email=str(data.email) if data.email else None,
            phone_number=data.phone_number,
            address=data.address,
            enrollment_date=data.enrollment_date,
            academic_status=data.academic_status,
            class_name=data.class_name,
            program_name=data.program_name,
            parent_full_name=data.parent_full_name,
            parent_phone=data.parent_phone,
            parent_email=str(data.parent_email) if data.parent_email else None,
            medical_notes=data.medical_notes,
        )

        created = await self._repo.create(student)
        return StudentResponse.model_validate(created)

    # ------------------------------------------------------------------
    # READ – single
    # ------------------------------------------------------------------

    async def get_student(self, student_code: str) -> StudentResponse:
        """
        Retrieve a single active student by business code.
        Raises StudentNotFoundException if not found.
        """
        student = await self._repo.get_by_student_code(student_code)
        if not student:
            raise StudentNotFoundException(student_id=student_code)
        return StudentResponse.model_validate(student)

    # ------------------------------------------------------------------
    # READ – list
    # ------------------------------------------------------------------

    async def list_students(
        self, params: StudentQueryParams
    ) -> StudentListResponse:
        """Return a paginated, filtered list of active students."""
        students, total = await self._repo.list_students(params)
        total_pages = math.ceil(total / params.page_size) if total > 0 else 1
        return StudentListResponse(
            items=[StudentResponse.model_validate(s) for s in students],
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

    # ------------------------------------------------------------------
    # UPDATE – partial profile update
    # ------------------------------------------------------------------

    async def update_student(
        self, student_code: str, data: StudentUpdateRequest
    ) -> StudentResponse:
        """
        Partially update a student profile (PATCH semantics).
        Only fields provided in data will be changed.

        Business rules:
          - student must exist and be active.
          - If email changes, new email must not be taken by another student.
        """
        student = await self._repo.get_by_student_code(student_code)
        if not student:
            raise StudentNotFoundException(student_id=student_code)

        # Guard: email uniqueness (skip if email not being changed)
        if data.email and str(data.email) != student.email:
            existing_email = await self._repo.get_by_email(str(data.email))
            if existing_email and existing_email.id != student.id:
                raise StudentAlreadyExistsException(
                    student_code=f"email:{data.email}"
                )

        updated = await self._repo.update(student, data)
        return StudentResponse.model_validate(updated)

    # ------------------------------------------------------------------
    # UPDATE – status transition
    # ------------------------------------------------------------------

    async def update_student_status(
        self, student_code: str, data: StudentStatusUpdateRequest
    ) -> StudentResponse:
        """
        Change the academic status of a student.

        Business rules:
          - Validates status transition against VALID_STATUS_TRANSITIONS matrix.
          - Special case: if returning from PRESERVED → ACTIVE, triggers
            the preservation-return check (curriculum change warning).
        """
        student = await self._repo.get_by_student_code(student_code)
        if not student:
            raise StudentNotFoundException(student_id=student_code)

        current_status = student.academic_status
        new_status = data.new_status

        # No-op check
        if current_status == new_status:
            return StudentResponse.model_validate(student)

        # Validate transition
        allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, set())
        if new_status not in allowed_transitions:
            raise StudentStatusTransitionException(
                current_status=current_status.value,
                target_status=new_status.value,
            )

        # Edge case: returning from preservation
        if (
            current_status == StudentStatus.PRESERVED
            and new_status == StudentStatus.ACTIVE
        ):
            self._check_preservation_return(student)

        updated = await self._repo.update_status(student, new_status)
        return StudentResponse.model_validate(updated)

    # ------------------------------------------------------------------
    # DELETE (soft)
    # ------------------------------------------------------------------

    async def delete_student(self, student_code: str) -> StudentResponse:
        """
        Soft-delete a student (set is_active=False).
        The record is preserved for audit/historical purposes.
        Raises StudentNotFoundException if the student does not exist.
        """
        student = await self._repo.get_by_student_code(student_code)
        if not student:
            raise StudentNotFoundException(student_id=student_code)

        deleted = await self._repo.soft_delete(student)
        return StudentResponse.model_validate(deleted)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_preservation_return(self, student: Student) -> None:
        """
        Edge case: student returning from preservation.
        Raise PreservationReturnException if the student's stored program_name
        is missing – which may indicate the curriculum has been updated and
        the program reference is no longer valid.

        In a full implementation this would compare the student's original
        curriculum version against the current active curriculum.
        """
        if not student.program_name:
            raise PreservationReturnException(
                student_id=student.student_code,
                reason=(
                    "No program/curriculum is associated with this student. "
                    "The original curriculum may have been removed or updated. "
                    "Please review and assign a valid program before reactivating."
                ),
            )
