"""
Lookup DTOs - minimal payloads for dropdowns/selectors.
"""

from typing import List, Optional

from pydantic import BaseModel


class TeacherLookupItem(BaseModel):
    id: int
    teacher_code: str
    full_name: str


class ClassroomLookupItem(BaseModel):
    id: int
    class_code: str
    class_name: str
    grade_level: Optional[int] = None
    academic_year: Optional[str] = None


class StudentLookupItem(BaseModel):
    id: int
    student_code: str
    full_name: str
    class_name: Optional[str] = None


class SubjectLookupItem(BaseModel):
    id: int
    subject_code: str
    subject_name: str


class TeacherLookupListResponse(BaseModel):
    items: List[TeacherLookupItem]


class ClassroomLookupListResponse(BaseModel):
    items: List[ClassroomLookupItem]


class StudentLookupListResponse(BaseModel):
    items: List[StudentLookupItem]


class SubjectLookupListResponse(BaseModel):
    items: List[SubjectLookupItem]
