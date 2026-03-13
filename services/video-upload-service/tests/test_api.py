import io
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_upload.db"

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_upload.db"

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
        assert response.json()["service"] == "video-upload-service"


class TestUploadEndpoint:
    @patch("app.main.redis_client")
    @patch("app.main.publish_video_event")
    @patch("app.main.upload_file", return_value=True)
    @patch("app.auth_middleware.jwt")
    def test_upload_video_success(
        self, mock_jwt, mock_upload, mock_publish, mock_redis, client
    ):
        mock_jwt.decode.return_value = {"sub": "1"}
        mock_redis.delete = MagicMock()

        video_content = b"fake video content"
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", io.BytesIO(video_content), "video/mp4")},
            headers={"Authorization": "Bearer fake_token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "test.mp4"
        assert data["status"] == "uploaded"
        assert data["user_id"] == 1

    @patch("app.auth_middleware.jwt")
    def test_upload_non_video_file(self, mock_jwt, client):
        mock_jwt.decode.return_value = {"sub": "1"}

        response = client.post(
            "/upload",
            files={"file": ("test.txt", io.BytesIO(b"text"), "text/plain")},
            headers={"Authorization": "Bearer fake_token"},
        )
        assert response.status_code == 400

    def test_upload_without_auth(self, client):
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", io.BytesIO(b"video"), "video/mp4")},
        )
        assert response.status_code == 401


class TestListVideosEndpoint:
    @patch("app.main.redis_client")
    @patch("app.auth_middleware.jwt")
    def test_list_videos_empty(self, mock_jwt, mock_redis, client):
        mock_jwt.decode.return_value = {"sub": "1"}
        mock_redis.get.return_value = None
        mock_redis.setex = MagicMock()

        response = client.get(
            "/videos",
            headers={"Authorization": "Bearer fake_token"},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_videos_without_auth(self, client):
        response = client.get("/videos")
        assert response.status_code == 401
