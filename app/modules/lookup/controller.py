"""
Lookup Controller – FastAPI router cho các Dropdown/Combobox APIs.

Các endpoint này trả về danh sách gọn {id, label, sub_label}
để FE render Dropdown, Combobox, Multi-select.
Không phân trang – giới hạn tối đa 200 items.

Endpoints:
  GET /lookups/teachers   – Danh sách GV đang active
  GET /lookups/classrooms – Danh sách lớp đang active
  GET /lookups/students   – Tìm kiếm HS theo tên/mã
  GET /lookups/subjects   – Danh sách môn học đang active
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.response import APIResponse
from app.modules.classroom.entity import (
    Classroom,
    EnrollmentStatus,
    StudentClassEnrollment,
)
from app.modules.grading.entity import Subject
from app.modules.student.entity import Student, StudentStatus
from app.modules.teacher.entity import Teacher, TeacherStatus

router = APIRouter()


def get_session(session: AsyncSession = Depends(get_async_session)) -> AsyncSession:
    return session


# ---------------------------------------------------------------------------
# GET /lookups/teachers
# ---------------------------------------------------------------------------

@router.get(
    "/teachers",
    status_code=200,
    summary="Lookup: Danh sách giáo viên active (dùng cho Dropdown)",
)
async def lookup_teachers(
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc mã GV"),
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> APIResponse:
    """
    Trả về danh sách GV đang active dạng {id, label, sub_label}.
    Dùng cho Dropdown chọn GVCN, phân công lớp, tạo payroll.
    """
    q = select(
        Teacher.id,
        Teacher.full_name,
        Teacher.teacher_code,
        Teacher.department,
    ).where(
        Teacher.is_active == True,
        Teacher.employment_status == TeacherStatus.ACTIVE,
    )
    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                Teacher.full_name.ilike(term),
                Teacher.teacher_code.ilike(term),
            )
        )
    q = q.order_by(Teacher.full_name.asc()).limit(limit)

    result = await session.execute(q)
    rows = result.fetchall()

    data = [
        {
            "id": r.id,
            "label": r.full_name,
            "sub_label": r.teacher_code,
        }
        for r in rows
    ]
    return APIResponse.success(data=data, detail=f"{len(data)} teacher(s)")


# ---------------------------------------------------------------------------
# GET /lookups/classrooms
# ---------------------------------------------------------------------------

@router.get(
    "/classrooms",
    status_code=200,
    summary="Lookup: Danh sách lớp học active (dùng cho Dropdown)",
)
async def lookup_classrooms(
    search: Optional[str] = Query(None, description="Tìm theo class_code hoặc class_name"),
    has_capacity: Optional[bool] = Query(
        None, description="true = chỉ lớp còn chỗ"
    ),
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> APIResponse:
    """
    Trả về danh sách lớp đang active dạng {id, label, sub_label}.
    Dùng cho Dropdown chọn lớp khi tạo HS, tạo enrollment.
    """
    enroll_count_sq = (
        select(
            StudentClassEnrollment.classroom_id,
            func.count(StudentClassEnrollment.id).label("cnt"),
        )
        .where(
            StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
            StudentClassEnrollment.is_active == True,
        )
        .group_by(StudentClassEnrollment.classroom_id)
        .subquery()
    )

    q = (
        select(
            Classroom.id,
            Classroom.class_code,
            Classroom.class_name,
            Classroom.max_capacity,
            func.coalesce(enroll_count_sq.c.cnt, 0).label("current_count"),
        )
        .outerjoin(enroll_count_sq, Classroom.id == enroll_count_sq.c.classroom_id)
        .where(Classroom.is_active == True)
    )

    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                Classroom.class_code.ilike(term),
                Classroom.class_name.ilike(term),
            )
        )
    if has_capacity is True:
        q = q.where(
            func.coalesce(enroll_count_sq.c.cnt, 0) < Classroom.max_capacity
        )

    q = q.order_by(Classroom.class_name.asc()).limit(limit)

    result = await session.execute(q)
    rows = result.fetchall()

    data = [
        {
            "id": r.id,
            "label": r.class_name,
            "sub_label": f"{r.class_code} · {r.current_count}/{r.max_capacity} HS",
        }
        for r in rows
    ]
    return APIResponse.success(data=data, detail=f"{len(data)} classroom(s)")


# ---------------------------------------------------------------------------
# GET /lookups/students
# ---------------------------------------------------------------------------

@router.get(
    "/students",
    status_code=200,
    summary="Lookup: Tìm kiếm học sinh (dùng cho Combobox)",
)
async def lookup_students(
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc mã HS"),
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> APIResponse:
    """
    Trả về danh sách HS dạng {id, label, sub_label} kèm trạng thái lớp.
    sub_label: 'StudXXXXXXX · Lớp ABC' hoặc 'StudXXXXXXX · Chờ xếp lớp'.
    Dùng cho Combobox trong form Enrollment.
    """
    # Subquery: lớp hiện tại của HS (primary active)
    primary_class_sq = (
        select(
            StudentClassEnrollment.student_id,
            Classroom.class_name,
        )
        .join(Classroom, Classroom.id == StudentClassEnrollment.classroom_id)
        .where(
            StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
            StudentClassEnrollment.is_active == True,
            Classroom.is_active == True,
        )
        .limit(1)
        .correlate()
    ).subquery()

    q = (
        select(
            Student.id,
            Student.full_name,
            Student.student_code,
        )
        .where(
            Student.is_active == True,
            Student.academic_status == StudentStatus.ACTIVE,
        )
    )

    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                Student.full_name.ilike(term),
                Student.student_code.ilike(term),
            )
        )

    q = q.order_by(Student.full_name.asc()).limit(limit)

    result = await session.execute(q)
    student_rows = result.fetchall()

    # Lấy thông tin lớp cho từng HS
    if student_rows:
        student_ids = [r.id for r in student_rows]
        enroll_q = (
            select(
                StudentClassEnrollment.student_id,
                Classroom.class_name,
            )
            .join(Classroom, Classroom.id == StudentClassEnrollment.classroom_id)
            .where(
                StudentClassEnrollment.student_id.in_(student_ids),
                StudentClassEnrollment.status == EnrollmentStatus.ACTIVE,
                StudentClassEnrollment.is_active == True,
                Classroom.is_active == True,
            )
        )
        enroll_result = await session.execute(enroll_q)
        # Map student_id -> class_name (lấy cái đầu tiên)
        enroll_map: Dict[int, str] = {}
        for er in enroll_result.fetchall():
            if er.student_id not in enroll_map:
                enroll_map[er.student_id] = er.class_name
    else:
        enroll_map = {}

    data = [
        {
            "id": r.id,
            "label": r.full_name,
            "sub_label": f"{r.student_code} · {enroll_map.get(r.id, 'Chờ xếp lớp')}",
        }
        for r in student_rows
    ]
    return APIResponse.success(data=data, detail=f"{len(data)} student(s)")


# ---------------------------------------------------------------------------
# GET /lookups/subjects
# ---------------------------------------------------------------------------

@router.get(
    "/subjects",
    status_code=200,
    summary="Lookup: Danh sách môn học active (dùng cho Dropdown)",
)
async def lookup_subjects(
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc mã môn"),
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> APIResponse:
    """
    Trả về danh sách môn học đang active dạng {id, label, sub_label}.
    Dùng cho Dropdown phân công môn (ClassSubject).
    """
    q = select(
        Subject.id,
        Subject.subject_name,
        Subject.subject_code,
        Subject.credits,
    ).where(Subject.is_active == True)

    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                Subject.subject_name.ilike(term),
                Subject.subject_code.ilike(term),
            )
        )

    q = q.order_by(Subject.subject_name.asc()).limit(limit)

    result = await session.execute(q)
    rows = result.fetchall()

    data = [
        {
            "id": r.id,
            "label": r.subject_name,
            "sub_label": r.subject_code,
        }
        for r in rows
    ]
    return APIResponse.success(data=data, detail=f"{len(data)} subject(s)")
