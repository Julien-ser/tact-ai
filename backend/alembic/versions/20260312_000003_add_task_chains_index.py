"""Add composite index for task_chains query optimization

Revision ID: 20260312_000003
Revises: 20260312_000002
Create Date: 2026-03-12 00:00:03

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260312_000003"
down_revision = "20260312_000002"
branch_labels = None
depends_on = None


def upgrade():
    # Add composite index for task_chains queries that filter by task_id and relationship_type
    # This optimizes the common query pattern in scheduler: WHERE task_id IN ? AND relationship_type = ?
    op.create_index(
        op.f("ix_task_chains_task_relationship"),
        "task_chains",
        ["task_id", "relationship_type"],
    )


def downgrade():
    # Drop composite index
    op.drop_index(op.f("ix_task_chains_task_relationship"), table_name="task_chains")
