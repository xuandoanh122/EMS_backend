"""Classroom module exceptions."""

from app.core.exceptions.base import EMSException


class ClassroomNotFoundException(EMSException):
    status_code = 404
    message = "Classroom Not Found"
    detail = "The requested classroom was not found"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "The requested classroom was not found"
        if identifier:
            detail = f"Classroom '{identifier}' was not found"
        super().__init__(detail=detail, **kwargs)


class ClassroomAlreadyExistsException(EMSException):
    status_code = 409
    message = "Classroom Already Exists"
    detail = "A classroom with this code already exists"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "A classroom with this code already exists"
        if identifier:
            detail = f"Classroom '{identifier}' already exists"
        super().__init__(detail=detail, **kwargs)


class ClassroomCapacityExceededException(EMSException):
    status_code = 400
    message = "Classroom Capacity Exceeded"
    detail = "The classroom has reached its maximum capacity"

    def __init__(self, class_code: str = "", capacity: int = 0, **kwargs):
        detail = "The classroom has reached its maximum capacity"
        if class_code:
            detail = f"Classroom '{class_code}' is full (max {capacity} students)"
        super().__init__(detail=detail, **kwargs)


class EnrollmentNotFoundException(EMSException):
    status_code = 404
    message = "Enrollment Not Found"
    detail = "The requested enrollment record was not found"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "The requested enrollment record was not found"
        if identifier:
            detail = f"Enrollment '{identifier}' was not found"
        super().__init__(detail=detail, **kwargs)


class EnrollmentAlreadyExistsException(EMSException):
    status_code = 409
    message = "Enrollment Already Exists"
    detail = "The student is already enrolled in this class"

    def __init__(self, student_id: str = "", class_code: str = "", **kwargs):
        detail = "The student is already enrolled in this class"
        if student_id and class_code:
            detail = f"Student '{student_id}' is already enrolled in class '{class_code}'"
        super().__init__(detail=detail, **kwargs)


class InvalidEnrollmentTransitionException(EMSException):
    status_code = 400
    message = "Invalid Enrollment Transition"
    detail = "The enrollment status transition is not allowed"

    def __init__(self, current: str = "", target: str = "", **kwargs):
        detail = "The enrollment status transition is not allowed"
        if current and target:
            detail = f"Cannot transition enrollment from '{current}' to '{target}'"
        super().__init__(detail=detail, **kwargs)


class DuplicatePrimaryEnrollmentException(EMSException):
    status_code = 400
    message = "Duplicate Primary Enrollment"
    detail = "The student already has an active primary enrollment"

    def __init__(self, student_id: str = "", **kwargs):
        detail = "The student already has an active primary enrollment"
        if student_id:
            detail = f"Student '{student_id}' already has an active primary enrollment in another class"
        super().__init__(detail=detail, **kwargs)
