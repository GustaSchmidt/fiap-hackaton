import json
from unittest.mock import MagicMock, patch

import pytest

from app.worker import callback, get_user_email


class TestGetUserEmail:
    @patch("app.worker.httpx.get")
    def test_get_user_email(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        email = get_user_email(1)
        assert "1" in email

    @patch("app.worker.httpx.get", side_effect=Exception("Connection error"))
    def test_get_user_email_fallback(self, mock_get):
        email = get_user_email(1)
        assert "1" in email


class TestCallback:
    @patch("app.worker.send_error_notification", return_value=True)
    @patch("app.worker.get_user_email", return_value="user@test.com")
    def test_callback_error_event(self, mock_email, mock_notify):
        ch = MagicMock()
        method = MagicMock()
        properties = MagicMock()
        body = json.dumps(
            {
                "event_type": "video.error",
                "data": {
                    "video_id": 1,
                    "user_id": 1,
                    "original_filename": "test.mp4",
                    "error_message": "Processing failed",
                },
            }
        )

        callback(ch, method, properties, body.encode())

        mock_notify.assert_called_once_with("user@test.com", "test.mp4", "Processing failed")
        ch.basic_ack.assert_called_once()

    def test_callback_invalid_json(self):
        ch = MagicMock()
        method = MagicMock()
        properties = MagicMock()

        callback(ch, method, properties, b"invalid json")
        ch.basic_nack.assert_called_once()
