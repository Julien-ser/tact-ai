"""Add composite indexes for optimized query performance

Revision ID: 20260312_000002
Revises: 20260312_000001
Create Date: 2026-03-12 00:00:02

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260312_000002"
down_revision = "20260312_000001"
branch_labels = None
depends_on = None


def upgrade():
    # Add composite indexes for task queries with user_id filters
    # These indexes optimize the common pattern: WHERE user_id = ? AND [column] = ?
    op.create_index(op.f("ix_tasks_user_completed"), "tasks", ["user_id", "completed"])
    op.create_index(op.f("ix_tasks_user_priority"), "tasks", ["user_id", "priority"])
    op.create_index(op.f("ix_tasks_user_quadrant"), "tasks", ["user_id", "quadrant"])
    op.create_index(op.f("ix_tasks_user_due_date"), "tasks", ["user_id", "due_date"])

    # Improve timeline index for common query pattern
    op.drop_index(op.f("ix_timelines_user_id"), table_name="timelines")
    op.create_index(
        op.f("ix_timelines_user_generated"),
        "timelines",
        ["user_id", "generated_at DESC"],
    )

    # Improve time_blocks index for user-specific day lookups
    op.drop_index(op.f("ix_time_blocks_user_id"), table_name="time_blocks")
    op.drop_index(op.f("ix_time_blocks_day_of_week"), table_name="time_blocks")
    op.create_index(
        op.f("ix_time_blocks_user_day"), "time_blocks", ["user_id", "day_of_week"]
    )


def downgrade():
    # Drop composite indexes
    op.drop_index(op.f("ix_tasks_user_completed"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_user_priority"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_user_quadrant"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_user_due_date"), table_name="tasks")

    # Restore original timeline indexes
    op.drop_index(op.f("ix_timelines_user_generated"), table_name="timelines")
    op.create_index(op.f("ix_timelines_user_id"), "timelines", ["user_id"])
    op.create_index(op.f("ix_timelines_start_date"), "timelines", ["start_date"])
    op.create_index(op.f("ix_timelines_end_date"), "timelines", ["end_date"])

    # Restore original time_blocks indexes
    op.drop_index(op.f("ix_time_blocks_user_day"), table_name="time_blocks")
    op.create_index(op.f("ix_time_blocks_user_id"), "time_blocks", ["user_id"])
    op.create_index(op.f("ix_time_blocks_day_of_week"), "time_blocks", ["day_of_week"])
