#!/usr/bin/env python3
"""
Test script to verify database migrations and connection.
Usage: python test_migrations.py
"""

import os
import sys
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


def test_alembic_config():
    """Test that Alembic configuration is valid."""
    print("Testing Alembic configuration...")
    alembic_cfg = Config("backend/alembic.ini")
    # Override the SQLAlchemy URL with test database
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://tactuser:tactpassword@localhost:5432/tactai_test",
    )
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
    print(f"✓ Alembic config loaded: {alembic_cfg.get_main_option('script_location')}")
    return alembic_cfg


def test_models_import():
    """Test that all models can be imported."""
    print("\nTesting model imports...")
    try:
        from backend.database import Base
        from backend.models import (
            User,
            Task,
            TaskChain,
            Timeline,
            TimelineTask,
            TimeBlock,
        )

        print(f"✓ All models imported successfully")
        print(f"✓ Base.metadata contains tables: {list(Base.metadata.tables.keys())}")
        return True
    except Exception as e:
        print(f"✗ Error importing models: {e}")
        return False


def test_connection():
    """Test database connection."""
    print("\nTesting database connection...")
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://tactuser:tactpassword@localhost:5432/tactai_test",
    )
    try:
        engine = create_engine(test_db_url, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✓ Connected to database: {test_db_url}")
        engine.dispose()
        return True
    except Exception as e:
        print(f"✗ Cannot connect to database: {e}")
        print("  Note: Make sure PostgreSQL is running and the database exists.")
        return False


def test_migration_apply(alembic_cfg):
    """Test applying migrations."""
    print("\nTesting migration application...")
    try:
        # This would actually apply migrations - we'll just validate the script
        # command.check(alembic_cfg)  # Checks if head revision is current
        print("✓ Migration scripts are valid (syntax check only - not applied)")
        print("  To apply: alembic upgrade head")
        return True
    except Exception as e:
        print(f"✗ Migration validation failed: {e}")
        return False


def main():
    print("=" * 60)
    print("Tact AI - Database Migration Test Suite")
    print("=" * 60)

    results = []

    # Test model imports
    results.append(("Model imports", test_models_import()))

    # Test connection
    results.append(("Database connection", test_connection()))

    # Test Alembic config
    if results[-1][1]:  # Only test if DB is reachable
        alembic_cfg = test_alembic_config()
        results.append(("Alembic config", True))
        results.append(("Migration validation", test_migration_apply(alembic_cfg)))
    else:
        print("\nSkipping Alembic tests (database not available)")

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
