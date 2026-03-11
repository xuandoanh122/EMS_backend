"""
EMS (Education Management System) - FastAPI Application Entry Point.

This is the main application file that creates and configures the FastAPI
instance, registers exception handlers, and includes module routers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

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

    # ── Register global exception handlers ──────────────────────────────
    register_exception_handlers(app)

    # ── Include module routers ───────────────────────────────────────────
    from app.modules.student.controller import router as student_router

    app.include_router(student_router, prefix="/api/v1/students", tags=["Students"])

    # Uncomment as you build each module:
    # from app.modules.auth.controller import router as auth_router
    # from app.modules.teacher.controller import router as teacher_router
    # from app.modules.facility.controller import router as facility_router
    # app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    # app.include_router(teacher_router, prefix="/api/v1/teachers", tags=["Teachers"])
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
