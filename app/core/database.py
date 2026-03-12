"""
Database configuration for EMS.

Strategy: PRIMARY (MSSQL) + BACKUP (SQLite fallback).
  - Khi khởi động, hệ thống thử kết nối PRIMARY trước.
  - Nếu PRIMARY không kết nối được → tự động chuyển sang BACKUP (SQLite local).
  - BACKUP chạy sync (không async) nhưng đủ để hệ thống không sập khi mất DB.

Cấu hình:
  - Điền MSSQL_* vào file .env khi deploy thực tế.
  - Username / Password để trống → bạn tự điền sau.

Usage:
    from app.core.database import get_async_session, engine

    # Trong FastAPI dependency:
    async def get_db():
        async with AsyncSessionLocal() as session:
            yield session
"""

import logging
import os
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

# Đảm bảo .env luôn được load dù module bị import trước main.py
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger("ems.database")

# ---------------------------------------------------------------------------
# Config – đọc lazy qua property để đảm bảo .env đã được load
# ---------------------------------------------------------------------------

def _cfg(key: str, default: str = "") -> str:
    return os.getenv(key, default)


SQLITE_BACKUP_PATH = Path(_cfg("SQLITE_BACKUP_PATH", "ems_backup.db"))

# ---------------------------------------------------------------------------
# Connection strings
# ---------------------------------------------------------------------------

def _build_mssql_url() -> str:
    """Build async MSSQL URL for SQLAlchemy (aioodbc driver)."""
    from urllib.parse import quote_plus
    host     = _cfg("MSSQL_HOST",     "localhost")
    port     = _cfg("MSSQL_PORT",     "1433")
    database = _cfg("MSSQL_DATABASE", "ems_db")
    username = _cfg("MSSQL_USERNAME", "ems_server")
    password = _cfg("MSSQL_PASSWORD", "Maiyeuem123@")
    driver   = _cfg("MSSQL_DRIVER",   "ODBC Driver 17 for SQL Server")

    auth = ""
    if username and password:
        auth = f"{quote_plus(username)}:{quote_plus(password)}@"
    elif username:
        auth = f"{quote_plus(username)}@"

    # Strip curly braces if present (e.g. "{ODBC Driver 17 for SQL Server}")
    # then URL-encode spaces as + for the query string
    driver = driver.strip("{}").replace(" ", "+")

    return (
        f"mssql+aioodbc://{auth}{host}:{port}/{database}"
        f"?driver={driver}"
    )


def _build_sqlite_url() -> str:
    """Build async SQLite URL for backup."""
    return f"sqlite+aiosqlite:///{SQLITE_BACKUP_PATH.resolve()}"


# ---------------------------------------------------------------------------
# Engine & Session factory – resolved at startup
# ---------------------------------------------------------------------------

_async_engine = None
_AsyncSessionLocal: async_sessionmaker | None = None
_is_using_backup: bool = False


def _create_mssql_engine():
    return create_async_engine(
        _build_mssql_url(),
        pool_size=int(_cfg("DB_POOL_SIZE", "10")),
        max_overflow=int(_cfg("DB_MAX_OVERFLOW", "20")),
        pool_timeout=int(_cfg("DB_POOL_TIMEOUT", "30")),
        pool_pre_ping=True,   # test connection before using from pool
        echo=False,
    )


def _create_sqlite_engine():
    return create_async_engine(
        _build_sqlite_url(),
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,   # share single connection in SQLite
        echo=False,
    )


async def init_db() -> None:
    """
    Called once at application startup (lifespan).

    1. Try to connect to PRIMARY (MSSQL).
    2. On failure → fall back to BACKUP (SQLite).
    3. Run create_all to ensure tables exist (safe for existing tables).
    """
    global _async_engine, _AsyncSessionLocal, _is_using_backup

    # ── Try PRIMARY ──────────────────────────────────────────────────────
    try:
        engine = _create_mssql_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))   # connectivity probe

        _async_engine = engine
        _is_using_backup = False
        logger.info("✅ Connected to PRIMARY database (MSSQL @ %s:%s/%s)",
                    _cfg("MSSQL_HOST", "localhost"),
                    _cfg("MSSQL_PORT", "1433"),
                    _cfg("MSSQL_DATABASE", "ems_db"))

    except Exception as primary_exc:
        logger.warning(
            "⚠️  PRIMARY database unavailable (%s). "
            "Falling back to BACKUP (SQLite: %s).",
            primary_exc,
            SQLITE_BACKUP_PATH.resolve(),
        )
        _async_engine = _create_sqlite_engine()
        _is_using_backup = True
        logger.info("✅ Connected to BACKUP database (SQLite @ %s)",
                    SQLITE_BACKUP_PATH.resolve())

    # ── Session factory ──────────────────────────────────────────────────
    _AsyncSessionLocal = async_sessionmaker(
        bind=_async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # ── Create tables ────────────────────────────────────────────────────
    await _create_tables()


async def _create_tables() -> None:
    """Create all tables that are registered on the metadata."""
    # Import here to avoid circular imports; all entities share the same Base
    from app.modules.student.entity import Base as StudentBase
    import app.modules.teacher.entity    # noqa: F401 – registers Teacher
    import app.modules.classroom.entity  # noqa: F401 – registers Classroom, StudentClassEnrollment
    import app.modules.salary.entity     # noqa: F401 – registers SalaryGrade, BonusPolicy, MonthlyPayroll, PayrollBonusDetail
    import app.modules.grading.entity    # noqa: F401 – registers Subject, ClassSubject, GradeComponent, StudentGrade, GradeAuditLog, SemesterAverage

    async with _async_engine.begin() as conn:
        await conn.run_sync(StudentBase.metadata.create_all)

    logger.info("📋 Database tables verified / created.")


async def close_db() -> None:
    """Dispose the engine pool gracefully on shutdown."""
    if _async_engine:
        await _async_engine.dispose()
        logger.info("🔌 Database engine disposed.")


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def is_using_backup() -> bool:
    """Returns True when the system is running on the SQLite backup DB."""
    return _is_using_backup


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency – yields an AsyncSession.

    Usage in controller:
        async def endpoint(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    if _AsyncSessionLocal is None:
        raise RuntimeError(
            "Database has not been initialised. "
            "Ensure init_db() is called during application startup."
        )
    async with _AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
