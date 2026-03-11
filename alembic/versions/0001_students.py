"""create students and students_backup tables

Revision ID: 0001_students
Revises:
Create Date: 2026-03-11

Tables:
  - students        : bảng chính (MSSQL / SQLite).
  - students_backup : bảng dự phòng – cấu trúc giống hệt students,
                      dùng để lưu snapshot khi mất kết nối PRIMARY
                      hoặc trước khi chạy batch operation lớn.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_students"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Shared column definition – reused for both tables
# ---------------------------------------------------------------------------

def _student_columns() -> list:
    """Return the column list shared by students and students_backup."""
    return [
        sa.Column("id",               sa.Integer,     primary_key=True, autoincrement=True),
        sa.Column("student_code",     sa.String(20),  nullable=False),
        sa.Column("full_name",        sa.String(150), nullable=False),
        sa.Column("date_of_birth",    sa.Date,        nullable=True),
        sa.Column("gender",           sa.String(10),  nullable=True),
        sa.Column("national_id",      sa.String(20),  nullable=True),
        sa.Column("email",            sa.String(200), nullable=True),
        sa.Column("phone_number",     sa.String(20),  nullable=True),
        sa.Column("address",          sa.Text,        nullable=True),
        sa.Column("enrollment_date",  sa.Date,        nullable=True),
        sa.Column(
            "academic_status",
            sa.Enum(
                "active", "preserved", "suspended", "graduated",
                name="studentstatus",
                create_constraint=True,
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column("class_name",       sa.String(50),  nullable=True),
        sa.Column("program_name",     sa.String(200), nullable=True),
        sa.Column("parent_full_name", sa.String(150), nullable=True),
        sa.Column("parent_phone",     sa.String(20),  nullable=True),
        sa.Column("parent_email",     sa.String(200), nullable=True),
        sa.Column("medical_notes",    sa.Text,        nullable=True),
        sa.Column("is_active",        sa.Boolean,     nullable=False, server_default=sa.true()),
        sa.Column("created_at",       sa.DateTime,    nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",       sa.DateTime,    nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    ]


def upgrade() -> None:
    # ── 1. students (primary table) ──────────────────────────────────────
    op.create_table("students", *_student_columns())

    # Unique constraints
    op.create_unique_constraint("uq_students_student_code", "students", ["student_code"])
    op.create_unique_constraint("uq_students_national_id",  "students", ["national_id"])
    op.create_unique_constraint("uq_students_email",        "students", ["email"])

    # Indexes for frequent lookups
    op.create_index("ix_students_id",           "students", ["id"],           unique=True)
    op.create_index("ix_students_student_code", "students", ["student_code"], unique=True)
    op.create_index("ix_students_national_id",  "students", ["national_id"],  unique=False)
    op.create_index("ix_students_email",        "students", ["email"],        unique=False)
    op.create_index("ix_students_academic_status", "students", ["academic_status"], unique=False)
    op.create_index("ix_students_class_name",   "students", ["class_name"],   unique=False)
    op.create_index("ix_students_is_active",    "students", ["is_active"],    unique=False)

    # ── 2. students_backup (fallback / snapshot table) ───────────────────
    # Same structure; uniqueness constraints relaxed on backup
    # so we can store multiple historical snapshots of the same student.
    op.create_table(
        "students_backup",
        sa.Column("backup_id",     sa.Integer,  primary_key=True, autoincrement=True),
        sa.Column("backup_reason", sa.String(200), nullable=True,
                  comment="e.g. 'pre_batch_import', 'primary_db_offline'"),
        sa.Column("backed_up_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
        # ── original student columns (nullable here for flexibility) ──
        sa.Column("id",               sa.Integer),
        sa.Column("student_code",     sa.String(20),  nullable=True),
        sa.Column("full_name",        sa.String(150), nullable=True),
        sa.Column("date_of_birth",    sa.Date,        nullable=True),
        sa.Column("gender",           sa.String(10),  nullable=True),
        sa.Column("national_id",      sa.String(20),  nullable=True),
        sa.Column("email",            sa.String(200), nullable=True),
        sa.Column("phone_number",     sa.String(20),  nullable=True),
        sa.Column("address",          sa.Text,        nullable=True),
        sa.Column("enrollment_date",  sa.Date,        nullable=True),
        sa.Column(
            "academic_status",
            sa.Enum(
                "active", "preserved", "suspended", "graduated",
                name="studentstatus",
                create_constraint=False,   # reuse existing enum type
            ),
            nullable=True,
        ),
        sa.Column("class_name",       sa.String(50),  nullable=True),
        sa.Column("program_name",     sa.String(200), nullable=True),
        sa.Column("parent_full_name", sa.String(150), nullable=True),
        sa.Column("parent_phone",     sa.String(20),  nullable=True),
        sa.Column("parent_email",     sa.String(200), nullable=True),
        sa.Column("medical_notes",    sa.Text,        nullable=True),
        sa.Column("is_active",        sa.Boolean,     nullable=True),
        sa.Column("created_at",       sa.DateTime,    nullable=True),
        sa.Column("updated_at",       sa.DateTime,    nullable=True),
    )

    # Index for quick lookup by original student id / code
    op.create_index("ix_students_backup_student_code", "students_backup", ["student_code"])
    op.create_index("ix_students_backup_id",           "students_backup", ["id"])
    op.create_index("ix_students_backup_backed_up_at", "students_backup", ["backed_up_at"])


def downgrade() -> None:
    # Drop indexes first, then tables
    op.drop_index("ix_students_backup_backed_up_at", table_name="students_backup")
    op.drop_index("ix_students_backup_id",           table_name="students_backup")
    op.drop_index("ix_students_backup_student_code", table_name="students_backup")
    op.drop_table("students_backup")

    op.drop_index("ix_students_is_active",        table_name="students")
    op.drop_index("ix_students_class_name",       table_name="students")
    op.drop_index("ix_students_academic_status",  table_name="students")
    op.drop_index("ix_students_email",            table_name="students")
    op.drop_index("ix_students_national_id",      table_name="students")
    op.drop_index("ix_students_student_code",     table_name="students")
    op.drop_index("ix_students_id",               table_name="students")

    op.drop_constraint("uq_students_email",        "students", type_="unique")
    op.drop_constraint("uq_students_national_id",  "students", type_="unique")
    op.drop_constraint("uq_students_student_code", "students", type_="unique")
    op.drop_table("students")

    # Drop enum type (PostgreSQL / MSSQL; no-op on SQLite)
    sa.Enum(name="studentstatus").drop(op.get_bind(), checkfirst=True)
