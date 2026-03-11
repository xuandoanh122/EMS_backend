"""
Unit tests for app/core/handlers/exception_handler.py

Coverage:
  1.  EMSException handler – base class
  2.  EMSException handler – errors field present / absent
  3.  Common exceptions (BadRequest, NotFound, AlreadyExists, Validation,
      Permission, Internal, RateLimit, FileProcessing)
  4.  Auth exceptions (credentials, tokens, roles, account states)
  5.  RequestValidationError handler (single/multiple fields, query param)
  6.  StarletteHTTPException handler (various status codes, None/empty detail)
  7.  Unhandled Exception handler (RuntimeError, ValueError, ZeroDivisionError)
  8.  EMSException – direct unit tests (no HTTP layer)
  9.  register_exception_handlers – registration side-effects
  10. Logging – handlers emit correct log levels

Bug fixed (vs deleted version):
  - Factory invocation was:
        exc = factory() if callable(factory) else factory()   ← both branches called factory()
    Fixed to:
        exc = factory() if callable(factory) else factory     ← correct no-op branch
    (In practice every entry in exc_map is callable, so the else branch is just
    a safety guard for non-callable values.)
"""

import logging

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions.auth import (
    AccountDisabledException,
    AccountLockedException,
    InsufficientRoleException,
    InvalidCredentialsException,
    TokenBlacklistedException,
    TokenExpiredException,
    TokenInvalidException,
)
from app.core.exceptions.base import EMSException
from app.core.exceptions.common import (
    AlreadyExistsException,
    BadRequestException,
    FileProcessingException,
    InternalServerException,
    NotFoundException,
    PermissionDeniedException,
    RateLimitExceededException,
    ValidationException,
)
from app.core.handlers.exception_handler import register_exception_handlers


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def app() -> FastAPI:
    """Fresh FastAPI app with all exception handlers registered."""
    _app = FastAPI()
    register_exception_handlers(_app)

    # ── Route: raise EMSException subclasses by name ─────────────────────
    @_app.get("/raise/ems")
    async def raise_ems(exc_type: str = "base", extra: bool = False):
        exc_map = {
            # base
            "base": EMSException,
            # common
            "bad_request":          BadRequestException,
            "not_found":            lambda: NotFoundException(resource="Student", identifier="42"),
            "not_found_no_id":      lambda: NotFoundException(resource="Student"),
            "already_exists":       lambda: AlreadyExistsException(resource="Course", identifier="CS101"),
            "already_exists_no_id": lambda: AlreadyExistsException(resource="Course"),
            "validation":           ValidationException,
            "permission":           PermissionDeniedException,
            "internal":             InternalServerException,
            "rate_limit":           RateLimitExceededException,
            "file_proc_full":       lambda: FileProcessingException(filename="data.xlsx", reason="corrupt"),
            "file_proc_name":       lambda: FileProcessingException(filename="data.xlsx"),
            "file_proc_reason":     lambda: FileProcessingException(reason="too large"),
            "file_proc_none":       FileProcessingException,
            # auth
            "invalid_creds":    InvalidCredentialsException,
            "token_expired":    TokenExpiredException,
            "token_invalid":    TokenInvalidException,
            "token_blacklisted":TokenBlacklistedException,
            "role_both":        lambda: InsufficientRoleException(required_role="Admin", current_role="Student"),
            "role_req_only":    lambda: InsufficientRoleException(required_role="Admin"),
            "role_none":        InsufficientRoleException,
            "account_disabled": AccountDisabledException,
            "account_locked":   AccountLockedException,
        }
        # ✅ FIX: use the value directly when it's not callable (safety guard)
        factory = exc_map.get(exc_type, EMSException)
        exc = factory() if callable(factory) else factory  # type: ignore[operator]
        if extra:
            exc.errors = [{"field": "name", "message": "required"}]
        raise exc

    # ── Route: raise with pre-set errors list ────────────────────────────
    @_app.get("/raise/ems/with-errors")
    async def raise_ems_with_errors():
        exc = BadRequestException()
        exc.errors = [
            {"field": "email", "message": "invalid format"},
            {"field": "age",   "message": "must be positive"},
        ]
        raise exc

    # ── Route: errors explicitly set to None ─────────────────────────────
    @_app.get("/raise/ems/errors-none")
    async def raise_ems_errors_none():
        exc = BadRequestException()
        exc.errors = None
        raise exc

    # ── Route: raise StarletteHTTPException with optional detail ─────────
    @_app.get("/raise/http/{status_code}")
    async def raise_http(status_code: int, detail: str = "Some detail"):
        raise StarletteHTTPException(status_code=status_code, detail=detail)

    @_app.get("/raise/http/no-detail/{status_code}")
    async def raise_http_no_detail(status_code: int):
        raise StarletteHTTPException(status_code=status_code, detail=None)

    # ── Routes: unhandled exceptions ─────────────────────────────────────
    @_app.get("/raise/unhandled")
    async def raise_unhandled():
        raise RuntimeError("Something went very wrong")

    @_app.get("/raise/unhandled/valueerror")
    async def raise_value_error():
        raise ValueError("bad value")

    @_app.get("/raise/unhandled/zerodiv")
    async def raise_zero_div():
        _ = 1 / 0

    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """TestClient with raise_server_exceptions=False so handlers execute."""
    return TestClient(app, raise_server_exceptions=False)


