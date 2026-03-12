"""
Integration tests for Authentication Router
Tests the full auth flow with a test database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.main import app
from shared.schemas import UserCreate, Token

# Test database URL
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


class TestAuthEndpoints:
    """Test authentication endpoints end-to-end"""

    def test_register_success(self, client):
        """Test user registration"""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepass123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "created_at" in data
        # Password should not be returned
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client):
        """Test registration fails with duplicate email"""
        # First registration
        client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "password123",
            },
        )

        # Second registration with same email
        response = client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "password456",
            },
        )

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_login_success(self, client):
        """Test user login"""
        # Create user first
        client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "mypassword",
            },
        )

        # Login
        response = client.post(
            "/auth/login",
            data={"username": "login@example.com", "password": "mypassword"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with wrong credentials"""
        response = client.post(
            "/auth/login",
            data={"username": "wrong@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_get_me_authenticated(self, client):
        """Test getting current user profile with valid token"""
        # Register a user
        register_response = client.post(
            "/auth/register",
            json={
                "email": "me@example.com",
                "username": "meuser",
                "password": "password123",
            },
        )
        assert register_response.status_code == 201

        # Login to get token
        login_response = client.post(
            "/auth/login",
            data={"username": "me@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Access /auth/me with token
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["username"] == "meuser"
        assert "id" in data

    def test_get_me_no_token(self, client):
        """Test /auth/me fails without token"""
        response = client.get("/auth/me")

        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_get_me_invalid_token(self, client):
        """Test /auth/me fails with invalid token"""
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    def test_register_password_min_length(self, client):
        """Test registration enforces password minimum length"""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "short",  # Only 5 characters
            },
        )

        assert response.status_code == 422  # Validation error
