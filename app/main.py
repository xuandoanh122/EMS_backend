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

# Load .env tá»« thÆ° má»¥c gá»‘c project (d:\EMS_backend\.env)
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
# Lifespan â€“ startup / shutdown hooks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # â”€â”€ Startup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("EMS starting upâ€¦")
    await init_db()    # connects to MSSQL (or SQLite fallback) + creates tables
    yield
    # â”€â”€ Shutdown â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    logger.info("EMS shutting downâ€¦")
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
            "Há»‡ thá»‘ng Quáº£n lÃ½ GiÃ¡o dá»¥c - API Backend. "
            "Quáº£n lÃ½ Há»c sinh, GiÃ¡o viÃªn, CÆ¡ sá»Ÿ váº­t cháº¥t."
        ),
        version="1.0.0",
        docs_url="/docs",     # Swagger UI
        redoc_url="/redoc",   # ReDoc
        lifespan=lifespan,
    )

    # â”€â”€ CORS middleware â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # â”€â”€ Register global exception handlers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    register_exception_handlers(app)

    # â”€â”€ Include module routers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    from app.modules.student.controller import router as student_router
    from app.modules.teacher.controller import router as teacher_router
    from app.modules.classroom.controller import router as classroom_router
    from app.modules.grading.controller import router as grading_router
    from app.modules.salary.controller import router as salary_router
    from app.modules.dashboard.controller import router as dashboard_router
    from app.modules.auth.controller import router as auth_router
    from app.modules.auth.init_routes import router as init_router
    from app.modules.lookups.controller import router as lookups_router
    from app.modules.teacher_portal.controller import admin_router as teacher_portal_admin_router
    from app.modules.teacher_portal.controller import router as teacher_portal_router

    app.include_router(student_router,   prefix="/api/v1/students",   tags=["Students"])
    app.include_router(teacher_router,   prefix="/api/v1/teachers",   tags=["Teachers"])
    app.include_router(classroom_router, prefix="/api/v1/classrooms", tags=["Classrooms"])
    app.include_router(grading_router,   prefix="/api/v1/grading",    tags=["Grading"])
    app.include_router(salary_router,    prefix="/api/v1/salary",     tags=["Salary"])
    app.include_router(dashboard_router, prefix="/api/v1/dashboard",  tags=["Dashboard"])
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(init_router, prefix="/api/v1/auth", tags=["Bootstrap"])
    app.include_router(lookups_router, prefix="/api/v1/lookups", tags=["Lookups"])
    app.include_router(teacher_portal_admin_router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(teacher_portal_router, prefix="/api/v1/teacher", tags=["Teacher Portal"])


    # â”€â”€ Health check endpoint â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
