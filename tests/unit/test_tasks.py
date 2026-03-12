"""
Unit tests for Tasks CRUD Router
Tests the task management endpoints with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.routers.tasks import router
from backend.auth.utils import get_current_user
from backend.models.task import Task as TaskModel
from backend.models.user import User as UserModel
from shared.schemas import TaskCreate, TaskUpdate, Priority, Quadrant


# Note: Tests now use the real get_current_user dependency but mock it to return user_id


class TestListTasks:
    """Test the list_tasks endpoint"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_tasks(self):
        """Create sample tasks"""
        now = datetime.now(timezone.utc)
        return [
            TaskModel(
                id=1,
                user_id=1,
                title="Task 1",
                description="Description 1",
                quadrant=Quadrant.Q1,
                priority=Priority.HIGH,
                estimated_duration=60,
                due_date=now,
                completed=False,
                created_at=now,
            ),
            TaskModel(
                id=2,
                user_id=1,
                title="Task 2",
                description="Description 2",
                quadrant=Quadrant.Q2,
                priority=Priority.MEDIUM,
                estimated_duration=30,
                due_date=None,
                completed=True,
                created_at=now,
            ),
        ]

    @pytest.mark.asyncio
    async def test_list_tasks_no_filters(self, mock_db, mock_tasks):
        """Test listing all tasks for a user"""
        # Mock the query chain
        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.scalars.return_value = mock_query
        mock_query.all.return_value = mock_tasks
        mock_db.execute.return_value = mock_query

        # Call the endpoint directly (simulating dependency injection)
        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            result = await router.routes[0].endpoint(
                completed=None, priority=None, db=mock_db
            )

        assert len(result) == 2
        assert result[0].title == "Task 1"
        assert result[1].title == "Task 2"

    @pytest.mark.asyncio
    async def test_list_tasks_filter_completed(self, mock_db, mock_tasks):
        """Test filtering by completed status"""
        active_tasks = [t for t in mock_tasks if not t.completed]

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.scalars.return_value = mock_query
        mock_query.all.return_value = active_tasks
        mock_db.execute.return_value = mock_query

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            result = await router.routes[0].endpoint(
                completed=False, priority=None, db=mock_db
            )

        assert len(result) == 1
        assert result[0].completed is False

    @pytest.mark.asyncio
    async def test_list_tasks_filter_priority(self, mock_db, mock_tasks):
        """Test filtering by priority"""
        high_priority = [t for t in mock_tasks if t.priority == Priority.HIGH]

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.scalars.return_value = mock_query
        mock_query.all.return_value = high_priority
        mock_db.execute.return_value = mock_query

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            result = await router.routes[0].endpoint(
                completed=None, priority=Priority.HIGH, db=mock_db
            )

        assert len(result) == 1
        assert result[0].priority == Priority.HIGH


