import os

os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestRegisterEndpoint:
    @patch("app.auth.redis_client")
    def test_register_success(self, mock_redis, client):
        response = client.post(
            "/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data

    @patch("app.auth.redis_client")
    def test_register_duplicate_username(self, mock_redis, client):
        client.post(
            "/register",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "password123",
            },
        )
        response = client.post(
            "/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "password456",
            },
        )
        assert response.status_code == 400


class TestLoginEndpoint:
    @patch("app.auth.redis_client")
    def test_login_success(self, mock_redis, client):
        mock_redis.setex = MagicMock()
        client.post(
            "/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch("app.auth.redis_client")
    def test_login_wrong_password(self, mock_redis, client):
        client.post(
            "/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/login",
            data={"username": "nobody", "password": "password123"},
        )
        assert response.status_code == 401
