"""
Teacher module exceptions for the EMS system.
Covers teacher HR management, scheduling & assignment, attendance/check-in
(QR Code / Geolocation), salary calculation, leave management,
availability tracking, and performance evaluation.
"""

from app.core.exceptions.base import EMSException


# =============================================================================
# Teacher Profile Exceptions
# =============================================================================

class TeacherNotFoundException(EMSException):
    """Raised when a teacher record is not found."""

    status_code = 404
    message = "Teacher Not Found"
    detail = "The requested teacher was not found"

    def __init__(self, teacher_id: str = "", **kwargs):
        detail = "The requested teacher was not found"
        if teacher_id:
            detail = f"Teacher with ID '{teacher_id}' was not found"
        super().__init__(detail=detail, **kwargs)


class TeacherAlreadyExistsException(EMSException):
    """Raised when attempting to create a teacher with duplicate information."""

    status_code = 409
    message = "Teacher Already Exists"
    detail = "A teacher with this information already exists"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "A teacher with this information already exists"
        if identifier:
            detail = f"Teacher with identifier '{identifier}' already exists"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Scheduling & Assignment Exceptions
# =============================================================================

class ScheduleConflictException(EMSException):
    """
    Raised when a scheduling conflict is detected.
    Cases: overlapping classes, conflict with teacher's leave time,
    double-booked time slots.
    """

    status_code = 409
    message = "Schedule Conflict"
    detail = "A scheduling conflict was detected"

    def __init__(
        self,
        teacher_id: str = "",
        time_slot: str = "",
        reason: str = "",
        **kwargs,
    ):
        detail = "A scheduling conflict was detected"
        if teacher_id and time_slot:
            detail = (
                f"Schedule conflict for teacher '{teacher_id}' "
                f"at time slot '{time_slot}'"
            )
        elif reason:
            detail = f"Schedule conflict: {reason}"
        super().__init__(detail=detail, **kwargs)


class SubstituteTeacherNotFoundException(EMSException):
    """
    Raised when no suitable substitute teacher can be found.
    System filters by: same subject expertise AND available time slot.
    Edge case: Giáo viên nghỉ đột xuất, không tìm được người dạy thay.
    """

    status_code = 404
    message = "Substitute Teacher Not Found"
    detail = "No suitable substitute teacher was found"

    def __init__(self, subject: str = "", time_slot: str = "", **kwargs):
        detail = "No suitable substitute teacher was found"
        parts = []
        if subject:
            parts.append(f"subject '{subject}'")
        if time_slot:
            parts.append(f"time slot '{time_slot}'")
        if parts:
            detail = (
                f"No substitute teacher found matching criteria: "
                f"{', '.join(parts)}"
            )
        super().__init__(detail=detail, **kwargs)


class TeacherAssignmentException(EMSException):
    """
    Raised when a teacher assignment is invalid.
    Example: assigning a teacher to a subject outside their expertise.
    """

    status_code = 400
    message = "Teacher Assignment Error"
    detail = "The teacher assignment is invalid"

    def __init__(self, teacher_id: str = "", reason: str = "", **kwargs):
        detail = "The teacher assignment is invalid"
        if teacher_id and reason:
            detail = f"Assignment failed for teacher '{teacher_id}': {reason}"
        elif reason:
            detail = f"Teacher assignment error: {reason}"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Attendance / Check-in Exceptions (QR Code / Geolocation)
# =============================================================================

class AttendanceCheckInException(EMSException):
    """
    Raised when the teacher's attendance check-in fails.
    Reasons: QR code expired, geolocation out of range, already checked in,
    check-in outside allowed time window.
    """

    status_code = 400
    message = "Check-In Error"
    detail = "The attendance check-in failed"

    def __init__(self, teacher_id: str = "", reason: str = "", **kwargs):
        detail = "The attendance check-in failed"
        if teacher_id and reason:
            detail = f"Check-in failed for teacher '{teacher_id}': {reason}"
        elif reason:
            detail = f"Check-in error: {reason}"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Salary & Payroll Exceptions
# =============================================================================

class SalaryCalculationException(EMSException):
    """
    Raised when salary calculation encounters an error.
    Depends on: attendance data + salary grade + actual teaching hours + KPI bonus.
    """

    status_code = 400
    message = "Salary Calculation Error"
    detail = "An error occurred during salary calculation"

    def __init__(self, teacher_id: str = "", period: str = "", reason: str = "", **kwargs):
        detail = "An error occurred during salary calculation"
        parts = []
        if teacher_id:
            parts.append(f"teacher '{teacher_id}'")
        if period:
            parts.append(f"period '{period}'")
        if parts:
            detail = f"Salary calculation failed for {', '.join(parts)}"
        if reason:
            detail += f": {reason}"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Leave Management Exceptions
# =============================================================================

class LeaveRequestException(EMSException):
    """
    Raised when a leave request is invalid.
    Reasons: exceeds allowed leave days, overlapping leave dates,
    leave during critical teaching period.
    """

    status_code = 400
    message = "Leave Request Error"
    detail = "The leave request is invalid"

    def __init__(self, teacher_id: str = "", reason: str = "", **kwargs):
        detail = "The leave request is invalid"
        if teacher_id and reason:
            detail = f"Leave request failed for teacher '{teacher_id}': {reason}"
        elif reason:
            detail = f"Leave request error: {reason}"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Availability Tracking Exceptions
# =============================================================================

class AvailabilityUpdateException(EMSException):
    """
    Raised when updating free time slots fails.
    Feature: Teachers can register their available time slots for
    substitute teaching or extra classes.
    """

    status_code = 400
    message = "Availability Update Error"
    detail = "An error occurred while updating availability"

    def __init__(self, teacher_id: str = "", reason: str = "", **kwargs):
        detail = "An error occurred while updating availability"
        if teacher_id and reason:
            detail = (
                f"Availability update failed for teacher '{teacher_id}': {reason}"
            )
        elif reason:
            detail = f"Availability update error: {reason}"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Performance Evaluation Exceptions
# =============================================================================

class PerformanceEvaluationException(EMSException):
    """
    Raised when there is an error during performance evaluation.
    Sources: student feedback forms, department KPIs.
    """

    status_code = 400
    message = "Performance Evaluation Error"
    detail = "An error occurred during performance evaluation"

    def __init__(self, teacher_id: str = "", reason: str = "", **kwargs):
        detail = "An error occurred during performance evaluation"
        if teacher_id and reason:
            detail = (
                f"Performance evaluation failed for teacher '{teacher_id}': {reason}"
            )
        elif reason:
            detail = f"Performance evaluation error: {reason}"
        super().__init__(detail=detail, **kwargs)
