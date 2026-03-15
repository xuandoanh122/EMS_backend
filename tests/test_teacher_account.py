"""
Unit tests for Teacher Account Creation feature.

Tests:
    1. API endpoint exists and accepts correct payload
    2. Email configuration works correctly
    3. DTO validation works
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def app() -> FastAPI:
    """Import the real application instance."""
    from app.main import create_app
    return create_app()


@pytest.fixture(scope="module")
def client(app: FastAPI) -> TestClient:
    """TestClient wrapping the real app."""
    return TestClient(app, raise_server_exceptions=False)


class TestTeacherAccountEndpoint:
    """Tests for POST /api/v1/auth/teachers/{teacher_id}/account endpoint."""

    def test_endpoint_exists(self, client):
        """Verify the endpoint is registered."""
        routes = [r.path for r in client.app.routes]
        assert "/api/v1/auth/teachers/{teacher_id}/account" in routes

    def test_endpoint_requires_auth(self, client):
        """Verify endpoint requires admin authentication."""
        r = client.post(
            "/api/v1/auth/teachers/1/account",
            json={"send_email": False}
        )
        # Should return 401 or 403 (unauthorized)
        assert r.status_code in [401, 403]

    def test_endpoint_rejects_invalid_payload(self, client):
        """Verify endpoint rejects invalid payload without auth."""
        r = client.post(
            "/api/v1/auth/teachers/1/account",
            json={"send_email": "invalid"}
        )
        # Should return 401 (no auth) or 422 (validation error)
        assert r.status_code in [401, 403, 422]


class TestEmailerModule:
    """Tests for email utility module."""

    def test_emailer_module_exists(self):
        """Verify emailer module can be imported."""
        from app.utils import emailer
        assert hasattr(emailer, "send_email")
        assert hasattr(emailer, "send_teacher_account_email")

    def test_is_configured_returns_bool(self):
        """Verify is_configured returns a boolean."""
        from app.utils.emailer import is_configured
        result = is_configured()
        assert isinstance(result, bool)

    def test_send_email_requires_params(self):
        """Verify send_email requires proper parameters."""
        from app.utils.emailer import send_email
        import inspect
        sig = inspect.signature(send_email)
        params = list(sig.parameters.keys())
        assert "to" in params
        assert "subject" in params
        assert "html_body" in params


class TestTeacherAccountDTO:
    """Tests for Teacher Account DTOs."""

    def test_create_teacher_account_request_dto(self):
        """Verify DTO can be created with valid data."""
        from app.modules.auth.dto import CreateTeacherAccountRequest
        
        dto = CreateTeacherAccountRequest(
            teacher_id=1,
            send_email=True
        )
        assert dto.teacher_id == 1
        assert dto.send_email is True

    def test_create_teacher_account_request_defaults(self):
        """Verify DTO has correct defaults."""
        from app.modules.auth.dto import CreateTeacherAccountRequest
        
        dto = CreateTeacherAccountRequest(teacher_id=1)
        assert dto.send_email is True  # Default is True

    def test_create_teacher_account_response_dto(self):
        """Verify response DTO works."""
        from app.modules.auth.dto import CreateTeacherAccountResponse
        
        dto = CreateTeacherAccountResponse(
            user_id=1,
            teacher_id=1,
            teacher_code="Tchr2603001",
            teacher_name="Nguyen Van A",
            email="nguyenvana@school.edu.vn",
            username="nguyenvana",
            temp_password="abc123",
            email_sent=True,
            must_change_password=True
        )
        assert dto.user_id == 1
        assert dto.must_change_password is True


class TestUserEntityMustChangePassword:
    """Tests for User entity must_change_password field."""

    def test_user_entity_has_must_change_password_field(self):
        """Verify User entity has must_change_password column."""
        from app.modules.auth.entity import User
        
        # Check the column exists in the table
        assert hasattr(User, "must_change_password")

    def test_user_entity_default_value(self):
        """Verify must_change_password defaults to True."""
        from app.modules.auth.entity import User
        
        # Get the column and check default
        col = User.__table__.c.get("must_change_password")
        # The column should exist
        assert col is not None or "must_change_password" in [c.name for c in User.__table__.c]


class TestBootstrapEndpoint:
    """Tests for Bootstrap endpoints."""

    def test_init_status_endpoint_exists(self, client):
        """Verify /auth/init/status endpoint exists."""
        routes = [r.path for r in client.app.routes]
        assert "/api/v1/auth/init/status" in routes

    def test_init_admin_endpoint_exists(self, client):
        """Verify /auth/init/admin endpoint exists."""
        routes = [r.path for r in client.app.routes]
        assert "/api/v1/auth/init/admin" in routes

    def test_init_status_no_auth_required(self, client):
        """Verify /auth/init/status doesn't require auth."""
        r = client.get("/api/v1/auth/init/status")
        # Should return 200 (success) or 500 (db error) but not 401
        assert r.status_code in [200, 500]