# ===========================================================================
# Helper
# ===========================================================================

def body(response) -> dict:
    return response.json()


# ===========================================================================
# 1. EMSException handler – base class
# ===========================================================================

class TestEMSExceptionHandlerBase:

    def test_status_code_500(self, client):
        assert client.get("/raise/ems?exc_type=base").status_code == 500

    def test_response_has_required_keys(self, client):
        b = body(client.get("/raise/ems?exc_type=base"))
        for key in ("code", "message", "detail", "data"):
            assert key in b

    def test_data_is_null(self, client):
        assert body(client.get("/raise/ems?exc_type=base"))["data"] is None

    def test_no_errors_key_by_default(self, client):
        # 'errors' must NOT appear when exc.errors is None
        assert "errors" not in body(client.get("/raise/ems?exc_type=base"))

    def test_code_field_matches_status(self, client):
        b = body(client.get("/raise/ems?exc_type=base"))
        assert b["code"] == 500


# ===========================================================================
# 2. EMSException handler – errors field
# ===========================================================================

class TestEMSExceptionHandlerErrors:

    def test_errors_present_when_set(self, client):
        b = body(client.get("/raise/ems/with-errors"))
        assert "errors" in b
        assert isinstance(b["errors"], list)
        assert len(b["errors"]) == 2

    def test_errors_absent_when_none(self, client):
        assert "errors" not in body(client.get("/raise/ems/errors-none"))

    def test_errors_content_fields(self, client):
        errors = body(client.get("/raise/ems/with-errors"))["errors"]
        fields = [e["field"] for e in errors]
        assert "email" in fields
        assert "age" in fields

    def test_extra_flag_adds_errors(self, client):
        b = body(client.get("/raise/ems?exc_type=base&extra=true"))
        assert "errors" in b
        assert b["errors"][0]["field"] == "name"


# ===========================================================================
# 3. Common exceptions
# ===========================================================================

class TestCommonExceptions:

    def test_bad_request_400(self, client):
        r = client.get("/raise/ems?exc_type=bad_request")
        assert r.status_code == 400
        assert body(r)["message"] == "Bad Request"

    def test_not_found_with_identifier(self, client):
        r = client.get("/raise/ems?exc_type=not_found")
        assert r.status_code == 404
        b = body(r)
        assert b["code"] == 404
        assert "42" in b["detail"]
        assert "Student" in b["detail"]

    def test_not_found_without_identifier(self, client):
        r = client.get("/raise/ems?exc_type=not_found_no_id")
        b = body(r)
        assert b["code"] == 404
        assert "Student" in b["detail"]
        assert "identifier" not in b["detail"]

    def test_already_exists_with_identifier(self, client):
        r = client.get("/raise/ems?exc_type=already_exists")
        assert r.status_code == 409
        b = body(r)
        assert b["message"] == "Already Exists"
        assert "CS101" in b["detail"]

    def test_already_exists_without_identifier(self, client):
        b = body(client.get("/raise/ems?exc_type=already_exists_no_id"))
        assert "Course" in b["detail"]

    def test_validation_422(self, client):
        r = client.get("/raise/ems?exc_type=validation")
        assert r.status_code == 422
        assert body(r)["message"] == "Validation Error"

    def test_permission_denied_403(self, client):
        r = client.get("/raise/ems?exc_type=permission")
        assert r.status_code == 403
        assert body(r)["message"] == "Permission Denied"

    def test_internal_server_500(self, client):
        r = client.get("/raise/ems?exc_type=internal")
        assert r.status_code == 500
        assert body(r)["message"] == "Internal Server Error"

    def test_rate_limit_429(self, client):
        r = client.get("/raise/ems?exc_type=rate_limit")
        assert r.status_code == 429
        assert body(r)["message"] == "Rate Limit Exceeded"

    def test_file_proc_full_details(self, client):
        b = body(client.get("/raise/ems?exc_type=file_proc_full"))
        assert "data.xlsx" in b["detail"]
        assert "corrupt" in b["detail"]

    def test_file_proc_filename_only(self, client):
        b = body(client.get("/raise/ems?exc_type=file_proc_name"))
        assert "data.xlsx" in b["detail"]

    def test_file_proc_reason_only(self, client):
        b = body(client.get("/raise/ems?exc_type=file_proc_reason"))
        assert "too large" in b["detail"]

    def test_file_proc_no_args(self, client):
        b = body(client.get("/raise/ems?exc_type=file_proc_none"))
        assert "file" in b["detail"].lower()


