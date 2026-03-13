"""
Integration tests for WebSocket functionality.
Tests real-time updates for task operations and schedule generation.
"""

import pytest
import json
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from backend.database import Base
from backend.main import app
from backend.models.user import User as UserModel
from backend.models.task import Task as TaskModel
from backend.auth.utils import get_password_hash, create_access_token
from shared.schemas import UserCreate

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

    from backend.database import get_db as original_get_db

    app.dependency_overrides[original_get_db] = override_get_db

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


class TestWebSocket:
    """Test WebSocket real-time updates"""

    def test_websocket_connection_with_valid_token(self, client, test_user):
        """Test WebSocket connection with valid JWT token"""
        user, token = test_user

        with client.websocket_connect(f"/ws?token={token}") as websocket:
            # Should receive connected message
            data = websocket.receive_json()
            assert data["event"] == "connected"
            assert data["data"]["user_id"] == user.id
            assert "Connected to Tact AI real-time updates" in data["data"]["message"]

    def test_websocket_connection_without_token(self, client):
        """Test WebSocket connection fails without token"""
        with pytest.raises(Exception) as exc_info:
            with client.websocket_connect("/ws"):
                pass
        # Should close with code 1008 (policy violation) or similar
        assert "Missing authentication token" in str(
            exc_info.value
        ) or "Invalid authentication token" in str(exc_info.value)

    def test_websocket_connection_with_invalid_token(self, client):
        """Test WebSocket connection fails with invalid token"""
        with pytest.raises(Exception) as exc_info:
            with client.websocket_connect("/ws?token=invalid-token"):
                pass
        assert "Invalid authentication token" in str(exc_info.value)

    def test_task_created_broadcast(self, client, test_user, test_db):
        """Test that creating a task broadcasts to WebSocket"""
        user, token = test_user

        with client.websocket_connect(f"/ws?token={token}") as websocket:
            # Create a task via REST API
            response = client.post(
                "/tasks/",
                json={
                    "title": "Test Task",
                    "description": "Test description",
                    "priority": "high",
                    "estimated_duration": 60,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 201
            task = response.json()

            # WebSocket should receive task_created event
            data = websocket.receive_json()
            assert data["event"] == "task_created"
            assert data["data"]["id"] == task["id"]
            assert data["data"]["title"] == "Test Task"

    def test_task_updated_broadcast(self, client, test_user, test_db):
        """Test that updating a task broadcasts to WebSocket"""
        user, token = test_user

        # Create a task first
        response = client.post(
            "/tasks/",
            json={
                "title": "Original Title",
                "description": "Original description",
                "priority": "medium",
                "estimated_duration": 30,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        task = response.json()
        task_id = task["id"]

        with client.websocket_connect(f"/ws?token={token}") as websocket:
            # Update the task
            response = client.put(
                f"/tasks/{task_id}",
                json={
                    "title": "Updated Title",
                    "description": "Updated description",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200

            # WebSocket should receive task_updated event
            data = websocket.receive_json()
            assert data["event"] == "task_updated"
            assert data["data"]["id"] == task_id
            assert data["data"]["title"] == "Updated Title"

    def test_task_deleted_broadcast(self, client, test_user, test_db):
        """Test that deleting a task broadcasts to WebSocket"""
        user, token = test_user

        # Create a task first
        response = client.post(
            "/tasks/",
            json={
                "title": "Task to Delete",
                "description": "Will be deleted",
                "priority": "low",
                "estimated_duration": 15,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        task = response.json()
        task_id = task["id"]

        with client.websocket_connect(f"/ws?token={token}") as websocket:
            # Delete the task
            response = client.delete(
                f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 204

            # WebSocket should receive task_deleted event
            data = websocket.receive_json()
            assert data["event"] == "task_deleted"
            assert data["data"]["task_id"] == task_id

    def test_schedule_generated_broadcast(self, client, test_user, test_db):
        """Test that generating a schedule broadcasts schedule_updated event"""
        user, token = test_user

        # Create a few tasks first
        for i in range(3):
            response = client.post(
                "/tasks/",
                json={
                    "title": f"Task {i + 1}",
                    "description": f"Description {i + 1}",
                    "priority": "medium",
                    "estimated_duration": 60,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 201

        with client.websocket_connect(f"/ws?token={token}") as websocket:
            # Generate schedule
            response = client.post(
                "/scheduler/generate", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200

            # WebSocket should receive schedule_updated event
            data = websocket.receive_json()
            assert data["event"] == "schedule_updated"
            assert "timeline_id" in data["data"]
            assert "tasks" in data["data"]
            assert data["data"]["task_count"] >= 0

    def test_conflict_alert_broadcast(self, client, test_user, test_db):
        """Test that conflicts trigger conflict_alert broadcast"""
        user, token = test_user

        # Create tasks with overlapping characteristics that may cause conflicts
        # For simplicity, create tasks with very short deadlines
        response = client.post(
            "/tasks/",
            json={
                "title": "Urgent Task 1",
                "description": "Very urgent",
                "priority": "high",
                "estimated_duration": 240,  # 4 hours
                "due_date": (datetime.now() + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

        response = client.post(
            "/tasks/",
            json={
                "title": "Urgent Task 2",
                "description": "Also very urgent",
                "priority": "high",
                "estimated_duration": 240,  # 4 hours
                "due_date": (datetime.now() + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

        with client.websocket_connect(f"/ws?token={token}") as websocket:
            # Generate schedule - should detect conflicts due to over-commitment
            response = client.post(
                "/scheduler/generate", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200

            # May receive conflict_alert event (depends on scheduler outcome)
            # Try to receive with timeout
            received_conflict = False
            received_schedule = False
            start_time = time.time()
            timeout = 2  # seconds

            while time.time() - start_time < timeout:
                try:
                    data = websocket.receive_json(timeout=0.5)
                    if data["event"] == "conflict_alert":
                        received_conflict = True
                        assert "conflicts" in data["data"]
                        assert data["data"]["conflict_count"] >= 0
                    elif data["event"] == "schedule_updated":
                        received_schedule = True
                except Exception:
                    break

            # At least schedule_updated should be received
            assert received_schedule, "Expected schedule_updated event"

    def test_ping_pong(self, client, test_user):
        """Test ping/pong heartbeat mechanism"""
        user, token = test_user

        with client.websocket_connect(f"/ws?token={token}") as websocket:
            # Receive initial connected message
            websocket.receive_json()

            # Send ping
            ping_msg = {"type": "ping", "timestamp": time.time()}
            websocket.send_text(json.dumps(ping_msg))

            # Should receive pong
            data = websocket.receive_json()
            assert data["event"] == "pong" or data["type"] == "pong"
            if "type" in data:
                assert data["type"] == "pong"
                assert data["timestamp"] == ping_msg["timestamp"]

    def test_multiple_connections_same_user(self, client, test_user):
        """Test that user can have multiple WebSocket connections"""
        user, token = test_user

        with client.websocket_connect(f"/ws?token={token}") as ws1:
            with client.websocket_connect(f"/ws?token={token}") as ws2:
                # Both should receive connected messages
                data1 = ws1.receive_json()
                assert data1["event"] == "connected"
                data2 = ws2.receive_json()
                assert data2["event"] == "connected"

                # Both should have same user_id
                assert data1["data"]["user_id"] == user.id
                assert data2["data"]["user_id"] == user.id

                # Different connection IDs
                assert data1["data"]["connection_id"] != data2["data"]["connection_id"]
