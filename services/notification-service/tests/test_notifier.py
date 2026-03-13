from unittest.mock import MagicMock, patch

import pytest

from app.notifier import send_email_notification, send_error_notification


class TestSendEmailNotification:
    @patch("app.notifier.smtplib.SMTP")
    def test_send_email_success(self, mock_smtp):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = send_email_notification(
            "test@example.com", "Test Subject", "Test Body"
        )
        assert result is True

    @patch("app.notifier.smtplib.SMTP", side_effect=Exception("SMTP error"))
    def test_send_email_failure(self, mock_smtp):
        result = send_email_notification(
            "test@example.com", "Test Subject", "Test Body"
        )
        assert result is False


class TestSendErrorNotification:
    @patch("app.notifier.send_email_notification", return_value=True)
    def test_send_error_notification(self, mock_send):
        result = send_error_notification(
            "test@example.com", "video.mp4", "Processing failed"
        )
        assert result is True
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert "video.mp4" in call_args[0][1]
