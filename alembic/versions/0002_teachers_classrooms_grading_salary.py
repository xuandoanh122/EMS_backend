"""create teachers, classrooms, enrollments, grading and salary tables

Revision ID: 0002_teachers_classrooms_grading_salary
Revises: 0001_students
Create Date: 2026-03-12

Tables created (in FK dependency order):
  1. teachers
  2. classrooms                   (FK → teachers)
  3. student_class_enrollments    (FK → students, classrooms)
  4. subjects
  5. class_subjects               (FK → classrooms, subjects, teachers)
  6. grade_components             (FK → class_subjects)
  7. student_grades               (FK → students, class_subjects, grade_components, teachers)
  8. grade_audit_log              (FK → student_grades, teachers)
  9. semester_averages            (FK → students, class_subjects)
 10. salary_grades
 11. bonus_policies
 12. monthly_payroll              (FK → teachers, salary_grades)
 13. payroll_bonus_details        (FK → monthly_payroll, bonus_policies)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_teachers_classrooms_grading_salary"
down_revision: Union[str, None] = "0001_students"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── 1. teachers ─────────────────────────────────────────────────────────
    op.create_table(
        "teachers",
        sa.Column("id",                sa.Integer,     primary_key=True, autoincrement=True),
        sa.Column("teacher_code",      sa.String(20),  nullable=False),
        sa.Column("full_name",         sa.Unicode(150), nullable=False),
        sa.Column("date_of_birth",     sa.Date,        nullable=True),
        sa.Column("gender",            sa.String(10),  nullable=True),
        sa.Column("national_id",       sa.String(20),  nullable=True),
        sa.Column("email",             sa.String(200), nullable=True),
        sa.Column("phone_number",      sa.String(20),  nullable=True),
        sa.Column("address",           sa.UnicodeText, nullable=True),
        sa.Column("specialization",    sa.Unicode(200), nullable=True),
        sa.Column("qualification",     sa.Unicode(200), nullable=True),
        sa.Column("join_date",         sa.Date,        nullable=True),
        sa.Column(
            "employment_status",
            sa.Enum(
                "active", "on_leave", "resigned", "retired",
                name="teacherstatus",
                create_constraint=True,
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column("department",  sa.Unicode(200), nullable=True),
        sa.Column("is_active",   sa.Boolean,      nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime,     nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime,     nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_unique_constraint("uq_teachers_teacher_code", "teachers", ["teacher_code"])
    op.create_unique_constraint("uq_teachers_national_id",  "teachers", ["national_id"])
    op.create_unique_constraint("uq_teachers_email",        "teachers", ["email"])
    op.create_index("ix_teachers_id",                "teachers", ["id"],                unique=True)
    op.create_index("ix_teachers_teacher_code",      "teachers", ["teacher_code"],      unique=True)
    op.create_index("ix_teachers_national_id",       "teachers", ["national_id"],       unique=False)
    op.create_index("ix_teachers_email",             "teachers", ["email"],             unique=False)
    op.create_index("ix_teachers_employment_status", "teachers", ["employment_status"], unique=False)
    op.create_index("ix_teachers_department",        "teachers", ["department"],        unique=False)
    op.create_index("ix_teachers_is_active",         "teachers", ["is_active"],         unique=False)

    # ── 2. classrooms ────────────────────────────────────────────────────────
    op.create_table(
        "classrooms",
        sa.Column("id",           sa.Integer,      primary_key=True, autoincrement=True),
        sa.Column("class_code",   sa.String(30),   nullable=False),
        sa.Column("class_name",   sa.Unicode(100), nullable=False),
        sa.Column(
            "class_type",
            sa.Enum("standard", "cambridge", name="classtype", create_constraint=True),
            nullable=False,
            server_default="standard",
        ),
        sa.Column("academic_year",        sa.String(10), nullable=False),
        sa.Column("grade_level",          sa.Integer,    nullable=False),
        sa.Column("homeroom_teacher_id",  sa.Integer,    sa.ForeignKey("teachers.id", ondelete="NO ACTION"), nullable=True),
        sa.Column("max_capacity",         sa.Integer,    nullable=False, server_default="40"),
        sa.Column("room_number",          sa.String(20), nullable=True),
        sa.Column("description",          sa.Unicode(300), nullable=True),
        sa.Column("is_active",   sa.Boolean,  nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime, nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_unique_constraint("uq_classrooms_class_code", "classrooms", ["class_code"])
    op.create_index("ix_classrooms_id",                  "classrooms", ["id"],                 unique=True)
    op.create_index("ix_classrooms_class_code",          "classrooms", ["class_code"],         unique=True)
    op.create_index("ix_classrooms_class_type",          "classrooms", ["class_type"],         unique=False)
    op.create_index("ix_classrooms_academic_year",       "classrooms", ["academic_year"],      unique=False)
    op.create_index("ix_classrooms_grade_level",         "classrooms", ["grade_level"],        unique=False)
    op.create_index("ix_classrooms_homeroom_teacher_id", "classrooms", ["homeroom_teacher_id"],unique=False)
    op.create_index("ix_classrooms_is_active",           "classrooms", ["is_active"],          unique=False)

    # ── 3. student_class_enrollments ─────────────────────────────────────────
    op.create_table(
        "student_class_enrollments",
        sa.Column("id",          sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("student_id",  sa.Integer, sa.ForeignKey("students.id",   ondelete="CASCADE"),  nullable=False),
        sa.Column("classroom_id",sa.Integer, sa.ForeignKey("classrooms.id", ondelete="CASCADE"),  nullable=False),
        sa.Column(
            "enrollment_type",
            sa.Enum("primary", "supplementary", name="enrollmenttype", create_constraint=True),
            nullable=False,
            server_default="primary",
        ),
        sa.Column(
            "status",
            sa.Enum("active", "transferred", "withdrawn", "completed",
                    name="enrollmentstatus", create_constraint=True),
            nullable=False,
            server_default="active",
        ),
        sa.Column("enrolled_date", sa.Date,         nullable=False, server_default=sa.func.current_date()),
        sa.Column("left_date",     sa.Date,         nullable=True),
        sa.Column("notes",         sa.Unicode(300), nullable=True),
        sa.Column("is_active",   sa.Boolean,  nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime, nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("student_id", "classroom_id", "enrollment_type",
                            name="uq_enrollment_student_class_type"),
    )
    op.create_index("ix_enrollment_id",           "student_class_enrollments", ["id"],          unique=True)
    op.create_index("ix_enrollment_student_id",   "student_class_enrollments", ["student_id"],  unique=False)
    op.create_index("ix_enrollment_classroom_id", "student_class_enrollments", ["classroom_id"],unique=False)
    op.create_index("ix_enrollment_type",         "student_class_enrollments", ["enrollment_type"], unique=False)
    op.create_index("ix_enrollment_status",       "student_class_enrollments", ["status"],      unique=False)

    # ── 4. subjects ──────────────────────────────────────────────────────────
    op.create_table(
        "subjects",
        sa.Column("id",           sa.Integer,      primary_key=True, autoincrement=True),
        sa.Column("subject_code", sa.String(20),   nullable=False),
        sa.Column("subject_name", sa.Unicode(100), nullable=False),
        sa.Column(
            "subject_type",
            sa.Enum("standard", "cambridge", name="subjecttype", create_constraint=True),
            nullable=False,
            server_default="standard",
        ),
        sa.Column("credits",     sa.Integer,      nullable=False, server_default="1"),
        sa.Column("description", sa.Unicode(300), nullable=True),
        sa.Column("is_active",   sa.Boolean,  nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime, nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_unique_constraint("uq_subjects_subject_code", "subjects", ["subject_code"])
    op.create_index("ix_subjects_id",           "subjects", ["id"],           unique=True)
    op.create_index("ix_subjects_subject_code", "subjects", ["subject_code"], unique=True)
    op.create_index("ix_subjects_subject_type", "subjects", ["subject_type"], unique=False)

    # ── 5. class_subjects ────────────────────────────────────────────────────
    op.create_table(
        "class_subjects",
        sa.Column("id",           sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("classroom_id", sa.Integer, sa.ForeignKey("classrooms.id", ondelete="CASCADE"),  nullable=False),
        sa.Column("subject_id",   sa.Integer, sa.ForeignKey("subjects.id",   ondelete="NO ACTION"), nullable=False),
        sa.Column("teacher_id",   sa.Integer, sa.ForeignKey("teachers.id",   ondelete="NO ACTION"), nullable=True),
        sa.Column("semester",      sa.Integer,    nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("is_active",   sa.Boolean,  nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime, nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("classroom_id", "subject_id", "semester", "academic_year",
                            name="uq_class_subject_semester"),
    )
    op.create_index("ix_class_subjects_id",           "class_subjects", ["id"],           unique=True)
    op.create_index("ix_class_subjects_classroom_id", "class_subjects", ["classroom_id"], unique=False)
    op.create_index("ix_class_subjects_subject_id",   "class_subjects", ["subject_id"],   unique=False)
    op.create_index("ix_class_subjects_teacher_id",   "class_subjects", ["teacher_id"],   unique=False)
    op.create_index("ix_class_subjects_semester",     "class_subjects", ["semester"],     unique=False)
    op.create_index("ix_class_subjects_academic_year","class_subjects", ["academic_year"],unique=False)

    # ── 6. grade_components ──────────────────────────────────────────────────
    op.create_table(
        "grade_components",
        sa.Column("id",               sa.Integer,      primary_key=True, autoincrement=True),
        sa.Column("class_subject_id", sa.Integer,      sa.ForeignKey("class_subjects.id", ondelete="NO ACTION"), nullable=False),
        sa.Column("component_name",   sa.Unicode(100), nullable=False),
        sa.Column("weight_percent",   sa.Integer,      nullable=False),
        sa.Column("min_count",        sa.Integer,      nullable=False, server_default="1"),
        sa.Column("is_active",   sa.Boolean,  nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime, nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_grade_components_id",               "grade_components", ["id"],               unique=True)
    op.create_index("ix_grade_components_class_subject_id", "grade_components", ["class_subject_id"], unique=False)

    # ── 7. student_grades ────────────────────────────────────────────────────
    op.create_table(
        "student_grades",
        sa.Column("id",                 sa.Integer,    primary_key=True, autoincrement=True),
        sa.Column("student_id",         sa.Integer,    sa.ForeignKey("students.id",         ondelete="CASCADE"),   nullable=False),
        sa.Column("class_subject_id",   sa.Integer,    sa.ForeignKey("class_subjects.id",   ondelete="NO ACTION"), nullable=False),
        sa.Column("grade_component_id", sa.Integer,    sa.ForeignKey("grade_components.id", ondelete="NO ACTION"), nullable=False),
        sa.Column("score",              sa.Numeric(4, 2), nullable=False),
        sa.Column("exam_date",          sa.Date,       nullable=True),
        sa.Column("entered_by",         sa.Integer,    sa.ForeignKey("teachers.id",          ondelete="NO ACTION"), nullable=True),
        sa.Column("entered_at",         sa.DateTime,   nullable=False, server_default=sa.func.now()),
        sa.Column("last_modified_by",   sa.Integer,    sa.ForeignKey("teachers.id",          ondelete="NO ACTION"), nullable=True),
        sa.Column("last_modified_at",   sa.DateTime,   nullable=True),
        sa.Column("is_active",   sa.Boolean,  nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime, nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_student_grades_id",                 "student_grades", ["id"],                 unique=True)
    op.create_index("ix_student_grades_student_id",         "student_grades", ["student_id"],         unique=False)
    op.create_index("ix_student_grades_class_subject_id",   "student_grades", ["class_subject_id"],   unique=False)
    op.create_index("ix_student_grades_grade_component_id", "student_grades", ["grade_component_id"], unique=False)
    op.create_index("ix_student_grades_entered_by",         "student_grades", ["entered_by"],         unique=False)

    # ── 8. grade_audit_log ───────────────────────────────────────────────────
    op.create_table(
        "grade_audit_log",
        sa.Column("id",               sa.Integer,      primary_key=True, autoincrement=True),
        sa.Column("student_grade_id", sa.Integer,      sa.ForeignKey("student_grades.id", ondelete="CASCADE"),   nullable=False),
        sa.Column("old_score",        sa.Numeric(4, 2), nullable=False),
        sa.Column("new_score",        sa.Numeric(4, 2), nullable=False),
        sa.Column("changed_by",       sa.Integer,      sa.ForeignKey("teachers.id",       ondelete="NO ACTION"), nullable=True),
        sa.Column("changed_at",       sa.DateTime,     nullable=False, server_default=sa.func.now()),
        sa.Column("reason",           sa.Unicode(300), nullable=False),
    )
    op.create_index("ix_grade_audit_log_id",               "grade_audit_log", ["id"],               unique=True)
    op.create_index("ix_grade_audit_log_student_grade_id", "grade_audit_log", ["student_grade_id"], unique=False)
    op.create_index("ix_grade_audit_log_changed_by",       "grade_audit_log", ["changed_by"],       unique=False)

    # ── 9. semester_averages ─────────────────────────────────────────────────
    op.create_table(
        "semester_averages",
        sa.Column("id",               sa.Integer,    primary_key=True, autoincrement=True),
        sa.Column("student_id",       sa.Integer,    sa.ForeignKey("students.id",       ondelete="CASCADE"),   nullable=False),
        sa.Column("class_subject_id", sa.Integer,    sa.ForeignKey("class_subjects.id", ondelete="NO ACTION"), nullable=False),
        sa.Column("semester",         sa.Integer,    nullable=False),
        sa.Column("academic_year",    sa.String(10), nullable=False),
        sa.Column("average_score",    sa.Numeric(4, 2), nullable=False, server_default="0"),
        sa.Column(
            "rank",
            sa.Enum("Gioi", "Kha", "Trung binh", "Yeu", name="academicrank", create_constraint=True),
            nullable=False,
            server_default="Yeu",
        ),
        sa.Column("calculated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "class_subject_id", name="uq_semester_avg_student_subject"),
    )
    op.create_index("ix_semester_averages_id",               "semester_averages", ["id"],               unique=True)
    op.create_index("ix_semester_averages_student_id",       "semester_averages", ["student_id"],       unique=False)
    op.create_index("ix_semester_averages_class_subject_id", "semester_averages", ["class_subject_id"], unique=False)

    # ── 10. salary_grades ────────────────────────────────────────────────────
    op.create_table(
        "salary_grades",
        sa.Column("id",         sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("grade_code", sa.String(30), nullable=False),
        sa.Column(
            "qualification_level",
            sa.Enum("cao_dang", "dai_hoc", "thac_si", "tien_si",
                    name="qualificationlevel", create_constraint=True),
            nullable=False,
        ),
        sa.Column(
            "experience_tier",
            sa.Enum("under_3y", "3_to_6y", "6_to_9y", "over_9y",
                    name="experiencetier", create_constraint=True),
            nullable=False,
        ),
        sa.Column("base_salary",    sa.Numeric(15, 2), nullable=False),
        sa.Column("hourly_rate",    sa.Numeric(10, 2), nullable=False),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to",   sa.Date, nullable=True),
        sa.Column("description",    sa.Unicode(300), nullable=True),
        sa.Column("is_active",   sa.Boolean,  nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime, nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("qualification_level", "experience_tier", "effective_from",
                            name="uq_salary_grade_combo"),
    )
    op.create_unique_constraint("uq_salary_grades_grade_code", "salary_grades", ["grade_code"])
    op.create_index("ix_salary_grades_id",                  "salary_grades", ["id"],                  unique=True)
    op.create_index("ix_salary_grades_grade_code",          "salary_grades", ["grade_code"],          unique=True)
    op.create_index("ix_salary_grades_qualification_level", "salary_grades", ["qualification_level"], unique=False)
    op.create_index("ix_salary_grades_experience_tier",     "salary_grades", ["experience_tier"],     unique=False)

    # ── 11. bonus_policies ───────────────────────────────────────────────────
    op.create_table(
        "bonus_policies",
        sa.Column("id",          sa.Integer,      primary_key=True, autoincrement=True),
        sa.Column("policy_code", sa.String(30),   nullable=False),
        sa.Column("policy_name", sa.Unicode(200), nullable=False),
        sa.Column(
            "bonus_type",
            sa.Enum("fixed", "percentage", name="bonustype", create_constraint=True),
            nullable=False,
            server_default="fixed",
        ),
        sa.Column("bonus_value",           sa.Numeric(15, 2), nullable=False),
        sa.Column("condition_description", sa.Unicode(500),   nullable=True),
        sa.Column("is_active",   sa.Boolean,  nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime, nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_unique_constraint("uq_bonus_policies_policy_code", "bonus_policies", ["policy_code"])
    op.create_index("ix_bonus_policies_id",          "bonus_policies", ["id"],          unique=True)
    op.create_index("ix_bonus_policies_policy_code", "bonus_policies", ["policy_code"], unique=True)

    # ── 12. monthly_payroll ──────────────────────────────────────────────────
    op.create_table(
        "monthly_payroll",
        sa.Column("id",              sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("teacher_id",      sa.Integer, sa.ForeignKey("teachers.id",      ondelete="NO ACTION"), nullable=False),
        sa.Column("salary_grade_id", sa.Integer, sa.ForeignKey("salary_grades.id", ondelete="NO ACTION"), nullable=False),
        sa.Column("payroll_month",   sa.Date,    nullable=False),
        sa.Column("work_days_standard",      sa.Integer,        nullable=False, server_default="22"),
        sa.Column("work_days_actual",        sa.Integer,        nullable=False, server_default="0"),
        sa.Column("teaching_hours_standard", sa.Integer,        nullable=False, server_default="0"),
        sa.Column("teaching_hours_actual",   sa.Integer,        nullable=False, server_default="0"),
        sa.Column("base_salary",        sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("teaching_allowance", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("total_bonus",        sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("deductions",         sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("net_salary",         sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum("draft", "confirmed", "paid", name="payrollstatus", create_constraint=True),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("confirmed_by", sa.Integer, sa.ForeignKey("teachers.id", ondelete="NO ACTION"), nullable=True),
        sa.Column("confirmed_at", sa.DateTime, nullable=True),
        sa.Column("paid_at",      sa.DateTime, nullable=True),
        sa.Column("notes",        sa.Unicode(500), nullable=True),
        sa.Column("created_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime, nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("teacher_id", "payroll_month", name="uq_payroll_teacher_month"),
    )
    op.create_index("ix_monthly_payroll_id",             "monthly_payroll", ["id"],             unique=True)
    op.create_index("ix_monthly_payroll_teacher_id",     "monthly_payroll", ["teacher_id"],     unique=False)
    op.create_index("ix_monthly_payroll_salary_grade_id","monthly_payroll", ["salary_grade_id"],unique=False)
    op.create_index("ix_monthly_payroll_payroll_month",  "monthly_payroll", ["payroll_month"],  unique=False)
    op.create_index("ix_monthly_payroll_status",         "monthly_payroll", ["status"],         unique=False)

    # ── 13. payroll_bonus_details ────────────────────────────────────────────
    op.create_table(
        "payroll_bonus_details",
        sa.Column("id",              sa.Integer,      primary_key=True, autoincrement=True),
        sa.Column("payroll_id",      sa.Integer,      sa.ForeignKey("monthly_payroll.id",  ondelete="CASCADE"),   nullable=False),
        sa.Column("bonus_policy_id", sa.Integer,      sa.ForeignKey("bonus_policies.id",   ondelete="NO ACTION"), nullable=False),
        sa.Column("amount",          sa.Numeric(15, 2), nullable=False),
        sa.Column("note",            sa.Unicode(300), nullable=True),
        sa.Column("created_at",  sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_payroll_bonus_details_id",              "payroll_bonus_details", ["id"],              unique=True)
    op.create_index("ix_payroll_bonus_details_payroll_id",      "payroll_bonus_details", ["payroll_id"],      unique=False)
    op.create_index("ix_payroll_bonus_details_bonus_policy_id", "payroll_bonus_details", ["bonus_policy_id"], unique=False)


def downgrade() -> None:
    # Drop in reverse FK dependency order

    # 13
    op.drop_index("ix_payroll_bonus_details_bonus_policy_id", table_name="payroll_bonus_details")
    op.drop_index("ix_payroll_bonus_details_payroll_id",      table_name="payroll_bonus_details")
    op.drop_index("ix_payroll_bonus_details_id",              table_name="payroll_bonus_details")
    op.drop_table("payroll_bonus_details")

    # 12
    op.drop_index("ix_monthly_payroll_status",          table_name="monthly_payroll")
    op.drop_index("ix_monthly_payroll_payroll_month",   table_name="monthly_payroll")
    op.drop_index("ix_monthly_payroll_salary_grade_id", table_name="monthly_payroll")
    op.drop_index("ix_monthly_payroll_teacher_id",      table_name="monthly_payroll")
    op.drop_index("ix_monthly_payroll_id",              table_name="monthly_payroll")
    op.drop_table("monthly_payroll")

    # 11
    op.drop_index("ix_bonus_policies_policy_code", table_name="bonus_policies")
    op.drop_index("ix_bonus_policies_id",          table_name="bonus_policies")
    op.drop_constraint("uq_bonus_policies_policy_code", "bonus_policies", type_="unique")
    op.drop_table("bonus_policies")

    # 10
    op.drop_index("ix_salary_grades_experience_tier",     table_name="salary_grades")
    op.drop_index("ix_salary_grades_qualification_level", table_name="salary_grades")
    op.drop_index("ix_salary_grades_grade_code",          table_name="salary_grades")
    op.drop_index("ix_salary_grades_id",                  table_name="salary_grades")
    op.drop_constraint("uq_salary_grades_grade_code", "salary_grades", type_="unique")
    op.drop_table("salary_grades")

    # 9
    op.drop_index("ix_semester_averages_class_subject_id", table_name="semester_averages")
    op.drop_index("ix_semester_averages_student_id",       table_name="semester_averages")
    op.drop_index("ix_semester_averages_id",               table_name="semester_averages")
    op.drop_table("semester_averages")

    # 8
    op.drop_index("ix_grade_audit_log_changed_by",       table_name="grade_audit_log")
    op.drop_index("ix_grade_audit_log_student_grade_id", table_name="grade_audit_log")
    op.drop_index("ix_grade_audit_log_id",               table_name="grade_audit_log")
    op.drop_table("grade_audit_log")

    # 7
    op.drop_index("ix_student_grades_entered_by",         table_name="student_grades")
    op.drop_index("ix_student_grades_grade_component_id", table_name="student_grades")
    op.drop_index("ix_student_grades_class_subject_id",   table_name="student_grades")
    op.drop_index("ix_student_grades_student_id",         table_name="student_grades")
    op.drop_index("ix_student_grades_id",                 table_name="student_grades")
    op.drop_table("student_grades")

    # 6
    op.drop_index("ix_grade_components_class_subject_id", table_name="grade_components")
    op.drop_index("ix_grade_components_id",               table_name="grade_components")
    op.drop_table("grade_components")

    # 5
    op.drop_index("ix_class_subjects_academic_year", table_name="class_subjects")
    op.drop_index("ix_class_subjects_semester",      table_name="class_subjects")
    op.drop_index("ix_class_subjects_teacher_id",    table_name="class_subjects")
    op.drop_index("ix_class_subjects_subject_id",    table_name="class_subjects")
    op.drop_index("ix_class_subjects_classroom_id",  table_name="class_subjects")
    op.drop_index("ix_class_subjects_id",            table_name="class_subjects")
    op.drop_table("class_subjects")

    # 4
    op.drop_index("ix_subjects_subject_type", table_name="subjects")
    op.drop_index("ix_subjects_subject_code", table_name="subjects")
    op.drop_index("ix_subjects_id",           table_name="subjects")
    op.drop_constraint("uq_subjects_subject_code", "subjects", type_="unique")
    op.drop_table("subjects")

    # 3
    op.drop_index("ix_enrollment_status",       table_name="student_class_enrollments")
    op.drop_index("ix_enrollment_type",         table_name="student_class_enrollments")
    op.drop_index("ix_enrollment_classroom_id", table_name="student_class_enrollments")
    op.drop_index("ix_enrollment_student_id",   table_name="student_class_enrollments")
    op.drop_index("ix_enrollment_id",           table_name="student_class_enrollments")
    op.drop_table("student_class_enrollments")

    # 2
    op.drop_index("ix_classrooms_is_active",           table_name="classrooms")
    op.drop_index("ix_classrooms_homeroom_teacher_id", table_name="classrooms")
    op.drop_index("ix_classrooms_grade_level",         table_name="classrooms")
    op.drop_index("ix_classrooms_academic_year",       table_name="classrooms")
    op.drop_index("ix_classrooms_class_type",          table_name="classrooms")
    op.drop_index("ix_classrooms_class_code",          table_name="classrooms")
    op.drop_index("ix_classrooms_id",                  table_name="classrooms")
    op.drop_constraint("uq_classrooms_class_code", "classrooms", type_="unique")
    op.drop_table("classrooms")

    # 1
    op.drop_index("ix_teachers_is_active",         table_name="teachers")
    op.drop_index("ix_teachers_department",        table_name="teachers")
    op.drop_index("ix_teachers_employment_status", table_name="teachers")
    op.drop_index("ix_teachers_email",             table_name="teachers")
    op.drop_index("ix_teachers_national_id",       table_name="teachers")
    op.drop_index("ix_teachers_teacher_code",      table_name="teachers")
    op.drop_index("ix_teachers_id",                table_name="teachers")
    op.drop_constraint("uq_teachers_email",       "teachers", type_="unique")
    op.drop_constraint("uq_teachers_national_id", "teachers", type_="unique")
    op.drop_constraint("uq_teachers_teacher_code","teachers", type_="unique")
    op.drop_table("teachers")

    # Drop enum types
    for enum_name in (
        "teacherstatus", "classtype", "enrollmenttype", "enrollmentstatus",
        "subjecttype", "academicrank", "qualificationlevel", "experiencetier",
        "bonustype", "payrollstatus",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
