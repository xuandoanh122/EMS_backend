"""
Teacher Portal entities.

Tables:
  - attendance_records
  - timetable_entries
"""

import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Unicode,
)
from sqlalchemy.sql import func

from app.modules.student.entity import Base


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    LATE = "late"
    ABSENT_EXCUSED = "absent_excused"
    ABSENT_UNEXCUSED = "absent_unexcused"


class AttendanceRecord(Base):
    """
    Student attendance record per day per classroom.
    """

    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "classroom_id",
            "attendance_date",
            name="uq_attendance_student_class_date",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    classroom_id = Column(
        Integer,
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attendance_date = Column(Date, nullable=False, index=True)
    status = Column(
        Enum(AttendanceStatus),
        nullable=False,
        default=AttendanceStatus.PRESENT,
        index=True,
    )
    note = Column(Unicode(300), nullable=True)
    recorded_by = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="NO ACTION"),
        nullable=True,
        index=True,
    )

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class TimetableEntry(Base):
    """
    Teacher timetable entry.
    """

    __tablename__ = "timetable_entries"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    teacher_id = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    classroom_id = Column(
        Integer,
        ForeignKey("classrooms.id", ondelete="NO ACTION"),
        nullable=True,
        index=True,
    )
    class_subject_id = Column(
        Integer,
        ForeignKey("class_subjects.id", ondelete="NO ACTION"),
        nullable=True,
        index=True,
    )
    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="NO ACTION"),
        nullable=True,
        index=True,
    )
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    room_number = Column(String(20), nullable=True)
    note = Column(Unicode(300), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