# ===========================================================================
# 4. Auth exceptions
# ===========================================================================

class TestAuthExceptions:

    def test_invalid_credentials_401(self, client):
        r = client.get("/raise/ems?exc_type=invalid_creds")
        assert r.status_code == 401
        assert body(r)["message"] == "Invalid Credentials"

    def test_token_expired_401(self, client):
        r = client.get("/raise/ems?exc_type=token_expired")
        assert r.status_code == 401
        assert body(r)["message"] == "Token Expired"

    def test_token_invalid_401(self, client):
        r = client.get("/raise/ems?exc_type=token_invalid")
        assert r.status_code == 401
        assert body(r)["message"] == "Invalid Token"

    def test_token_blacklisted_401(self, client):
        r = client.get("/raise/ems?exc_type=token_blacklisted")
        assert r.status_code == 401
        assert body(r)["message"] == "Token Revoked"

    def test_insufficient_role_both(self, client):
        b = body(client.get("/raise/ems?exc_type=role_both"))
        assert "Admin" in b["detail"]
        assert "Student" in b["detail"]

    def test_insufficient_role_required_only(self, client):
        b = body(client.get("/raise/ems?exc_type=role_req_only"))
        assert "Admin" in b["detail"]

    def test_insufficient_role_no_args_403(self, client):
        assert client.get("/raise/ems?exc_type=role_none").status_code == 403

    def test_account_disabled_403(self, client):
        r = client.get("/raise/ems?exc_type=account_disabled")
        assert r.status_code == 403
        assert body(r)["message"] == "Account Disabled"

    def test_account_locked_423(self, client):
        r = client.get("/raise/ems?exc_type=account_locked")
        assert r.status_code == 423
        assert body(r)["code"] == 423
        assert body(r)["message"] == "Account Locked"


# ===========================================================================
# 5. RequestValidationError handler
# ===========================================================================

@pytest.fixture
def validation_client() -> TestClient:
    """Separate app with typed routes that trigger Pydantic validation."""
    _app = FastAPI()
    register_exception_handlers(_app)

    from pydantic import BaseModel

    class Item(BaseModel):
        name: str
        age: int

    @_app.post("/items")
    async def create_item(item: Item):
        return item

    @_app.get("/typed")
    async def typed_param(age: int):
        return {"age": age}

    return TestClient(_app, raise_server_exceptions=False)


