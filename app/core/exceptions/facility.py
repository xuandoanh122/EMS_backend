"""
Facility module exceptions for the EMS system.
Covers room/equipment inventory, booking & allocation (concurrency-safe),
maintenance scheduling, asset depreciation, and equipment borrowing.
"""

from app.core.exceptions.base import EMSException


# =============================================================================
# Facility Lookup Exceptions
# =============================================================================

class FacilityNotFoundException(EMSException):
    """Raised when a facility (room or equipment) is not found."""

    status_code = 404
    message = "Facility Not Found"
    detail = "The requested facility was not found"

    def __init__(self, facility_type: str = "Facility", facility_id: str = "", **kwargs):
        detail = f"The requested {facility_type.lower()} was not found"
        if facility_id:
            detail = f"{facility_type} with ID '{facility_id}' was not found"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Booking & Allocation Exceptions (Concurrency-safe)
# =============================================================================

class RoomBookingConflictException(EMSException):
    """
    Raised when a room booking conflict is detected.
    Edge case: concurrent booking attempts for the same room/time slot.
    Uses optimistic locking or database-level constraints to prevent.
    """

    status_code = 409
    message = "Room Booking Conflict"
    detail = "The room is already booked for the requested time slot"

    def __init__(self, room_name: str = "", time_slot: str = "", **kwargs):
        detail = "The room is already booked for the requested time slot"
        if room_name and time_slot:
            detail = (
                f"Room '{room_name}' is already booked for "
                f"time slot '{time_slot}'"
            )
        elif room_name:
            detail = f"Room '{room_name}' is already booked for the requested time"
        super().__init__(detail=detail, **kwargs)


class EquipmentUnavailableException(EMSException):
    """
    Raised when a piece of equipment is not available.
    Reasons: currently borrowed, under maintenance, or broken.
    """

    status_code = 409
    message = "Equipment Unavailable"
    detail = "The requested equipment is not available"

    def __init__(self, equipment_name: str = "", status: str = "", **kwargs):
        detail = "The requested equipment is not available"
        if equipment_name and status:
            detail = (
                f"Equipment '{equipment_name}' is unavailable "
                f"(current status: {status})"
            )
        elif equipment_name:
            detail = f"Equipment '{equipment_name}' is not available"
        super().__init__(detail=detail, **kwargs)


class EquipmentBorrowException(EMSException):
    """
    Raised when an equipment borrow/return operation fails.
    Reasons: equipment already borrowed, return past due date, etc.
    """

    status_code = 400
    message = "Equipment Borrow Error"
    detail = "An error occurred while processing the equipment borrow/return"

    def __init__(self, equipment_name: str = "", reason: str = "", **kwargs):
        detail = "An error occurred while processing the equipment borrow/return"
        if equipment_name and reason:
            detail = (
                f"Borrow/return failed for equipment '{equipment_name}': {reason}"
            )
        elif reason:
            detail = f"Equipment borrow/return error: {reason}"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Maintenance & Depreciation Exceptions
# =============================================================================

class MaintenanceScheduleException(EMSException):
    """
    Raised when there is a conflict or error in the maintenance schedule.
    Example: scheduling maintenance during active room usage.
    """

    status_code = 409
    message = "Maintenance Schedule Error"
    detail = "An error occurred while scheduling maintenance"

    def __init__(self, facility_name: str = "", reason: str = "", **kwargs):
        detail = "An error occurred while scheduling maintenance"
        if facility_name and reason:
            detail = (
                f"Maintenance scheduling failed for '{facility_name}': {reason}"
            )
        elif reason:
            detail = f"Maintenance schedule error: {reason}"
        super().__init__(detail=detail, **kwargs)


class AssetDepreciationException(EMSException):
    """
    Raised when there is an error calculating asset depreciation.
    Used for tracking depreciation of equipment over time.
    """

    status_code = 400
    message = "Asset Depreciation Error"
    detail = "An error occurred while calculating asset depreciation"

    def __init__(self, asset_name: str = "", reason: str = "", **kwargs):
        detail = "An error occurred while calculating asset depreciation"
        if asset_name and reason:
            detail = (
                f"Depreciation calculation failed for asset '{asset_name}': {reason}"
            )
        elif reason:
            detail = f"Asset depreciation error: {reason}"
        super().__init__(detail=detail, **kwargs)


# =============================================================================
# Facility Status Transition Exceptions
# =============================================================================

class FacilityStatusTransitionException(EMSException):
    """
    Raised when an invalid facility/asset status transition is attempted.
    Valid statuses: mới (new), đang sử dụng (in use), hỏng (broken),
    đang bảo trì (under maintenance).
    """

    status_code = 400
    message = "Invalid Status Transition"
    detail = "The requested facility status transition is not allowed"

    def __init__(self, current_status: str = "", target_status: str = "", **kwargs):
        detail = "The requested facility status transition is not allowed"
        if current_status and target_status:
            detail = (
                f"Cannot transition facility status from "
                f"'{current_status}' to '{target_status}'"
            )
        super().__init__(detail=detail, **kwargs)
