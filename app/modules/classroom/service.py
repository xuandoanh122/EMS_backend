"""
Classroom Service – business logic layer.
"""

import math
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.classroom import (
    ClassroomAlreadyExistsException,
    ClassroomCapacityExceededException,
    ClassroomNotFoundException,
    DuplicatePrimaryEnrollmentException,
    EnrollmentAlreadyExistsException,
    EnrollmentNotFoundException,
    InvalidEnrollmentTransitionException,
)
from app.modules.classroom.dto import (
    ClassroomCreateRequest,
    ClassroomListResponse,
    ClassroomQueryParams,
    ClassroomResponse,
    ClassroomUpdateRequest,
    EnrollmentCreateRequest,
    EnrollmentListResponse,
    EnrollmentResponse,
    EnrollmentStatusUpdateRequest,
    EnrollmentUpdateRequest,
)
from app.modules.classroom.entity import (
    Classroom,
    EnrollmentType,
    StudentClassEnrollment,
    VALID_ENROLLMENT_STATUS_TRANSITIONS,
)
from app.modules.classroom.repository import ClassroomRepository


class ClassroomService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ClassroomRepository(session)

    # ------------------------------------------------------------------
    # Internal helper – build ClassroomResponse tránh lazy-load @property
    # ------------------------------------------------------------------

    async def _to_response(self, classroom: Classroom) -> ClassroomResponse:
        enrollment_count = await self._repo.count_active_enrollments(classroom.id)
        return ClassroomResponse.model_validate({
            "id": classroom.id,
            "class_code": classroom.class_code,
            "class_name": classroom.class_name,
            "class_type": classroom.class_type,
            "academic_year": classroom.academic_year,
            "grade_level": classroom.grade_level,
            "homeroom_teacher_id": classroom.homeroom_teacher_id,
            "max_capacity": classroom.max_capacity,
            "current_enrollment": enrollment_count,
            "room_number": classroom.room_number,
            "description": classroom.description,
            "is_active": classroom.is_active,
            "created_at": classroom.created_at,
            "updated_at": classroom.updated_at,
        })

    # ------------------------------------------------------------------
    # Classroom CRUD
    # ------------------------------------------------------------------

    async def create_classroom(self, data: ClassroomCreateRequest) -> ClassroomResponse:
        if await self._repo.exists_by_code(data.class_code):
            raise ClassroomAlreadyExistsException(identifier=data.class_code)
        obj = Classroom(
            class_code=data.class_code,
            class_name=data.class_name,
            class_type=data.class_type,
            academic_year=data.academic_year,
            grade_level=data.grade_level,
            homeroom_teacher_id=data.homeroom_teacher_id,
            max_capacity=data.max_capacity,
            room_number=data.room_number,
            description=data.description,
        )
        created = await self._repo.create_classroom(obj)
        return await self._to_response(created)

    async def get_classroom(self, class_code: str) -> ClassroomResponse:
        obj = await self._repo.get_classroom_by_code(class_code)
        if not obj:
            raise ClassroomNotFoundException(identifier=class_code)
        return await self._to_response(obj)

    async def get_classroom_by_id(self, classroom_id: int) -> ClassroomResponse:
        obj = await self._repo.get_classroom_by_id(classroom_id)
        if not obj:
            raise ClassroomNotFoundException(identifier=str(classroom_id))
        return await self._to_response(obj)

    async def list_classrooms(self, params: ClassroomQueryParams) -> ClassroomListResponse:
        rows, total = await self._repo.list_classrooms(params)
        total_pages = math.ceil(total / params.page_size) if total > 0 else 1

        items = []
        for classroom, enrollment_count in rows:
            data = {
                "id": classroom.id,
                "class_code": classroom.class_code,
                "class_name": classroom.class_name,
                "class_type": classroom.class_type,
                "academic_year": classroom.academic_year,
                "grade_level": classroom.grade_level,
                "homeroom_teacher_id": classroom.homeroom_teacher_id,
                "max_capacity": classroom.max_capacity,
                "current_enrollment": enrollment_count,
                "room_number": classroom.room_number,
                "description": classroom.description,
                "is_active": classroom.is_active,
                "created_at": classroom.created_at,
                "updated_at": classroom.updated_at,
            }
            items.append(ClassroomResponse.model_validate(data))

        return ClassroomListResponse(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

    async def update_classroom(
        self, class_code: str, data: ClassroomUpdateRequest
    ) -> ClassroomResponse:
        obj = await self._repo.get_classroom_by_code(class_code)
        if not obj:
            raise ClassroomNotFoundException(identifier=class_code)
        updated = await self._repo.update_classroom(obj, data)
        return await self._to_response(updated)

    async def delete_classroom(self, class_code: str) -> ClassroomResponse:
        obj = await self._repo.get_classroom_by_code(class_code)
        if not obj:
            raise ClassroomNotFoundException(identifier=class_code)
        deleted = await self._repo.soft_delete_classroom(obj)
        return await self._to_response(deleted)

    # ------------------------------------------------------------------
    # Enrollment CRUD
    # ------------------------------------------------------------------

    async def create_enrollment_by_code(
        self, class_code: str, data: EnrollmentCreateRequest
    ) -> EnrollmentResponse:
        """Enroll student bằng class_code (dùng cho API endpoint /{class_code}/enrollments)."""
        classroom = await self._repo.get_classroom_by_code(class_code)
        if not classroom:
            raise ClassroomNotFoundException(identifier=class_code)
        data.classroom_id = classroom.id
        return await self.create_enrollment(data)

    async def list_enrollments_by_class_code(
        self, class_code: str, page: int = 1, page_size: int = 50
    ) -> EnrollmentListResponse:
        """List enrollments bằng class_code (dùng cho API endpoint /{class_code}/enrollments)."""
        classroom = await self._repo.get_classroom_by_code(class_code)
        if not classroom:
            raise ClassroomNotFoundException(identifier=class_code)
        return await self.list_enrollments_by_classroom(classroom.id, page, page_size)

    async def create_enrollment(self, data: EnrollmentCreateRequest) -> EnrollmentResponse:
        # Check classroom exists + capacity
        classroom = await self._repo.get_classroom_by_id(data.classroom_id)
        if not classroom:
            raise ClassroomNotFoundException(identifier=str(data.classroom_id))

        current_count = await self._repo.count_active_enrollments(data.classroom_id)
        if current_count >= classroom.max_capacity:
            raise ClassroomCapacityExceededException(
                class_code=classroom.class_code,
                capacity=classroom.max_capacity,
            )

        # Prevent duplicate primary enrollment
        if data.enrollment_type == EnrollmentType.PRIMARY:
            existing_primary = await self._repo.get_active_primary_enrollment(data.student_id)
            if existing_primary:
                raise DuplicatePrimaryEnrollmentException(student_id=str(data.student_id))

        # Prevent duplicate same type in same class
        existing = await self._repo.get_enrollment(
            data.student_id, data.classroom_id, data.enrollment_type
        )
        if existing and existing.is_active:
            raise EnrollmentAlreadyExistsException(
                student_id=str(data.student_id),
                class_code=classroom.class_code,
            )

        obj = StudentClassEnrollment(
            student_id=data.student_id,
            classroom_id=data.classroom_id,
            enrollment_type=data.enrollment_type,
            enrolled_date=data.enrolled_date,
            notes=data.notes,
        )
        created = await self._repo.create_enrollment(obj)
        return EnrollmentResponse.model_validate(created)

    async def get_enrollment(self, enrollment_id: int) -> EnrollmentResponse:
        obj = await self._repo.get_enrollment_by_id(enrollment_id)
        if not obj:
            raise EnrollmentNotFoundException(identifier=str(enrollment_id))
        return EnrollmentResponse.model_validate(obj)

    async def list_enrollments_by_classroom(
        self, classroom_id: int, page: int = 1, page_size: int = 50
    ) -> EnrollmentListResponse:
        items, total = await self._repo.list_enrollments_by_classroom(
            classroom_id, page, page_size
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return EnrollmentListResponse(
            items=[EnrollmentResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def list_enrollments_by_student(
        self, student_id: int
    ) -> List[EnrollmentResponse]:
        items = await self._repo.list_enrollments_by_student(student_id)
        return [EnrollmentResponse.model_validate(i) for i in items]

    async def update_enrollment(
        self, enrollment_id: int, data: EnrollmentUpdateRequest
    ) -> EnrollmentResponse:
        obj = await self._repo.get_enrollment_by_id(enrollment_id)
        if not obj:
            raise EnrollmentNotFoundException(identifier=str(enrollment_id))
        updated = await self._repo.update_enrollment(obj, data)
        return EnrollmentResponse.model_validate(updated)

    async def update_enrollment_status(
        self, enrollment_id: int, data: EnrollmentStatusUpdateRequest
    ) -> EnrollmentResponse:
        obj = await self._repo.get_enrollment_by_id(enrollment_id)
        if not obj:
            raise EnrollmentNotFoundException(identifier=str(enrollment_id))

        current = obj.status
        new_status = data.new_status
        if current == new_status:
            return EnrollmentResponse.model_validate(obj)

        allowed = VALID_ENROLLMENT_STATUS_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise InvalidEnrollmentTransitionException(
                current=current.value, target=new_status.value
            )
        updated = await self._repo.update_enrollment_status(
            obj, new_status, data.left_date, data.notes
        )
        return EnrollmentResponse.model_validate(updated)