class TestValidationExceptionHandler:

    def test_status_422(self, validation_client):
        r = validation_client.post("/items", json={"name": "Alice", "age": "bad"})
        assert r.status_code == 422

    def test_body_code_422(self, validation_client):
        b = body(validation_client.post("/items", json={"name": "Alice", "age": "bad"}))
        assert b["code"] == 422

    def test_message(self, validation_client):
        b = body(validation_client.post("/items", json={"name": "Alice", "age": "bad"}))
        assert b["message"] == "Validation Error"

    def test_detail_mentions_validation(self, validation_client):
        b = body(validation_client.post("/items", json={"name": "Alice", "age": "bad"}))
        assert "validation" in b["detail"].lower()

    def test_data_null(self, validation_client):
        b = body(validation_client.post("/items", json={"name": "Alice", "age": "bad"}))
        assert b["data"] is None

    def test_errors_is_list(self, validation_client):
        b = body(validation_client.post("/items", json={"name": "Alice", "age": "bad"}))
        assert isinstance(b["errors"], list)
        assert len(b["errors"]) >= 1

    def test_errors_contain_age_field(self, validation_client):
        errors = body(validation_client.post("/items", json={"name": "Alice", "age": "bad"}))["errors"]
        assert any("age" in e["field"] for e in errors)

    def test_missing_required_field(self, validation_client):
        r = validation_client.post("/items", json={"age": 25})
        assert r.status_code == 422
        errors = body(r)["errors"]
        assert any("name" in e["field"] for e in errors)

    def test_multiple_invalid_fields(self, validation_client):
        errors = body(validation_client.post("/items", json={}))["errors"]
        assert len(errors) >= 2

    def test_each_error_has_type_key(self, validation_client):
        errors = body(validation_client.post("/items", json={"name": "X", "age": "bad"}))["errors"]
        for e in errors:
            assert "type" in e

    def test_each_error_has_message_key(self, validation_client):
        errors = body(validation_client.post("/items", json={"name": "X", "age": "bad"}))["errors"]
        for e in errors:
            assert "message" in e

    def test_field_is_string(self, validation_client):
        errors = body(validation_client.post("/items", json={"name": 1, "age": "bad"}))["errors"]
        for e in errors:
            assert isinstance(e["field"], str)

    def test_query_param_validation(self, validation_client):
        r = validation_client.get("/typed?age=abc")
        assert r.status_code == 422
        assert body(r)["code"] == 422


# ===========================================================================
# 6. StarletteHTTPException handler
# ===========================================================================

class TestHTTPExceptionHandler:

    def test_404_status_code(self, client):
        assert client.get("/raise/http/404").status_code == 404

    def test_404_body_code(self, client):
        assert body(client.get("/raise/http/404"))["code"] == 404

    def test_404_message_is_http_error(self, client):
        assert body(client.get("/raise/http/404"))["message"] == "HTTP Error"

    def test_404_data_null(self, client):
        assert body(client.get("/raise/http/404"))["data"] is None

    def test_404_detail_populated_from_query(self, client):
        b = body(client.get("/raise/http/404?detail=Page+Not+Found"))
        assert b["detail"] == "Page Not Found"

    def test_405_status_code(self, client):
        r = client.get("/raise/http/405")
        assert r.status_code == 405
        assert body(r)["code"] == 405

    def test_403_status_code(self, client):
        assert client.get("/raise/http/403").status_code == 403

    def test_500_status_code(self, client):
        assert client.get("/raise/http/500").status_code == 500

    def test_none_detail_uses_fallback(self, client):
        b = body(client.get("/raise/http/no-detail/404"))
        assert b["detail"] == "An HTTP error occurred"

    def test_empty_string_detail_uses_fallback(self, client):
        b = body(client.get("/raise/http/404?detail="))
        assert b["detail"] == "An HTTP error occurred"

    def test_custom_detail_string_preserved(self, client):
        b = body(client.get("/raise/http/410?detail=Gone+forever"))
        assert b["detail"] == "Gone forever"

    def test_message_always_http_error_for_all_codes(self, client):
        for code in [400, 401, 403, 404, 405, 410, 500]:
            assert body(client.get(f"/raise/http/{code}"))["message"] == "HTTP Error"

    def test_response_content_type_is_json(self, client):
        r = client.get("/raise/http/404")
        assert r.headers["content-type"].startswith("application/json")


# ===========================================================================
# 7. Unhandled Exception handler
# ===========================================================================

