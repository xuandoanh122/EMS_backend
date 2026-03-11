"""
Student module exceptions for the EMS system.
Covers student profile management, academic management (grades, attendance,
course registration), financial management (tuition), and edge cases
(class transfer, preservation return, grade modification audit).
"""

from app.core.exceptions.base import EMSException


# =============================================================================
# Student Profile Exceptions
# =============================================================================

class StudentNotFoundException(EMSException):
    """Raised when a student record is not found."""

    status_code = 404
    message = "Student Not Found"
    detail = "The requested student was not found"

    def __init__(self, student_id: str = "", **kwargs):
        detail = "The requested student was not found"
        if student_id:
            detail = f"Student with ID '{student_id}' was not found"
        super().__init__(detail=detail, **kwargs)


class StudentAlreadyExistsException(EMSException):
    """Raised when attempting to create a student with a duplicate student code."""

    status_code = 409
    message = "Student Already Exists"
    detail = "A student with this student code already exists"

    def __init__(self, student_code: str = "", **kwargs):
        detail = "A student with this student code already exists"
        if student_code:
            detail = f"Student with code '{student_code}' already exists"
        super().__init__(detail=detail, **kwargs)


class StudentStatusTransitionException(EMSException):
    """
    Raised when an invalid status transition is attempted.
    Valid statuses: đang học, bảo lưu, đình chỉ, đã tốt nghiệp.
    Example: Cannot transition from 'đã tốt nghiệp' back to 'đang học'.
    """

    status_code = 400
    message = "Invalid Status Transition"
    detail = "The requested student status transition is not allowed"

    def __init__(self, current_status: str = "", target_status: str = "", **kwargs):
        detail = "The requested student status transition is not allowed"
        if current_status and target_status:
            detail = (
                f"Cannot transition student status from "
                f"'{current_status}' to '{target_status}'"
            )
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Academic Management Exceptions
# =============================================================================

class ClassTransferException(EMSException):
    """
    Raised when there is an error during mid-term class transfer.
    Edge case: Học sinh chuyển lớp giữa kỳ.
    """

    status_code = 400
    message = "Class Transfer Error"
    detail = "An error occurred during the class transfer process"

    def __init__(self, student_id: str = "", reason: str = "", **kwargs):
        detail = "An error occurred during the class transfer process"
        if student_id and reason:
            detail = f"Class transfer failed for student '{student_id}': {reason}"
        elif reason:
            detail = f"Class transfer failed: {reason}"
        super().__init__(detail=detail, **kwargs)


class CourseRegistrationException(EMSException):
    """
    Raised when course/subject registration fails.
    Reasons: schedule conflict, missing prerequisites, class full, etc.
    """

    status_code = 400
    message = "Course Registration Error"
    detail = "An error occurred during course registration"

    def __init__(self, course_name: str = "", reason: str = "", **kwargs):
        detail = "An error occurred during course registration"
        if course_name and reason:
            detail = f"Registration for course '{course_name}' failed: {reason}"
        elif course_name:
            detail = f"Registration for course '{course_name}' failed"
        elif reason:
            detail = f"Course registration failed: {reason}"
        super().__init__(detail=detail, **kwargs)


class GradeModificationException(EMSException):
    """
    Raised when a grade modification request is invalid.
    Edge case: Requires proper workflow (audit log - who modified, when,
    old score -> new score).
    """

    status_code = 400
    message = "Grade Modification Error"
    detail = "The grade modification request is invalid"

    def __init__(self, student_id: str = "", subject: str = "", reason: str = "", **kwargs):
        detail = "The grade modification request is invalid"
        parts = []
        if student_id:
            parts.append(f"student '{student_id}'")
        if subject:
            parts.append(f"subject '{subject}'")
        if parts:
            detail = f"Grade modification failed for {', '.join(parts)}"
        if reason:
            detail += f": {reason}"
        super().__init__(detail=detail, **kwargs)


class AttendanceException(EMSException):
    """
    Raised when there is an error related to student attendance tracking.
    Covers: điểm danh chuyên cần, nghỉ phép có/không phép.
    """

    status_code = 400
    message = "Attendance Error"
    detail = "An error occurred while processing attendance"

    def __init__(self, reason: str = "", **kwargs):
        detail = "An error occurred while processing attendance"
        if reason:
            detail = f"Attendance error: {reason}"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Financial Management Exceptions
# =============================================================================

class TuitionPaymentException(EMSException):
    """
    Raised when there is an error processing tuition payment.
    Covers: học phí, thu hộ/chi hộ, miễn giảm (học bổng), nợ đọng.
    """

    status_code = 400
    message = "Tuition Payment Error"
    detail = "An error occurred while processing the tuition payment"

    def __init__(self, student_id: str = "", reason: str = "", **kwargs):
        detail = "An error occurred while processing the tuition payment"
        if student_id and reason:
            detail = f"Tuition payment failed for student '{student_id}': {reason}"
        elif reason:
            detail = f"Tuition payment error: {reason}"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Import/Export Exceptions
# =============================================================================

class StudentImportException(EMSException):
    """
    Raised when importing student list from Excel/CSV fails.
    Reasons: invalid format, duplicate records, missing required fields.
    """

    status_code = 400
    message = "Student Import Error"
    detail = "An error occurred while importing the student list"

    def __init__(self, filename: str = "", row: int = 0, reason: str = "", **kwargs):
        detail = "An error occurred while importing the student list"
        parts = []
        if filename:
            parts.append(f"file '{filename}'")
        if row > 0:
            parts.append(f"row {row}")
        if parts:
            detail = f"Student import failed at {', '.join(parts)}"
        if reason:
            detail += f": {reason}"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Edge Case Exceptions
# =============================================================================

class PreservationReturnException(EMSException):
    """
    Raised when a student returns from preservation (bảo lưu) but the
    original curriculum has been changed/updated.
    Edge case: Bảo lưu rồi quay lại học nhưng chương trình học cũ đã thay đổi.
    """

    status_code = 400
    message = "Preservation Return Error"
    detail = "An error occurred while processing the student's return from preservation"

    def __init__(self, student_id: str = "", reason: str = "", **kwargs):
        detail = "An error occurred while processing the student's return from preservation"
        if student_id and reason:
            detail = (
                f"Preservation return failed for student '{student_id}': {reason}"
            )
        elif student_id:
            detail = (
                f"Student '{student_id}' cannot return from preservation: "
                f"the original curriculum may have changed"
            )
        elif reason:
            detail = f"Preservation return error: {reason}"
        super().__init__(detail=detail, **kwargs)
