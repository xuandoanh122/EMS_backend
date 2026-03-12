"""
EMS (Education Management System) - FastAPI Application Entry Point.

This is the main application file that creates and configures the FastAPI
instance, registers exception handlers, and includes module routers.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env từ thư mục gốc project (d:\EMS_backend\.env)
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from app.core.database import close_db, init_db
from app.core.handlers.exception_handler import register_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("ems")


# ---------------------------------------------------------------------------
# Lifespan – startup / shutdown hooks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("EMS starting up…")
    await init_db()    # connects to MSSQL (or SQLite fallback) + creates tables
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("EMS shutting down…")
    await close_db()   # disposes connection pool


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """
    Application factory pattern.
    Creates and configures the FastAPI application instance.
    """
    app = FastAPI(
        title="EMS - Education Management System",
        description=(
            "Hệ thống Quản lý Giáo dục - API Backend. "
            "Quản lý Học sinh, Giáo viên, Cơ sở vật chất."
        ),
        version="1.0.0",
        docs_url="/docs",     # Swagger UI
        redoc_url="/redoc",   # ReDoc
        lifespan=lifespan,
    )

    # ── CORS middleware ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Register global exception handlers ──────────────────────────────
    register_exception_handlers(app)

    # ── Include module routers ───────────────────────────────────────────
    from app.modules.student.controller import router as student_router
    from app.modules.teacher.controller import router as teacher_router
    from app.modules.classroom.controller import router as classroom_router
    from app.modules.grading.controller import router as grading_router
    from app.modules.salary.controller import router as salary_router
    from app.modules.dashboard.controller import router as dashboard_router

    app.include_router(student_router,   prefix="/api/v1/students",   tags=["Students"])
    app.include_router(teacher_router,   prefix="/api/v1/teachers",   tags=["Teachers"])
    app.include_router(classroom_router, prefix="/api/v1/classrooms", tags=["Classrooms"])
    app.include_router(grading_router,   prefix="/api/v1/grading",    tags=["Grading"])
    app.include_router(salary_router,    prefix="/api/v1/salary",     tags=["Salary"])
    app.include_router(dashboard_router, prefix="/api/v1/dashboard",  tags=["Dashboard"])

    # Uncomment as you build each module:
    # from app.modules.auth.controller import router as auth_router
    # from app.modules.facility.controller import router as facility_router
    # app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    # app.include_router(facility_router, prefix="/api/v1/facilities", tags=["Facilities"])

    # ── Health check endpoint ────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health_check():
        from app.core.database import is_using_backup
        db_mode = "backup (SQLite)" if is_using_backup() else "primary (MSSQL)"
        return {
            "code": 200,
            "message": "Success",
            "detail": "EMS Backend is running",
            "data": {"status": "healthy", "database": db_mode},
        }

    logger.info("EMS Application initialized successfully")
    return app


# Create the application instance
app = create_app()
