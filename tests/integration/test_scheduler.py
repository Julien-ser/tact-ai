"""
Integration tests for Scheduler Router
Tests schedule generation, history retrieval, and conflict detection.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, time

from backend.database import Base, get_db
from backend.main import app
from backend.models.user import User as UserModel
from backend.models.task import Task as TaskModel
from backend.models.time_block import TimeBlock as TimeBlockModel
from backend.auth.utils import get_password_hash, create_access_token

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create a test client with overridden database dependency"""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_with_data(test_db):
    """
    Create a test user with tasks and time blocks.
    Returns the user and auth headers.
    """
    # Create user
    user = UserModel(
        email="scheduler@example.com",
        username="scheduleruser",
        hashed_password=get_password_hash("schedulerpass123"),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Create some tasks
    tasks = [
        TaskModel(
            user_id=user.id,
            title="Task 1",
            description="First task",
            quadrant="q1",
            priority="high",
            estimated_duration=60,
            due_date=datetime.now() + timedelta(days=3),
        ),
        TaskModel(
            user_id=user.id,
            title="Task 2",
            description="Second task with dependency",
            quadrant="q2",
            priority="medium",
            estimated_duration=45,
        ),
        TaskModel(
            user_id=user.id,
            title="Task 3",
            description="Third task",
            quadrant="q1",
            priority="high",
            estimated_duration=90,
        ),
    ]
    for task in tasks:
        test_db.add(task)
    test_db.commit()

    # Create time blocks (working hours)
    time_blocks = [
        TimeBlockModel(
            user_id=user.id,
            day_of_week=1,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0),
        ),
        TimeBlockModel(
            user_id=user.id,
            day_of_week=2,  # Tuesday
            start_time=time(9, 0),
            end_time=time(17, 0),
        ),
        TimeBlockModel(
            user_id=user.id,
            day_of_week=3,  # Wednesday
            start_time=time(9, 0),
            end_time=time(17, 0),
        ),
    ]
    for tb in time_blocks:
        test_db.add(tb)
    test_db.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    return user, headers


