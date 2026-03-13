"""Add composite index for tasks pagination with created_at ordering

Revision ID: 20260312_000004
Revises: 20260312_000002
Create Date: 2026-03-12 00:00:04

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260312_000004"
down_revision = "20260312_000002"
branch_labels = None
depends_on = None


def upgrade():
    # Add composite index to optimize task list pagination with ORDER BY created_at DESC
    # This covers the common query: WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?
    op.create_index(
        op.f("ix_tasks_user_created"),
        "tasks",
        ["user_id", "created_at DESC"],
    )


def downgrade():
    # Drop the index
    op.drop_index(op.f("ix_tasks_user_created"), table_name="tasks")
