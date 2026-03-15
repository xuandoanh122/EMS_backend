"""
Unit tests for EMS Application – Route Registration & Health Check.

Verifies:
  1. Application creates successfully via create_app()
  2. Health check endpoint responds correctly
  3. ALL module routers are registered with correct prefixes
  4. Teacher portal router (bug fix) is properly included
  5. No duplicate/dead lookup module exists
  6. CORS middleware is configured
  7. All expected route paths are present
"""

import importlib
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app() -> FastAPI:
    """Import the real application instance."""
    from app.main import create_app
    return create_app()


@pytest.fixture(scope="module")
def client(app: FastAPI) -> TestClient:
    """TestClient wrapping the real app (no actual DB needed for route checks)."""
    return TestClient(app, raise_server_exceptions=False)


def _get_route_paths(app: FastAPI) -> set[str]:
    """Extract all registered route paths from the app."""
    return {
        r.path
        for r in app.routes
        if hasattr(r, "path") and hasattr(r, "methods")
    }


def _get_route_methods(app: FastAPI) -> dict[str, set[str]]:
    """Map path -> set of HTTP methods."""
    result: dict[str, set[str]] = {}
    for r in app.routes:
        if hasattr(r, "path") and hasattr(r, "methods"):
            result[r.path] = set(r.methods)
    return result


# ===========================================================================
# 1. Application Factory
# ===========================================================================

class TestApplicationFactory:

    def test_create_app_returns_fastapi_instance(self, app):
        assert isinstance(app, FastAPI)

    def test_app_title(self, app):
        assert "EMS" in app.title

    def test_app_version(self, app):
        assert app.version == "1.0.0"

    def test_docs_url(self, app):
        assert app.docs_url == "/docs"

    def test_redoc_url(self, app):
        assert app.redoc_url == "/redoc"


# ===========================================================================
# 2. Health Check Endpoint
# ===========================================================================

class TestHealthCheck:

    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_structure(self, client):
        b = client.get("/health").json()
        assert b["code"] == 200
        assert b["message"] == "Success"
        assert "EMS Backend is running" in b["detail"]

    def test_health_data_has_status(self, client):
        data = client.get("/health").json()["data"]
        assert data["status"] == "healthy"

    def test_health_data_has_database_field(self, client):
        data = client.get("/health").json()["data"]
        assert "database" in data


# ===========================================================================
# 3. Student Module Routes
# ===========================================================================

class TestStudentRoutes:

    def test_student_list_path_registered(self, app):
        assert "/api/v1/students" in _get_route_paths(app)

    def test_student_detail_path_registered(self, app):
        assert "/api/v1/students/{student_id}" in _get_route_paths(app)

    def test_student_list_supports_get(self, app):
        methods = _get_route_methods(app)
        assert "GET" in methods.get("/api/v1/students", set())

    def test_student_list_supports_post(self, app):
        methods = _get_route_methods(app)
        assert "POST" in methods.get("/api/v1/students", set())


# ===========================================================================
# 4. Teacher Module Routes
# ===========================================================================

class TestTeacherRoutes:

    def test_teacher_list_path_registered(self, app):
        assert "/api/v1/teachers" in _get_route_paths(app)

    def test_teacher_detail_path_registered(self, app):
        assert "/api/v1/teachers/{teacher_id}" in _get_route_paths(app)


# ===========================================================================
# 5. Classroom Module Routes
# ===========================================================================

class TestClassroomRoutes:

    def test_classroom_list_path_registered(self, app):
        assert "/api/v1/classrooms" in _get_route_paths(app)


# ===========================================================================
# 6. Grading Module Routes
# ===========================================================================

class TestGradingRoutes:

    def test_grading_path_registered(self, app):
        paths = _get_route_paths(app)
        grading_paths = [p for p in paths if p.startswith("/api/v1/grading")]
        assert len(grading_paths) > 0, "No grading routes found"


# ===========================================================================
# 7. Salary Module Routes
# ===========================================================================

class TestSalaryRoutes:

    def test_salary_path_registered(self, app):
        paths = _get_route_paths(app)
        salary_paths = [p for p in paths if p.startswith("/api/v1/salary")]
        assert len(salary_paths) > 0, "No salary routes found"


