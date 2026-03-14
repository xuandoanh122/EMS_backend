"""
Student Service – business logic layer.

Responsibilities:
  - Orchestrate CRUD operations using StudentRepository.
  - Enforce business rules:
      * Auto-generate student_code = StudYYMMxxx.
      * Uniqueness of email, national_id.
      * Valid status transitions (e.g. graduated → active is forbidden).
      * Integrated enrollment on create (class_ids) within 1 DB Transaction.
  - Raise domain-specific exceptions from app.core.exceptions.student.
  - Never access the database directly (always via repository).
"""

import math
from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.student import (
    StudentAlreadyExistsException,
    StudentNotFoundException,
    StudentStatusTransitionException,
)
from app.modules.student.dto import (
    EnrollmentCreateResult,
    EnrollmentSummary,
    StudentCreateRequest,
    StudentCreateResponse,
    StudentDetailResponse,
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
        self._session = session
        self._repo = StudentRepository(session)

    # ------------------------------------------------------------------
    # CREATE – với tích hợp enrollment (1 Transaction)
    # ------------------------------------------------------------------

    async def create_student(self, data: StudentCreateRequest) -> StudentCreateResponse:
        """
        Create a new student profile, optionally enrolling into classrooms.

        Business rules:
          - student_code is AUTO-GENERATED: StudYYMMxxx (not from FE).
          - email must be unique among active students (if provided).
          - national_id must be unique if provided.
          - If class_ids provided: enroll in transaction; partial failure OK
            (student is still created, failed enrollments reported).
        """
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

        # Auto-generate student_code
        now = datetime.now()
        yymm = now.strftime("%y%m")   # VD: "2603" cho tháng 03/2026
        student_code = await self._repo.generate_student_code(yymm)

        student = Student(
            student_code=student_code,
            full_name=data.full_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            national_id=data.national_id,
            email=str(data.email) if data.email else None,
            phone_number=data.phone_number,
            address=data.address,
            enrollment_date=data.enrollment_date,
            academic_status=data.academic_status,
            parent_full_name=data.parent_full_name,
            parent_phone=data.parent_phone,
            parent_email=str(data.parent_email) if data.parent_email else None,
            medical_notes=data.medical_notes,
        )

        # Flush để lấy student.id (chưa commit)
        created = await self._repo.create(student)

        # ── Enroll vào các lớp (nếu có class_ids) ────────────────────
        enrollment_results: List[EnrollmentCreateResult] = []

        if data.class_ids:
            from app.modules.classroom.entity import (
                Classroom,
                EnrollmentStatus,
                EnrollmentType,
                StudentClassEnrollment,
            )
            from sqlalchemy import select

            for class_id in data.class_ids:
                try:
                    # Lấy classroom
                    cls_result = await self._session.execute(
                        select(Classroom).where(
                            Classroom.id == class_id,
                            Classroom.is_active == True,
                        )
                    )
                    classroom = cls_result.scalars().first()

                    if not classroom:
                        enrollment_results.append(EnrollmentCreateResult(
                            classroom_id=class_id,
                            classroom_name=f"ID:{class_id}",
                            status="failed",
                            reason="ClassroomNotFound",
                        ))
                        continue

                    # Kiểm tra capacity
                    from sqlalchemy import func
                    cnt_result = await self._session.execute(
                        select(func.count(StudentClassEnrollment.id)).where(
                            StudentClassEnrollment.classroom_id == class_id,
                            StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
                            StudentClassEnrollment.is_active == True,
                        )
                    )
                    current_count = cnt_result.scalar_one() or 0

                    if current_count >= classroom.max_capacity:
                        enrollment_results.append(EnrollmentCreateResult(
                            classroom_id=class_id,
                            classroom_name=classroom.class_name,
                            status="failed",
                            reason="ClassroomCapacityExceeded",
                        ))
                        continue

                    # Tạo enrollment
                    enrollment = StudentClassEnrollment(
                        student_id=created.id,
                        classroom_id=class_id,
                        enrollment_type=EnrollmentType.PRIMARY
                        if not enrollment_results  # Lớp đầu tiên = primary
                        else EnrollmentType.SUPPLEMENTARY,
                        enrolled_date=data.enrollment_date,
                    )
                    self._session.add(enrollment)
                    await self._session.flush()

                    enrollment_results.append(EnrollmentCreateResult(
                        classroom_id=class_id,
                        classroom_name=classroom.class_name,
                        status="success",
                    ))

                except Exception as e:
                    enrollment_results.append(EnrollmentCreateResult(
                        classroom_id=class_id,
                        classroom_name=f"ID:{class_id}",
                        status="failed",
                        reason=str(e),
                    ))

        # Commit toàn bộ transaction (student + enrollments)
        await self._repo.commit()

        return StudentCreateResponse(
            student_id=created.id,
            student_code=created.student_code,
            full_name=created.full_name,
            enrollments=enrollment_results,
        )

    # ------------------------------------------------------------------
    # READ – single (with enrollments)
    # ------------------------------------------------------------------

    async def get_student(self, student_code: str) -> StudentDetailResponse:
        """
        Retrieve a single active student by business code.
        Raises StudentNotFoundException if not found.
        Includes current_enrollments in response.
        """
        student = await self._repo.get_by_student_code(student_code)
        if not student:
            raise StudentNotFoundException(student_id=student_code)

        enrollments_data = await self._repo.get_enrollments_for_student(student.id)
        enrollment_list = [EnrollmentSummary(**e) for e in enrollments_data]

        base = StudentResponse.model_validate(student)
        return StudentDetailResponse(
            **base.model_dump(),
            current_enrollments=enrollment_list,
        )

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
          - student_code and class changes are NOT allowed via this endpoint.
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