class TestSchedulerIntegration:
    """Integration tests for scheduler endpoints"""

    def test_generate_schedule_success(self, client, test_user_with_data):
        """Test generating a schedule with available tasks"""
        user, headers = test_user_with_data

        response = client.post("/scheduler/generate", headers=headers)

        # Should succeed even if optimal schedule cannot be found
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "timeline_id" in data
            assert "tasks" in data
            assert "conflicts" in data
            assert "stats" in data
            assert data["stats"]["total_tasks"] >= 0
            # Tasks should be scheduled within the time horizon
            for task in data["tasks"]:
                assert "task_id" in task
                assert "start" in task
                assert "end" in task
                assert task["end"] > task["start"]

    def test_generate_schedule_with_custom_dates(self, client, test_user_with_data):
        """Test generating schedule with custom start and end dates"""
        user, headers = test_user_with_data

        start_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=5)

        response = client.post(
            "/scheduler/generate",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=headers,
        )

        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            # Schedule should respect the date range
            returned_start = datetime.fromisoformat(data["start_date"])
            returned_end = datetime.fromisoformat(data["end_date"])
            # Allow some tolerance but should be close to requested range
            assert abs((returned_start - start_date).total_seconds()) < 3600  # 1 hour

    def test_generate_schedule_no_tasks(self, client, test_user_with_data, test_db):
        """Test schedule generation fails when user has no incomplete tasks"""
        user, headers = test_user_with_data

        # Delete all tasks for the user
        test_db.query(TaskModel).filter(TaskModel.user_id == user.id).delete()
        test_db.commit()

        response = client.post("/scheduler/generate", headers=headers)

        assert response.status_code == 400
        assert "No incomplete tasks" in response.json()["detail"]

    def test_generate_schedule_creates_timeline(self, client, test_user_with_data):
        """Test that generating a schedule creates a timeline record"""
        user, headers = test_user_with_data

        response = client.post("/scheduler/generate", headers=headers)
        assert response.status_code == 200
        data = response.json()

        timeline_id = data["timeline_id"]
        assert timeline_id is not None

        # Retrieve the timeline via history or direct get
        history_response = client.get("/scheduler/history", headers=headers)
        assert history_response.status_code == 200
        history = history_response.json()

        # The generated timeline should appear in history
        timeline_ids = [t["id"] for t in history]
        assert timeline_id in timeline_ids

    def test_get_schedule_history(self, client, test_user_with_data):
        """Test retrieving user's schedule history"""
        user, headers = test_user_with_data

        # Generate multiple schedules
        for _ in range(3):
            client.post("/scheduler/generate", headers=headers)

        response = client.get("/scheduler/history", headers=headers)

        assert response.status_code == 200
        history = response.json()
        assert len(history) >= 1
        # Each entry should have required fields
        for entry in history:
            assert "id" in entry
            assert "name" in entry
            assert "start_date" in entry
            assert "end_date" in entry
            assert "generated_at" in entry
            assert "task_count" in entry

    def test_get_schedule_history_with_limit(self, client, test_user_with_data):
        """Test schedule history respects limit parameter"""
        user, headers = test_user_with_data

        # Generate multiple schedules
        for _ in range(5):
            client.post("/scheduler/generate", headers=headers)

        response = client.get("/scheduler/history?limit=2", headers=headers)

        assert response.status_code == 200
        history = response.json()
        assert len(history) <= 2

    def test_get_specific_schedule(self, client, test_user_with_data):
        """Test retrieving a specific timeline by ID"""
        user, headers = test_user_with_data

        # Generate a schedule
        generate_response = client.post("/scheduler/generate", headers=headers)
        assert generate_response.status_code == 200
        timeline_id = generate_response.json()["timeline_id"]

        # Retrieve it
        response = client.get(f"/scheduler/{timeline_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == timeline_id
        assert "tasks" in data
        assert "tasks_detailed" in data
        # Verify tasks are present
        assert len(data["tasks"]) > 0

    def test_get_schedule_not_found(self, client, auth_headers):
        """Test getting non-existent timeline returns 404"""
        response = client.get("/scheduler/99999", headers=auth_headers)

        assert response.status_code == 404
        assert "Timeline not found" in response.json()["detail"]

    def test_schedule_unauthorized(self, client):
        """Test schedule endpoints require authentication"""
        response = client.post("/scheduler/generate")
        assert response.status_code in [401, 403]

        response = client.get("/scheduler/history")
        assert response.status_code in [401, 403]

        response = client.get("/scheduler/1")
        assert response.status_code in [401, 403]

    def test_generate_schedule_with_invalid_dates(self, client, test_user_with_data):
        """Test schedule generation with invalid date range"""
        user, headers = test_user_with_data

        # End date before start date
        start_date = datetime.now()
        end_date = start_date - timedelta(days=1)

        response = client.post(
            "/scheduler/generate",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=headers,
        )

        # Should return error
        assert response.status_code == 422 or response.status_code == 400

    def test_schedule_isolated_per_user(self, client, test_db, test_user_with_data):
        """Test that schedules are isolated per user"""
        user1, headers1 = test_user_with_data

        # Generate schedule for user1
        response1 = client.post("/scheduler/generate", headers=headers1)
        assert response1.status_code == 200
        timeline1_id = response1.json()["timeline_id"]

        # Create second user
        user2 = UserModel(
            email="user2@example.com",
            username="user2",
            hashed_password=get_password_hash("pass2"),
        )
        test_db.add(user2)
        test_db.commit()

        token2 = create_access_token(data={"sub": user2.email})
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User2 should not see user1's schedules in history
        history2 = client.get("/scheduler/history", headers=headers2).json()
        timeline_ids_user2 = [t["id"] for t in history2]
        assert timeline1_id not in timeline_ids_user2

        # User1's history should contain their own timeline
        history1 = client.get("/scheduler/history", headers=headers1).json()
        timeline_ids_user1 = [t["id"] for t in history1]
        assert timeline1_id in timeline_ids_user1

    def test_history_empty(self, client, auth_headers):
        """Test schedule history is empty when no schedules generated"""
        response = client.get("/scheduler/history", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_schedule_with_time_blocks_required(
        self, client, test_user_with_data, test_db
    ):
        """Test that having no time blocks can cause scheduling issues"""
        user, headers = test_user_with_data

        # Delete all time blocks for the user
        test_db.query(TimeBlockModel).filter(TimeBlockModel.user_id == user.id).delete()
        test_db.commit()

        response = client.post("/scheduler/generate", headers=headers)

        # Should fail due to no available working hours
        assert response.status_code in [400, 422]
        data = response.json()
        assert (
            "No available working hours" in data.get("detail", "")
            or "time" in data.get("detail", "").lower()
        )

    def test_complex_workflow(self, client, test_user_with_data):
        """Test a complex workflow: create tasks, generate schedule, get history, retrieve specific"""
        user, headers = test_user_with_data

        # 1. Check initial task count
        tasks_initial = client.get("/tasks/", headers=headers).json()
        initial_task_count = len(tasks_initial)

        # 2. Generate a schedule
        schedule_resp = client.post("/scheduler/generate", headers=headers)
        assert schedule_resp.status_code == 200
        schedule_data = schedule_resp.json()
        timeline_id = schedule_data["timeline_id"]

        # 3. Get history - should include this schedule
        history = client.get("/scheduler/history", headers=headers).json()
        assert timeline_id in [t["id"] for t in history]

        # 4. Get specific timeline
        specific = client.get(f"/scheduler/{timeline_id}", headers=headers).json()
        assert specific["id"] == timeline_id
        assert len(specific["tasks"]) <= schedule_data["stats"]["scheduled_tasks"]

        # 5. Generate another schedule
        schedule2_resp = client.post("/scheduler/generate", headers=headers)
        assert schedule2_resp.status_code == 200
        timeline2_id = schedule2_resp.json()["timeline_id"]

        # History should now have at least 2 entries
        history = client.get("/scheduler/history", headers=headers).json()
        assert len(history) >= 2
        assert timeline1_id in [t["id"] for t in history]
        assert timeline2_id in [t["id"] for t in history]
