"""Initial schema creation

Revision ID: 20260312_000001
Revises:
Create Date: 2026-03-12 00:00:01

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260312_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types first
    quadrant_enum = postgresql.ENUM(
        "Q1", "Q2", "Q3", "Q4", name="quadrant_enum", create_type=True
    )
    priority_enum = postgresql.ENUM(
        "low", "medium", "high", "critical", name="priority_enum", create_type=True
    )
    relationship_type_enum = postgresql.ENUM(
        "depends_on",
        "blocks",
        "relates_to",
        name="relationship_type_enum",
        create_type=True,
    )
    day_of_week_enum = postgresql.ENUM(
        0, 1, 2, 3, 4, 5, 6, name="day_of_week_enum", create_type=True
    )

    quadrant_enum.create(op.get_bind(), checkfirst=True)
    priority_enum.create(op.get_bind(), checkfirst=True)
    relationship_type_enum.create(op.get_bind(), checkfirst=True)
    day_of_week_enum.create(op.get_bind(), checkfirst=True)

     # Create users table
     op.create_table(
         "users",
         sa.Column("id", sa.Integer, primary_key=True, index=True),
         sa.Column("email", sa.String, unique=True, index=True, nullable=False),
         sa.Column("username", sa.String, nullable=True),
         sa.Column("hashed_password", sa.String, nullable=False),
         sa.Column("is_active", sa.Boolean, default=True, nullable=False),
         sa.Column(
             "created_at",
             sa.DateTime(timezone=True),
             server_default=sa.text("NOW()"),
             nullable=False,
         ),
         sa.Column(
             "updated_at",
             sa.DateTime(timezone=True),
             onupdate=sa.text("NOW()"),
             nullable=True,
         ),
     )

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("quadrant", quadrant_enum, nullable=False),
        sa.Column("priority", priority_enum, default="medium", nullable=False),
        sa.Column("estimated_duration", sa.Integer, nullable=True),  # in minutes
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed", sa.Boolean, default=False, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            onupdate=sa.text("NOW()"),
            nullable=True,
        ),
    )

    # Create task_chains table
    op.create_table(
        "task_chains",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "task_id",
            sa.Integer,
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "prerequisite_task_id",
            sa.Integer,
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "relationship_type",
            relationship_type_enum,
            default="depends_on",
            nullable=False,
        ),
    )

    # Create timelines table
    op.create_table(
        "timelines",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "schedule_data", sa.Text, nullable=True
        ),  # JSON string with full schedule
    )

    # Create timeline_tasks table
    op.create_table(
        "timeline_tasks",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "timeline_id",
            sa.Integer,
            sa.ForeignKey("timelines.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            sa.Integer,
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    # Create time_blocks table
    op.create_table(
        "time_blocks",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "day_of_week", day_of_week_enum, nullable=False
        ),  # 0=Monday, 6=Sunday
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
    )

    # Create indexes for better performance
    op.create_index(op.f("ix_tasks_user_id"), "tasks", ["user_id"])
    op.create_index(op.f("ix_tasks_due_date"), "tasks", ["due_date"])
    op.create_index(op.f("ix_tasks_completed"), "tasks", ["completed"])
    op.create_index(op.f("ix_tasks_quadrant"), "tasks", ["quadrant"])
    op.create_index(op.f("ix_tasks_priority"), "tasks", ["priority"])
    op.create_index(op.f("ix_task_chains_task_id"), "task_chains", ["task_id"])
    op.create_index(
        op.f("ix_task_chains_prerequisite_task_id"),
        "task_chains",
        ["prerequisite_task_id"],
    )
    op.create_index(op.f("ix_timelines_user_id"), "timelines", ["user_id"])
    op.create_index(op.f("ix_timelines_start_date"), "timelines", ["start_date"])
    op.create_index(op.f("ix_timelines_end_date"), "timelines", ["end_date"])
    op.create_index(
        op.f("ix_timeline_tasks_timeline_id"), "timeline_tasks", ["timeline_id"]
    )
    op.create_index(op.f("ix_timeline_tasks_task_id"), "timeline_tasks", ["task_id"])
    op.create_index(
        op.f("ix_timeline_tasks_scheduled_start"), "timeline_tasks", ["scheduled_start"]
    )
    op.create_index(op.f("ix_time_blocks_user_id"), "time_blocks", ["user_id"])
    op.create_index(op.f("ix_time_blocks_day_of_week"), "time_blocks", ["day_of_week"])

    # Create unique constraint on timeline_tasks (timeline_id, task_id)
    op.create_unique_constraint(
        "uq_timeline_task", "timeline_tasks", ["timeline_id", "task_id"]
    )


def downgrade():
    # Drop indexes first
    op.drop_index(op.f("ix_time_blocks_day_of_week"), table_name="time_blocks")
    op.drop_index(op.f("ix_time_blocks_user_id"), table_name="time_blocks")
    op.drop_index(
        op.f("ix_timeline_tasks_scheduled_start"), table_name="timeline_tasks"
    )
    op.drop_index(op.f("ix_timeline_tasks_task_id"), table_name="timeline_tasks")
    op.drop_index(op.f("ix_timeline_tasks_timeline_id"), table_name="timeline_tasks")
    op.drop_index(op.f("ix_timelines_end_date"), table_name="timelines")
    op.drop_index(op.f("ix_timelines_start_date"), table_name="timelines")
    op.drop_index(op.f("ix_timelines_user_id"), table_name="timelines")
    op.drop_index(op.f("ix_task_chains_prerequisite_task_id"), table_name="task_chains")
    op.drop_index(op.f("ix_task_chains_task_id"), table_name="task_chains")
    op.drop_index(op.f("ix_tasks_priority"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_quadrant"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_completed"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_due_date"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_user_id"), table_name="tasks")

    # Drop constraints
    op.drop_constraint("uq_timeline_task", "timeline_tasks", type_="unique")

    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table("time_blocks")
    op.drop_table("timeline_tasks")
    op.drop_table("timelines")
    op.drop_table("task_chains")
    op.drop_table("tasks")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS day_of_week_enum")
    op.execute("DROP TYPE IF EXISTS relationship_type_enum")
    op.execute("DROP TYPE IF EXISTS priority_enum")
    op.execute("DROP TYPE IF EXISTS quadrant_enum")
