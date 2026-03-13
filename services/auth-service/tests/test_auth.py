from unittest.mock import MagicMock, patch

import pytest

from app.auth import create_access_token, get_password_hash, verify_password, verify_token


class TestPasswordHashing:
    def test_hash_password(self):
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_correct_password(self):
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password("wrong_password", hashed) is False


class TestJWTTokens:
    @patch("app.auth.redis_client")
    def test_create_access_token(self, mock_redis):
        mock_redis.setex = MagicMock()
        token = create_access_token(data={"sub": "1"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    @patch("app.auth.redis_client")
    def test_verify_valid_token(self, mock_redis):
        mock_redis.setex = MagicMock()
        token = create_access_token(data={"sub": "1"})
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "1"

    def test_verify_invalid_token(self):
        payload = verify_token("invalid_token")
        assert payload is None

    @patch("app.auth.redis_client")
    def test_token_contains_expiration(self, mock_redis):
        mock_redis.setex = MagicMock()
        token = create_access_token(data={"sub": "1"})
        payload = verify_token(token)
        assert "exp" in payload
