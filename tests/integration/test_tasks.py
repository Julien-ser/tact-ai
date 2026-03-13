"""
Integration tests for Tasks Router
Tests the full task management CRUD operations with a real test database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, timezone

from backend.database import Base, get_db
from backend.main import app
from backend.models.user import User as UserModel
from backend.models.task import Task as TaskModel
from backend.auth.utils import get_password_hash, create_access_token
from shared.schemas import UserCreate, TaskCreate, TaskUpdate, Priority, Quadrant

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
def test_user(test_db):
    """Create a test user and return user object and token"""
    user = UserModel(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    token = create_access_token(data={"sub": user.email})
    return user, token


@pytest.fixture
def auth_headers(test_user):
    """Return authorization headers for the test user"""
    _, token = test_user
    return {"Authorization": f"Bearer {token}"}


class TestTasksIntegration:
    """Integration tests for task CRUD operations"""

    def test_create_task_success(self, client, test_user, auth_headers):
        """Test creating a task with valid data"""
        response = client.post(
            "/tasks/",
            json={
                "title": "Test Task",
                "description": "Test description",
                "priority": "high",
                "estimated_duration": 60,
                "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "Test description"
        assert data["priority"] == "high"
        assert data["estimated_duration"] == 60
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data

    def test_create_task_with_ai_classification(
        self, client, test_user, auth_headers, mocker
    ):
        """Test creating a task without quadrant triggers AI classification"""
        # Mock the OpenAI classifier to avoid real API calls
        mock_classification = mocker.MagicMock()
        mock_classification.quadrant = "important_urgent"
        mock_classifier = mocker.MagicMock()
        mock_classifier.classify = mocker.AsyncMock(return_value=mock_classification)

        mocker.patch(
            "backend.routers.tasks.EisenhowerQuadrantClassifier",
            return_value=mock_classifier,
        )

        response = client.post(
            "/tasks/",
            json={
                "title": "AI Task",
                "description": "Will be classified by AI",
                "priority": "medium",
                "estimated_duration": 45,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        # Should be Q1 (important_urgent maps to Q1)
        assert data["quadrant"] == "q1" or data["quadrant"] == "Q1"
        mock_classifier.classify.assert_called_once_with(
            task_title="AI Task", task_description="Will be classified by AI"
        )

    def test_create_task_unauthorized(self, client):
        """Test creating task fails without authentication"""
        response = client.post(
            "/tasks/",
            json={
                "title": "Test Task",
                "description": "Test",
                "priority": "low",
            },
        )

        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers

    def test_list_tasks_empty(self, client, test_user, auth_headers):
        """Test listing tasks when user has none"""
        response = client.get("/tasks/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_list_tasks_with_data(self, client, test_user, auth_headers):
        """Test listing user's tasks"""
        # Create a few tasks first
        for i in range(3):
            client.post(
                "/tasks/",
                json={
                    "title": f"Task {i}",
                    "description": f"Description {i}",
                    "priority": "medium",
                },
                headers=auth_headers,
            )

        response = client.get("/tasks/", headers=auth_headers)

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 3

    def test_list_tasks_filter_by_completed(self, client, test_user, auth_headers):
        """Test filtering tasks by completion status"""
        # Create tasks with different completion statuses
        client.post(
            "/tasks/",
            json={"title": "Active Task", "priority": "high"},
            headers=auth_headers,
        )
        client.post(
            "/tasks/",
            json={"title": "Completed Task", "priority": "low"},
            headers=auth_headers,
        )

        # Mark one as completed by updating it
        tasks = client.get("/tasks/", headers=auth_headers).json()
        completed_task_id = tasks[1]["id"]
        client.put(
            f"/tasks/{completed_task_id}",
            json={"completed": True},
            headers=auth_headers,
        )

        # Filter for active tasks
        response = client.get("/tasks/?completed=false", headers=auth_headers)
        assert response.status_code == 200
        active_tasks = response.json()
        assert all(not t["completed"] for t in active_tasks)

        # Filter for completed tasks
        response = client.get("/tasks/?completed=true", headers=auth_headers)
        assert response.status_code == 200
        completed_tasks = response.json()
        assert all(t["completed"] for t in completed_tasks)

    def test_list_tasks_filter_by_priority(self, client, test_user, auth_headers):
        """Test filtering tasks by priority"""
        client.post(
            "/tasks/",
            json={"title": "High Priority", "priority": "critical"},
            headers=auth_headers,
        )
        client.post(
            "/tasks/",
            json={"title": "Medium Priority", "priority": "medium"},
            headers=auth_headers,
        )
        client.post(
            "/tasks/",
            json={"title": "Low Priority", "priority": "low"},
            headers=auth_headers,
        )

        response = client.get("/tasks/?priority=high", headers=auth_headers)
        assert response.status_code == 200
        high_priority_tasks = response.json()
        assert len(high_priority_tasks) >= 1
        assert all(t["priority"] == "high" for t in high_priority_tasks)

    def test_get_task_success(self, client, test_user, auth_headers):
        """Test retrieving a specific task by ID"""
        create_response = client.post(
            "/tasks/",
            json={
                "title": "Get Me",
                "description": "Retrieve me",
                "priority": "medium",
            },
            headers=auth_headers,
        )
        task_id = create_response.json()["id"]

        response = client.get(f"/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Get Me"

    def test_get_task_not_found(self, client, auth_headers):
        """Test getting non-existent task returns 404"""
        response = client.get("/tasks/99999", headers=auth_headers)

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    def test_get_task_wrong_user(self, client, test_db, test_user, auth_headers):
        """Test user cannot access another user's task"""
        # Create another user
        other_user = UserModel(
            email="other@example.com",
            username="otheruser",
            hashed_password=get_password_hash("otherpass"),
        )
        test_db.add(other_user)
        test_db.commit()
        test_db.refresh(other_user)

        # Create task as other user
        other_token = create_access_token(data={"sub": other_user.email})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        create_response = client.post(
            "/tasks/",
            json={"title": "Other's Task", "priority": "high"},
            headers=other_headers,
        )
        task_id = create_response.json()["id"]

        # Try to access as first user
        response = client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_task_success(self, client, test_user, auth_headers):
        """Test updating task fields"""
        create_response = client.post(
            "/tasks/",
            json={
                "title": "Original",
                "description": "Original desc",
                "priority": "low",
            },
            headers=auth_headers,
        )
        task_id = create_response.json()["id"]

        update_response = client.put(
            f"/tasks/{task_id}",
            json={
                "title": "Updated",
                "description": "Updated desc",
                "priority": "high",
                "completed": True,
            },
            headers=auth_headers,
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["title"] == "Updated"
        assert data["description"] == "Updated desc"
        assert data["priority"] == "high"
        assert data["completed"] is True

    def test_update_task_partial(self, client, test_user, auth_headers):
        """Test partial update with only some fields"""
        create_response = client.post(
            "/tasks/",
            json={
                "title": "Original Title",
                "description": "Original desc",
                "priority": "medium",
                "estimated_duration": 60,
            },
            headers=auth_headers,
        )
        task_id = create_response.json()["id"]

        # Update only title
        update_response = client.put(
            f"/tasks/{task_id}",
            json={"title": "New Title"},
            headers=auth_headers,
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["title"] == "New Title"
        # Other fields should remain unchanged
        assert data["description"] == "Original desc"
        assert data["estimated_duration"] == 60

    def test_update_task_not_found(self, client, auth_headers):
        """Test updating non-existent task returns 404"""
        response = client.put(
            "/tasks/99999",
            json={"title": "Updated"},
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    def test_delete_task_success(self, client, test_user, auth_headers):
        """Test deleting a task"""
        create_response = client.post(
            "/tasks/",
            json={"title": "Delete Me", "priority": "low"},
            headers=auth_headers,
        )
        task_id = create_response.json()["id"]

        delete_response = client.delete(f"/tasks/{task_id}", headers=auth_headers)

        assert delete_response.status_code == 204

        # Verify task is gone
        get_response = client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_task_not_found(self, client, auth_headers):
        """Test deleting non-existent task returns 404"""
        response = client.delete("/tasks/99999", headers=auth_headers)

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    def test_task_lifecycle_full(self, client, test_user, auth_headers):
        """Test complete task lifecycle: create, read, update, delete"""
        # Create
        create_response = client.post(
            "/tasks/",
            json={
                "title": "Lifecycle Task",
                "description": "Full test",
                "priority": "medium",
                "estimated_duration": 120,
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Read
        read_response = client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert read_response.status_code == 200
        assert read_response.json()["title"] == "Lifecycle Task"

        # Update
        update_response = client.put(
            f"/tasks/{task_id}",
            json={"title": "Updated Lifecycle", "completed": True},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Lifecycle"

        # Delete
        delete_response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
        assert delete_response.status_code == 204

        # Verify deleted
        verify_response = client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert verify_response.status_code == 404

    def test_create_task_validation_missing_title(self, client, auth_headers):
        """Test task creation fails with missing required fields"""
        response = client.post(
            "/tasks/",
            json={"description": "No title"},
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_create_task_validation_invalid_priority(self, client, auth_headers):
        """Test task creation fails with invalid priority"""
        response = client.post(
            "/tasks/",
            json={"title": "Task", "priority": "invalid"},
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_user_isolation(self, client, test_db, test_user):
        """Test that users can only access their own tasks"""
        user1, token1 = test_user
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Create task as user1
        client.post(
            "/tasks/",
            json={"title": "User1 Task", "priority": "high"},
            headers=headers1,
        )

        # Create second user
        user2 = UserModel(
            email="user2@example.com",
            username="user2",
            hashed_password=get_password_hash("pass2"),
        )
        test_db.add(user2)
        test_db.commit()
        test_db.refresh(user2)

        token2 = create_access_token(data={"sub": user2.email})
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User2's task list should not include user1's task
        response2 = client.get("/tasks/", headers=headers2)
        assert response2.status_code == 200
        user2_tasks = response2.json()
        assert all(t["title"] != "User1 Task" for t in user2_tasks)

        # User1's task list should have their task
        response1 = client.get("/tasks/", headers=headers1)
        assert response1.status_code == 200
        user1_tasks = response1.json()
        assert any(t["title"] == "User1 Task" for t in user1_tasks)