# ===========================================================================
# 8. Dashboard Module Routes
# ===========================================================================

class TestDashboardRoutes:

    def test_dashboard_stats_path_registered(self, app):
        assert "/api/v1/dashboard/stats" in _get_route_paths(app)


# ===========================================================================
# 9. Auth Module Routes
# ===========================================================================

class TestAuthRoutes:

    def test_auth_login_registered(self, app):
        assert "/api/v1/auth/login" in _get_route_paths(app)

    def test_auth_refresh_registered(self, app):
        assert "/api/v1/auth/refresh" in _get_route_paths(app)

    def test_auth_logout_registered(self, app):
        assert "/api/v1/auth/logout" in _get_route_paths(app)

    def test_auth_users_registered(self, app):
        assert "/api/v1/auth/users" in _get_route_paths(app)


# ===========================================================================
# 10. Lookups Module Routes
# ===========================================================================

class TestLookupsRoutes:

    def test_lookups_teachers_registered(self, app):
        assert "/api/v1/lookups/teachers" in _get_route_paths(app)

    def test_lookups_classrooms_registered(self, app):
        assert "/api/v1/lookups/classrooms" in _get_route_paths(app)

    def test_lookups_students_registered(self, app):
        assert "/api/v1/lookups/students" in _get_route_paths(app)

    def test_lookups_subjects_registered(self, app):
        assert "/api/v1/lookups/subjects" in _get_route_paths(app)


# ===========================================================================
# 11. Teacher Portal Routes (BUG FIX – was missing include_router)
# ===========================================================================

class TestTeacherPortalRoutes:
    """
    These tests verify the bug fix: teacher_portal_router was imported in
    main.py but never included via app.include_router(). All /api/v1/teacher/*
    endpoints were unreachable before the fix.
    """

    def test_teacher_dashboard_registered(self, app):
        assert "/api/v1/teacher/dashboard" in _get_route_paths(app)

    def test_teacher_assignments_registered(self, app):
        assert "/api/v1/teacher/assignments" in _get_route_paths(app)

    def test_teacher_classroom_students_registered(self, app):
        assert "/api/v1/teacher/classrooms/{classroom_id}/students" in _get_route_paths(app)

    def test_teacher_gradebook_matrix_registered(self, app):
        assert "/api/v1/teacher/gradebook/matrix" in _get_route_paths(app)

    def test_teacher_gradebook_entries_registered(self, app):
        assert "/api/v1/teacher/gradebook/entries" in _get_route_paths(app)

    def test_teacher_attendance_matrix_registered(self, app):
        assert "/api/v1/teacher/attendance/matrix" in _get_route_paths(app)

    def test_teacher_attendance_entries_registered(self, app):
        assert "/api/v1/teacher/attendance/entries" in _get_route_paths(app)

    def test_teacher_timetable_registered(self, app):
        assert "/api/v1/teacher/timetable" in _get_route_paths(app)

    def test_teacher_portal_has_get_methods(self, app):
        methods = _get_route_methods(app)
        assert "GET" in methods.get("/api/v1/teacher/dashboard", set())
        assert "GET" in methods.get("/api/v1/teacher/assignments", set())

    def test_teacher_portal_has_patch_methods(self, app):
        methods = _get_route_methods(app)
        assert "PATCH" in methods.get("/api/v1/teacher/gradebook/entries", set())
        assert "PATCH" in methods.get("/api/v1/teacher/attendance/entries", set())


# ===========================================================================
# 12. Admin Portal Routes (teacher_portal admin_router)
# ===========================================================================

class TestAdminPortalRoutes:

    def test_admin_timetable_list_registered(self, app):
        assert "/api/v1/admin/timetable" in _get_route_paths(app)

    def test_admin_timetable_detail_registered(self, app):
        assert "/api/v1/admin/timetable/{entry_id}" in _get_route_paths(app)

    def test_admin_attendance_matrix_registered(self, app):
        assert "/api/v1/admin/attendance/matrix" in _get_route_paths(app)

    def test_admin_attendance_entries_registered(self, app):
        assert "/api/v1/admin/attendance/entries" in _get_route_paths(app)


# ===========================================================================
# 13. Dead Module Removal – lookup/ should not exist
# ===========================================================================

