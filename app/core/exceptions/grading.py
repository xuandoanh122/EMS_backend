"""Grading module exceptions."""

from app.core.exceptions.base import EMSException


class SubjectNotFoundException(EMSException):
    status_code = 404
    message = "Subject Not Found"
    detail = "The requested subject was not found"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "The requested subject was not found"
        if identifier:
            detail = f"Subject '{identifier}' was not found"
        super().__init__(detail=detail, **kwargs)


class SubjectAlreadyExistsException(EMSException):
    status_code = 409
    message = "Subject Already Exists"
    detail = "A subject with this code already exists"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "A subject with this code already exists"
        if identifier:
            detail = f"Subject '{identifier}' already exists"
        super().__init__(detail=detail, **kwargs)


class ClassSubjectNotFoundException(EMSException):
    status_code = 404
    message = "Class Subject Assignment Not Found"
    detail = "The requested class-subject assignment was not found"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "The requested class-subject assignment was not found"
        if identifier:
            detail = f"Class-subject assignment '{identifier}' was not found"
        super().__init__(detail=detail, **kwargs)


class ClassSubjectAlreadyExistsException(EMSException):
    status_code = 409
    message = "Class Subject Already Exists"
    detail = "This subject is already assigned to the class for this semester"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "This subject is already assigned to the class for this semester"
        if identifier:
            detail = f"Class-subject assignment '{identifier}' already exists"
        super().__init__(detail=detail, **kwargs)


class GradeComponentNotFoundException(EMSException):
    status_code = 404
    message = "Grade Component Not Found"
    detail = "The requested grade component was not found"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "The requested grade component was not found"
        if identifier:
            detail = f"Grade component '{identifier}' was not found"
        super().__init__(detail=detail, **kwargs)


class GradeWeightSumException(EMSException):
    status_code = 400
    message = "Grade Weight Sum Error"
    detail = "The sum of grade component weights must equal 100"

    def __init__(self, current_sum: int = 0, **kwargs):
        detail = f"The sum of grade component weights must equal 100 (current: {current_sum})"
        super().__init__(detail=detail, **kwargs)


class StudentGradeNotFoundException(EMSException):
    status_code = 404
    message = "Student Grade Not Found"
    detail = "The requested student grade record was not found"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "The requested student grade record was not found"
        if identifier:
            detail = f"Student grade '{identifier}' was not found"
        super().__init__(detail=detail, **kwargs)


class UnauthorizedGradeEntryException(EMSException):
    status_code = 403
    message = "Unauthorized Grade Entry"
    detail = "Only the assigned teacher can enter grades for this class-subject"

    def __init__(self, teacher_id: str = "", class_subject_id: str = "", **kwargs):
        detail = "Only the assigned teacher can enter grades for this class-subject"
        if teacher_id and class_subject_id:
            detail = (
                f"Teacher '{teacher_id}' is not assigned to "
                f"class-subject '{class_subject_id}'"
            )
        super().__init__(detail=detail, **kwargs)


class GradeScoreOutOfRangeException(EMSException):
    status_code = 400
    message = "Score Out Of Range"
    detail = "Score must be between 0.00 and 10.00"

    def __init__(self, score: float = 0, **kwargs):
        detail = f"Score {score} is out of range (must be 0.00 – 10.00)"
        super().__init__(detail=detail, **kwargs)
