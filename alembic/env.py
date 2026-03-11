"""
Alembic environment script.

Resolves the SQLAlchemy URL dynamically from app.core.database config
so we don't hard-code credentials here.

For async engines (aioodbc / aiosqlite) we use run_async_migrations().
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Make sure 'app' package is importable ───────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ── Import metadata from ALL entities so autogenerate can see every table ───
from app.modules.student.entity import Base as StudentBase  # noqa: E402

target_metadata = StudentBase.metadata

# ── Alembic Config object ────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Resolve DB URL at migration time ─────────────────────────────────────────
def _get_url() -> str:
    """
    Priority:
      1. DATABASE_URL env var (CI/CD override)
      2. MSSQL env vars → build mssql+aioodbc URL
      3. Fallback to SQLite backup
    """
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    host     = os.getenv("MSSQL_HOST",     "localhost")
    port     = os.getenv("MSSQL_PORT",     "1433")
    db       = os.getenv("MSSQL_DATABASE", "ems_db")
    user     = os.getenv("MSSQL_USERNAME", "")
    pwd      = os.getenv("MSSQL_PASSWORD", "")
    driver   = os.getenv("MSSQL_DRIVER",   "ODBC+Driver+17+for+SQL+Server")

    auth = f"{user}:{pwd}@" if user and pwd else (f"{user}@" if user else "")
    return (
        f"mssql+aioodbc://{auth}{host}:{port}/{db}?driver={driver}"
    )


# ── Offline migrations (generates SQL script without connecting) ──────────────
def run_migrations_offline() -> None:
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (connects to DB and runs) ───────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entry point ───────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
