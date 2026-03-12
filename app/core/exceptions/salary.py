"""Salary / Payroll module exceptions."""

from app.core.exceptions.base import EMSException


class SalaryGradeNotFoundException(EMSException):
    status_code = 404
    message = "Salary Grade Not Found"
    detail = "The requested salary grade was not found"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "The requested salary grade was not found"
        if identifier:
            detail = f"Salary grade '{identifier}' was not found"
        super().__init__(detail=detail, **kwargs)


class SalaryGradeAlreadyExistsException(EMSException):
    status_code = 409
    message = "Salary Grade Already Exists"
    detail = "A salary grade with this combination already exists"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "A salary grade with this combination already exists"
        if identifier:
            detail = f"Salary grade '{identifier}' already exists"
        super().__init__(detail=detail, **kwargs)


class BonusPolicyNotFoundException(EMSException):
    status_code = 404
    message = "Bonus Policy Not Found"
    detail = "The requested bonus policy was not found"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "The requested bonus policy was not found"
        if identifier:
            detail = f"Bonus policy '{identifier}' was not found"
        super().__init__(detail=detail, **kwargs)


class BonusPolicyAlreadyExistsException(EMSException):
    status_code = 409
    message = "Bonus Policy Already Exists"
    detail = "A bonus policy with this code already exists"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "A bonus policy with this code already exists"
        if identifier:
            detail = f"Bonus policy '{identifier}' already exists"
        super().__init__(detail=detail, **kwargs)


class PayrollNotFoundException(EMSException):
    status_code = 404
    message = "Payroll Not Found"
    detail = "The requested payroll record was not found"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "The requested payroll record was not found"
        if identifier:
            detail = f"Payroll '{identifier}' was not found"
        super().__init__(detail=detail, **kwargs)


class PayrollAlreadyExistsException(EMSException):
    status_code = 409
    message = "Payroll Already Exists"
    detail = "A payroll record for this teacher/month already exists"

    def __init__(self, teacher_code: str = "", month: str = "", **kwargs):
        detail = "A payroll record for this teacher/month already exists"
        if teacher_code and month:
            detail = f"Payroll for teacher '{teacher_code}' in month '{month}' already exists"
        super().__init__(detail=detail, **kwargs)


class InvalidPayrollTransitionException(EMSException):
    status_code = 400
    message = "Invalid Payroll Transition"
    detail = "The payroll status transition is not allowed"

    def __init__(self, current: str = "", target: str = "", **kwargs):
        detail = "The payroll status transition is not allowed"
        if current and target:
            detail = f"Cannot transition payroll from '{current}' to '{target}'"
        super().__init__(detail=detail, **kwargs)


class PayrollLockedEception(EMSException):
    status_code = 400
    message = "Payroll Locked"
    detail = "The payroll has been paid and cannot be modified"

    def __init__(self, identifier: str = "", **kwargs):
        detail = "The payroll has been paid and cannot be modified"
        if identifier:
            detail = f"Payroll '{identifier}' is in PAID state and is locked"
        super().__init__(detail=detail, **kwargs)