class TestDeadModuleRemoved:
    """
    The old app/modules/lookup/ (without 's') was a monolithic duplicate of
    app/modules/lookups/. It was dead code after the branch merge. Verify it
    no longer exists.
    """

    def test_old_lookup_module_does_not_exist(self):
        lookup_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "modules", "lookup"
        )
        assert not os.path.exists(lookup_path), (
            f"Dead module 'app/modules/lookup/' still exists at {lookup_path}. "
            "It should be removed – 'app/modules/lookups/' is the active module."
        )

    def test_lookups_module_exists(self):
        lookups_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "modules", "lookups"
        )
        assert os.path.isdir(lookups_path), (
            "Active module 'app/modules/lookups/' is missing!"
        )

    def test_lookups_has_controller(self):
        controller_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "modules", "lookups", "controller.py"
        )
        assert os.path.isfile(controller_path)

    def test_lookups_has_service(self):
        service_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "modules", "lookups", "service.py"
        )
        assert os.path.isfile(service_path)

    def test_lookups_has_repository(self):
        repo_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "modules", "lookups", "repository.py"
        )
        assert os.path.isfile(repo_path)


# ===========================================================================
# 14. Complete Route Coverage Check
# ===========================================================================

class TestCompleteRouteCoverage:
    """Verify minimum number of routes are registered for each module prefix."""

    @pytest.mark.parametrize(
        "prefix, min_count",
        [
            ("/api/v1/students", 2),
            ("/api/v1/teachers", 2),
            ("/api/v1/classrooms", 1),
            ("/api/v1/grading", 1),
            ("/api/v1/salary", 1),
            ("/api/v1/dashboard", 1),
            ("/api/v1/auth", 4),
            ("/api/v1/lookups", 4),
            ("/api/v1/admin", 4),
            ("/api/v1/teacher", 7),   # Bug fix: was 0 before
        ],
    )
    def test_module_has_minimum_routes(self, app, prefix, min_count):
        paths = _get_route_paths(app)
        matching = [p for p in paths if p.startswith(prefix)]
        assert len(matching) >= min_count, (
            f"Expected at least {min_count} routes under '{prefix}', "
            f"found {len(matching)}: {matching}"
        )


# ===========================================================================
# 15. Module Import Integrity
# ===========================================================================

class TestModuleImports:
    """Verify all module controllers can be imported without error."""

    @pytest.mark.parametrize(
        "module_path",
        [
            "app.modules.student.controller",
            "app.modules.teacher.controller",
            "app.modules.classroom.controller",
            "app.modules.grading.controller",
            "app.modules.salary.controller",
            "app.modules.dashboard.controller",
            "app.modules.auth.controller",
            "app.modules.lookups.controller",
            "app.modules.teacher_portal.controller",
        ],
    )
    def test_controller_importable(self, module_path):
        mod = importlib.import_module(module_path)
        assert hasattr(mod, "router"), f"{module_path} missing 'router' attribute"

    def test_teacher_portal_exports_both_routers(self):
        from app.modules.teacher_portal.controller import router, admin_router
        assert router is not None
        assert admin_router is not None
        assert router is not admin_router

    def test_old_lookup_module_not_importable(self):
        """Ensure the dead lookup module cannot be imported."""
        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.import_module("app.modules.lookup.controller")


# ===========================================================================
# 16. CORS Middleware
# ===========================================================================

class TestCORSMiddleware:

    def test_cors_allows_origin_header(self, client):
        r = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS should respond with access-control-allow-origin
        assert "access-control-allow-origin" in r.headers


# ===========================================================================
# 17. Response Format Consistency
# ===========================================================================

class TestResponseFormat:

    def test_health_response_has_standard_keys(self, client):
        b = client.get("/health").json()
        required_keys = {"code", "message", "detail", "data"}
        assert required_keys.issubset(b.keys()), (
            f"Missing keys: {required_keys - set(b.keys())}"
        )

    def test_nonexistent_route_returns_json(self, client):
        r = client.get("/this/does/not/exist")
        assert r.status_code == 404
        # Should still return JSON (via exception handler)
        b = r.json()
        assert "code" in b or "detail" in b
