#!/usr/bin/env python3
"""
Setup script for load testing.
Creates test users and tasks in the database.
"""

import asyncio
import sys
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import secrets

# Add backend to path
sys.path.insert(0, "/home/julien/Desktop/Free-Wiggum-opencode/projects/tact-ai/backend")

from config import settings
from models.user import User as UserModel
from models.task import Task as TaskModel
from models.task_chain import TaskChain as TaskChainModel, RelationshipTypeEnum
from database import Base


def create_test_data(num_users: int = 200, tasks_per_user: int = 50):
    """Create test users and tasks for load testing."""

    # Connect to database
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    db = SessionLocal()

    try:
        print(f"Creating {num_users} test users...")

        created_users = 0
        for i in range(1, num_users + 1):
            username = f"loadtest{i}"
            email = f"loadtest{i}@example.com"

            # Check if user already exists
            existing = db.query(UserModel).filter_by(email=email).first()
            if existing:
                print(f"  User {username} already exists, skipping...")
                continue

            # Create user
            from auth.utils import get_password_hash

            user = UserModel(
                email=email,
                username=username,
                hashed_password=get_password_hash("testpassword123"),
                is_active=True,
            )
            db.add(user)
            created_users += 1

            # Commit every 50 users to avoid large transactions
            if created_users % 50 == 0:
                db.commit()
                print(f"  Created {created_users} users so far...")

        db.commit()
        print(f"✓ Created {created_users} new users")

        # Create tasks for each user
        print(f"\nCreating {tasks_per_user} tasks per user...")

        total_tasks = 0
        users = (
            db.query(UserModel)
            .filter(UserModel.email.like("loadtest%@example.com"))
            .all()
        )

        task_templates = [
            "Complete project proposal",
            "Team meeting",
            "Review pull requests",
            "Write documentation",
            "Bug fix: login issue",
            "Client call",
            "Update dependencies",
            "Code review",
            "Plan sprint",
            "Training session",
            "Deploy to production",
            "Monitoring setup",
            "Security audit",
            "Performance optimization",
            "Database backup",
            "Code refactoring",
            "Feature development",
            "Testing and QA",
            "Stakeholder update",
            "Documentation review",
        ]

        priorities = ["low", "medium", "high", "critical"]
        quadrants = ["Q1", "Q2", "Q3", "Q4"]

        for user_idx, user in enumerate(users):
            user_tasks = []

            # Create tasks for this user
            for task_idx in range(tasks_per_user):
                title_idx = (user_idx * tasks_per_user + task_idx) % len(task_templates)
                priority_idx = (user_idx + task_idx) % len(priorities)
                quadrant_idx = (user_idx + task_idx) % len(quadrants)

                due_date = datetime.utcnow() + timedelta(
                    days=random.randint(1, 30), hours=random.randint(0, 23)
                )

                task = TaskModel(
                    user_id=user.id,
                    title=f"{task_templates[title_idx]} #{task_idx + 1}",
                    description=f"Auto-generated test task for load testing",
                    estimated_duration=random.randint(30, 180),
                    priority=priorities[priority_idx],
                    quadrant=quadrants[quadrant_idx],
                    due_date=due_date,
                    completed=False,
                )
                db.add(task)
                user_tasks.append(task)

            # Commit tasks for this user
            db.flush()

            # Create task dependencies for first few tasks (about 20% have dependencies)
            if user_idx < num_users // 2:  # For half the users
                num_deps = random.randint(3, min(10, tasks_per_user // 2))
                for _ in range(num_deps):
                    from_task = random.choice(
                        user_tasks[5:]
                    )  # Don't depend on first few
                    to_task = random.choice(user_tasks[:10])  # Depend on early tasks
                    if from_task.id != to_task.id:
                        chain = TaskChainModel(
                            task_id=from_task.id,
                            prerequisite_task_id=to_task.id,
                            relationship_type=RelationshipTypeEnum.DEPENDS_ON,
                        )
                        db.add(chain)

            total_tasks += len(user_tasks)

            if (user_idx + 1) % 20 == 0:
                db.commit()
                print(f"  Created tasks for {user_idx + 1}/{len(users)} users...")

        db.commit()
        print(f"✓ Created {total_tasks} tasks")

        # Verify counts
        total_users = db.query(UserModel).count()
        total_tasks_db = db.query(TaskModel).count()
        print(f"\nDatabase Summary:")
        print(f"  Total users: {total_users}")
        print(f"  Total tasks: {total_tasks_db}")

        print("\n✓ Test data setup complete!")

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import os

    # Check environment
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL environment variable not set")
        print("Make sure docker-compose is running: docker-compose up -d postgres")
        sys.exit(1)

    # Override settings to use env var
    settings.DATABASE_URL = os.getenv("DATABASE_URL")

    try:
        create_test_data()
        print("\nNext steps:")
        print("  1. Run load test: k6 run load-tests/load-test.js")
        print("  2. Monitor results in k6 output")
        print("  3. Check load-tests/README.md for troubleshooting")
    except Exception as e:
        print(f"\nSetup failed: {e}")
        sys.exit(1)
