"""
Unit tests for Authentication Router
Tests the auth endpoints with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session
from jose import JWTError

from backend.auth.router import router, get_current_user
from backend.models.user import User as UserModel
from shared.schemas import UserCreate, UserResponse, Token


class TestGetCurrentUser:
    """Test the get_current_user dependency"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """Create a sample user"""
        return UserModel(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_db, mock_user):
        """Test valid token returns user"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Mock decode_token to return a valid payload
        with patch(
            "backend.auth.router.decode_token", return_value={"sub": "test@example.com"}
        ):
            user = await get_current_user("valid-token", mock_db)

        assert user.id == 1
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_db):
        """Test invalid token raises 401"""
        with patch("backend.auth.router.decode_token", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("invalid-token", mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub(self, mock_db):
        """Test token without sub claim raises 401"""
        with patch("backend.auth.router.decode_token", return_value={"exp": 123}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("token-no-sub", mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_db):
        """Test user not in database raises 401"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch(
            "backend.auth.router.decode_token",
            return_value={"sub": "nonexistent@example.com"},
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("token-valid-but-user-missing", mock_db)

        assert exc_info.value.status_code == 401


class TestRegister:
    """Test the register endpoint"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def user_create_data(self):
        """Sample user registration data"""
        return UserCreate(
            email="new@example.com", username="newuser", password="securepassword123"
        )

    @pytest.mark.asyncio
    async def test_register_success(self, mock_db, user_create_data):
        """Test successful user registration"""
        # Simulate no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Mock the user that would be created
        created_user = UserModel(
            id=1,
            email=user_create_data.email,
            username=user_create_data.username,
            hashed_password="hashed_password",
            is_active=True,
        )
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        with patch.object(UserModel, "__init__", return_value=None) as mock_init:
            with patch(
                "backend.auth.router.get_password_hash", return_value="hashed_password"
            ):
                result = await router.routes[0].endpoint(
                    user_data=user_create_data, db=mock_db
                )

        # Verify user was created with correct data
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, mock_db, user_create_data):
        """Test registration with existing email fails"""
        # Simulate existing user
        existing_user = UserModel(
            id=1,
            email=user_create_data.email,
            username="existing",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await router.routes[0].endpoint(user_data=user_create_data, db=mock_db)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail


class TestLogin:
    """Test the login endpoint"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """Create a sample user for login"""
        return UserModel(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_login_success(self, mock_db, mock_user):
        """Test successful login returns token"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        form_data = MagicMock()
        form_data.username = "test@example.com"
        form_data.password = "plain_password"

        with patch("backend.auth.router.verify_password", return_value=True):
            with patch(
                "backend.auth.router.create_access_token", return_value="jwt-token"
            ) as mock_token:
                result = await router.routes[1].endpoint(
                    form_data=form_data, db=mock_db
                )

        assert isinstance(result, Token)
        assert result.access_token == "jwt-token"
        assert result.token_type == "bearer"
        mock_token.assert_called_once_with(data={"sub": mock_user.email})

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, mock_db, mock_user):
        """Test login with wrong password fails"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        form_data = MagicMock()
        form_data.username = "test@example.com"
        form_data.password = "wrong_password"

        with patch("backend.auth.router.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await router.routes[1].endpoint(form_data=form_data, db=mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, mock_db):
        """Test login with inactive user fails"""
        inactive_user = UserModel(
            id=1,
            email="inactive@example.com",
            hashed_password="hashed",
            is_active=False,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inactive_user
        mock_db.execute.return_value = mock_result

        form_data = MagicMock()
        form_data.username = "inactive@example.com"
        form_data.password = "password"

        with patch("backend.auth.router.verify_password", return_value=True):
            with pytest.raises(HTTPException) as exc_info:
                await router.routes[1].endpoint(form_data=form_data, db=mock_db)

        assert exc_info.value.status_code == 400
        assert "Inactive user" in exc_info.value.detail


class TestGetMe:
    """Test the /auth/me endpoint"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """Create a sample user"""
        return UserModel(
            id=1,
            email="me@example.com",
            username="meuser",
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_get_me_success(self, mock_db, mock_user):
        """Test getting current user profile"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Mock decode_token to return email
        with patch(
            "backend.auth.router.decode_token", return_value={"sub": mock_user.email}
        ):
            result = await router.routes[2].endpoint(current_user=mock_user)

        assert result.id == mock_user.id
        assert result.email == mock_user.email
        assert result.username == mock_user.username