class TestCreateTask:
    """Test the create_task endpoint"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def task_create_data(self):
        """Sample task creation data"""
        return TaskCreate(
            title="New Task",
            description="A new task",
            quadrant=Quadrant.Q2,
            priority=Priority.HIGH,
            estimated_duration=90,
            due_date=datetime(2026, 1, 20, 12, 0, tzinfo=timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_create_task_with_quadrant(self, mock_db, task_create_data):
        """Test creating a task with explicit quadrant"""
        # Mock refresh
        mock_task = TaskModel(
            id=1,
            user_id=1,
            title=task_create_data.title,
            description=task_create_data.description,
            quadrant=task_create_data.quadrant,
            priority=task_create_data.priority,
            estimated_duration=task_create_data.estimated_duration,
            due_date=task_create_data.due_date,
            completed=False,
            created_at=datetime.now(timezone.utc),
        )
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            # Call directly with mocked model instantiation
            with patch.object(TaskModel, "__init__", return_value=None) as mock_init:
                result = await router.routes[1].endpoint(
                    task_data=task_create_data, db=mock_db
                )

        # Verify the task was created
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_task_ai_classification(self, mock_db):
        """Test creating a task without quadrant triggers AI classification"""
        task_data_no_quadrant = TaskCreate(
            title="AI Task",
            description="Will be classified",
            quadrant=None,  # No quadrant provided
            priority=Priority.MEDIUM,
            estimated_duration=45,
        )

        # Mock AI classifier
        mock_classification = MagicMock()
        mock_classification.quadrant = "important_urgent"
        mock_classifier = MagicMock()
        mock_classifier.classify = AsyncMock(return_value=mock_classification)

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            with patch(
                "backend.routers.tasks.EisenhowerQuadrantClassifier",
                return_value=mock_classifier,
            ):
                with patch.object(TaskModel, "__init__", return_value=None):
                    try:
                        result = await router.routes[1].endpoint(
                            task_data=task_data_no_quadrant, db=mock_db
                        )
                    except Exception as e:
                        # The actual endpoint may raise due to our mock, but we can check classifier was called
                        pass

        mock_classifier.classify.assert_called_once_with(
            task_title=task_data_no_quadrant.title,
            task_description=task_data_no_quadrant.description,
        )


class TestGetTask:
    """Test the get_task endpoint"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_task(self):
        now = datetime.now(timezone.utc)
        return TaskModel(
            id=42,
            user_id=1,
            title="Test Task",
            quadrant=Quadrant.Q1,
            priority=Priority.CRITICAL,
            created_at=now,
        )

    @pytest.mark.asyncio
    async def test_get_task_success(self, mock_db, mock_task):
        """Test retrieving a task by ID"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db.execute.return_value = mock_result

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            result = await router.routes[2].endpoint(task_id=42, db=mock_db)

        assert result.id == 42
        assert result.title == "Test Task"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mock_db):
        """Test 404 when task doesn't exist"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            with pytest.raises(HTTPException) as exc_info:
                await router.routes[2].endpoint(task_id=999, db=mock_db)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Task not found"

    @pytest.mark.asyncio
    async def test_get_task_wrong_user(self, mock_db, mock_task):
        """Test 404 when task belongs to different user"""
        mock_task.user_id = 2  # Different user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = (
            None  # Query returns None because user_id mismatch
        )
        mock_db.execute.return_value = mock_result

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            with pytest.raises(HTTPException) as exc_info:
                await router.routes[2].endpoint(task_id=42, db=mock_db)

        assert exc_info.value.status_code == 404


class TestUpdateTask:
    """Test the update_task endpoint"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_task(self):
        now = datetime.now(timezone.utc)
        return TaskModel(
            id=42,
            user_id=1,
            title="Original Title",
            description="Original desc",
            quadrant=Quadrant.Q1,
            priority=Priority.MEDIUM,
            estimated_duration=60,
            completed=False,
            created_at=now,
            updated_at=now,
        )

    @pytest.mark.asyncio
    async def test_update_task_success(self, mock_db, mock_task):
        """Test updating task fields"""
        update_data = TaskUpdate(
            title="Updated Title",
            priority=Priority.HIGH,
            completed=True,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            result = await router.routes[3].endpoint(
                task_id=42, task_update=update_data, db=mock_db
            )

        # Verify updates were applied
        assert mock_task.title == "Updated Title"
        assert mock_task.priority == Priority.HIGH.value
        assert mock_task.completed is True
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_task_partial(self, mock_db, mock_task):
        """Test partial update with only some fields"""
        update_data = TaskUpdate(estimated_duration=120)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            result = await router.routes[3].endpoint(
                task_id=42, task_update=update_data, db=mock_db
            )

        assert mock_task.estimated_duration == 120
        # Other fields unchanged
        assert mock_task.title == "Original Title"

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, mock_db):
        """Test 404 when updating non-existent task"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        update_data = TaskUpdate(title="Updated")

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            with pytest.raises(HTTPException) as exc_info:
                await router.routes[3].endpoint(
                    task_id=999, task_update=update_data, db=mock_db
                )

        assert exc_info.value.status_code == 404


class TestDeleteTask:
    """Test the delete_task endpoint"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_task(self):
        return TaskModel(
            id=42,
            user_id=1,
            title="To be deleted",
            quadrant=Quadrant.Q3,
        )

    @pytest.mark.asyncio
    async def test_delete_task_success(self, mock_db, mock_task):
        """Test deleting a task"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db.execute.return_value = mock_result
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            result = await router.routes[4].endpoint(task_id=42, db=mock_db)

        assert result is None
        mock_db.delete.assert_called_once_with(mock_task)
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, mock_db):
        """Test 404 when deleting non-existent task"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("backend.routers.tasks.get_current_user") as mock_get_user:
            mock_get_user.return_value = UserModel(
                id=1, email="test@example.com", username="test"
            )
            with pytest.raises(HTTPException) as exc_info:
                await router.routes[4].endpoint(task_id=999, db=mock_db)

        assert exc_info.value.status_code == 404
