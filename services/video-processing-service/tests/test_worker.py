import json
from unittest.mock import MagicMock, patch

import pytest

from app.worker import callback, handle_video, update_video_status


class TestUpdateVideoStatus:
    @patch("app.worker.httpx.patch")
    def test_update_status_success(self, mock_patch):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        update_video_status(1, "processing")
        mock_patch.assert_called_once()

    @patch("app.worker.httpx.patch", side_effect=Exception("Connection error"))
    def test_update_status_failure(self, mock_patch):
        # Should not raise, just log
        update_video_status(1, "processing")


class TestHandleVideo:
    @patch("app.worker.publish_error_event")
    @patch("app.worker.update_video_status")
    @patch("app.worker.process_video", return_value=True)
    def test_handle_video_success(self, mock_process, mock_update, mock_publish):
        video_data = {"video_id": 1, "filename": "test.mp4", "user_id": 1}
        connection_params = MagicMock()

        handle_video(video_data, connection_params)

        mock_update.assert_any_call(1, "processing")
        mock_update.assert_any_call(1, "completed")
        mock_publish.assert_not_called()

    @patch("app.worker.publish_error_event")
    @patch("app.worker.update_video_status")
    @patch("app.worker.process_video", return_value=False)
    def test_handle_video_failure(self, mock_process, mock_update, mock_publish):
        video_data = {"video_id": 1, "filename": "test.mp4", "user_id": 1}
        connection_params = MagicMock()

        handle_video(video_data, connection_params)

        mock_update.assert_any_call(1, "processing")
        mock_update.assert_any_call(1, "error", "Video processing failed")
        mock_publish.assert_called_once()


class TestCallback:
    @patch("app.worker.executor")
    @patch("app.worker.update_video_status")
    def test_callback_uploaded_event(self, mock_update, mock_executor):
        ch = MagicMock()
        method = MagicMock()
        properties = MagicMock()
        body = json.dumps(
            {
                "event_type": "video.uploaded",
                "data": {"video_id": 1, "filename": "test.mp4", "user_id": 1},
            }
        )

        callback(ch, method, properties, body.encode())

        mock_update.assert_called_with(1, "queued")
        mock_executor.submit.assert_called_once()
        ch.basic_ack.assert_called_once()

    def test_callback_invalid_json(self):
        ch = MagicMock()
        method = MagicMock()
        properties = MagicMock()

        callback(ch, method, properties, b"invalid json")
        ch.basic_nack.assert_called_once()
