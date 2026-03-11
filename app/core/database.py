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

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

logger = logging.getLogger("ems.database")

# ---------------------------------------------------------------------------
# Config – fill in .env or edit directly
# ---------------------------------------------------------------------------

MSSQL_HOST     = os.getenv("MSSQL_HOST",     "localhost")
MSSQL_PORT     = os.getenv("MSSQL_PORT",     "1433")
MSSQL_DATABASE = os.getenv("MSSQL_DATABASE", "ems_db")
MSSQL_USERNAME = os.getenv("MSSQL_USERNAME", "")   # ← điền sau
MSSQL_PASSWORD = os.getenv("MSSQL_PASSWORD", "")   # ← điền sau
MSSQL_DRIVER   = os.getenv("MSSQL_DRIVER",   "ODBC+Driver+17+for+SQL+Server")

# SQLite backup path (relative to project root)
SQLITE_BACKUP_PATH = Path(os.getenv("SQLITE_BACKUP_PATH", "ems_backup.db"))

# Pool settings (only for MSSQL)
DB_POOL_SIZE    = int(os.getenv("DB_POOL_SIZE",    "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# ---------------------------------------------------------------------------
# Connection strings
# ---------------------------------------------------------------------------

def _build_mssql_url() -> str:
    """Build async MSSQL URL for SQLAlchemy (aioodbc driver)."""
    auth = ""
    if MSSQL_USERNAME and MSSQL_PASSWORD:
        auth = f"{MSSQL_USERNAME}:{MSSQL_PASSWORD}@"
    elif MSSQL_USERNAME:
        auth = f"{MSSQL_USERNAME}@"

    return (
        f"mssql+aioodbc://{auth}{MSSQL_HOST}:{MSSQL_PORT}/{MSSQL_DATABASE}"
        f"?driver={MSSQL_DRIVER}"
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
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
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
                    MSSQL_HOST, MSSQL_PORT, MSSQL_DATABASE)

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
    # Import here to avoid circular imports; entity registers on Base.metadata
    from app.modules.student.entity import Base as StudentBase

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
