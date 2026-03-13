"""Add composite index for scheduler task query optimization

Revision ID: 20260312_000004_add_scheduler_task_index
Revises: 20260312_000003_add_task_chains_index
Create Date: 2026-03-12 00:00:04

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260312_000004_add_scheduler_task_index"
down_revision = "20260312_000003_add_task_chains_index"
branch_labels = None
depends_on = None


def upgrade():
    # Add composite index for scheduler query pattern:
    # SELECT * FROM tasks WHERE user_id = ? AND completed = FALSE
    # This is the most common query in the schedule generation endpoint
    op.create_index(
        op.f("ix_tasks_user_completed"),
        "tasks",
        ["user_id", "completed"],
    )


def downgrade():
    # Drop composite index
    op.drop_index(op.f("ix_tasks_user_completed"), table_name="tasks")