class TestUnhandledExceptionHandler:

    def test_runtime_error_500(self, client):
        assert client.get("/raise/unhandled").status_code == 500

    def test_body_code_500(self, client):
        assert body(client.get("/raise/unhandled"))["code"] == 500

    def test_message_internal(self, client):
        assert body(client.get("/raise/unhandled"))["message"] == "Internal Server Error"

    def test_detail_mentions_unexpected(self, client):
        assert "unexpected" in body(client.get("/raise/unhandled"))["detail"].lower()

    def test_data_null(self, client):
        assert body(client.get("/raise/unhandled"))["data"] is None

    def test_internal_message_not_leaked(self, client):
        """Raw exception message must never be exposed to the client."""
        b = body(client.get("/raise/unhandled"))
        assert "Something went very wrong" not in b["detail"]
        assert "Something went very wrong" not in b.get("message", "")

    def test_value_error_500(self, client):
        assert client.get("/raise/unhandled/valueerror").status_code == 500

    def test_zero_division_500(self, client):
        assert client.get("/raise/unhandled/zerodiv").status_code == 500

    def test_no_errors_key(self, client):
        assert "errors" not in body(client.get("/raise/unhandled"))

    def test_response_content_type_is_json(self, client):
        r = client.get("/raise/unhandled")
        assert r.headers["content-type"].startswith("application/json")


# ===========================================================================
# 8. EMSException – direct unit tests (no HTTP layer)
# ===========================================================================

class TestEMSExceptionDirect:

    def test_default_status_code(self):
        assert EMSException().status_code == 500

    def test_default_message(self):
        assert EMSException().message == "Internal Server Error"

    def test_default_detail(self):
        assert EMSException().detail == "An unexpected error occurred"

    def test_default_errors_is_none(self):
        assert EMSException().errors is None

    def test_override_message(self):
        assert EMSException(message="Custom").message == "Custom"

    def test_override_detail(self):
        assert EMSException(detail="Desc").detail == "Desc"

    def test_override_status_code(self):
        assert EMSException(status_code=418).status_code == 418

    def test_errors_stored(self):
        errs = [{"field": "x"}]
        assert EMSException(errors=errs).errors == errs

    def test_to_dict_without_errors(self):
        d = EMSException(status_code=400, message="Bad", detail="desc").to_dict()
        assert d == {"code": 400, "message": "Bad", "detail": "desc", "data": None}
        assert "errors" not in d

    def test_to_dict_with_errors(self):
        errs = [{"field": "name"}]
        d = EMSException(errors=errs).to_dict()
        assert "errors" in d
        assert d["errors"] == errs

    def test_repr_contains_code_and_message(self):
        r = repr(EMSException(status_code=400, message="Bad", detail="x"))
        assert "400" in r
        assert "Bad" in r

    def test_str_equals_message(self):
        assert str(EMSException(message="hello")) == "hello"

    def test_is_exception_subclass(self):
        assert issubclass(EMSException, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(EMSException):
            raise EMSException()


# ===========================================================================
# 9. register_exception_handlers – side-effects
# ===========================================================================

class TestRegisterExceptionHandlers:

    def test_returns_none(self):
        assert register_exception_handlers(FastAPI()) is None

    def test_at_least_four_handlers_registered(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        assert len(_app.exception_handlers) >= 4

    def test_idempotent_on_different_apps(self):
        app1, app2 = FastAPI(), FastAPI()
        register_exception_handlers(app1)
        register_exception_handlers(app2)
        assert app1 is not app2
        assert len(app1.exception_handlers) == len(app2.exception_handlers)


# ===========================================================================
# 10. Logging – handlers emit correct log levels
# ===========================================================================

class TestExceptionHandlerLogging:

    def test_ems_exception_logs_warning(self, client, caplog):
        with caplog.at_level(logging.WARNING, logger="ems.exception_handler"):
            client.get("/raise/ems?exc_type=bad_request")
        assert any("EMSException" in r.message for r in caplog.records)

    def test_http_exception_logs_warning(self, client, caplog):
        with caplog.at_level(logging.WARNING, logger="ems.exception_handler"):
            client.get("/raise/http/404")
        assert any("HTTPException" in r.message for r in caplog.records)

    def test_unhandled_exception_logs_error(self, client, caplog):
        with caplog.at_level(logging.ERROR, logger="ems.exception_handler"):
            client.get("/raise/unhandled")
        assert any(r.levelname == "ERROR" for r in caplog.records)

    def test_validation_error_returns_422(self):
        """Smoke-test: validation handler is wired correctly."""
        from pydantic import BaseModel

        _app = FastAPI()
        register_exception_handlers(_app)

        class Item(BaseModel):
            age: int

        @_app.post("/v")
        async def v(item: Item):
            return item

        c = TestClient(_app, raise_server_exceptions=False)
        r = c.post("/v", json={"age": "bad"})
        assert r.status_code == 422
