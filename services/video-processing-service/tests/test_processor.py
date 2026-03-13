from unittest.mock import patch

import pytest

from app.processor import process_video


class TestVideoProcessor:
    @patch("app.processor.settings")
    def test_process_video_success(self, mock_settings):
        mock_settings.PROCESSING_SIMULATE_TIME = 1  # Speed up test
        result = process_video(1, "test_video.mp4")
        assert result is True

    @patch("app.processor.settings")
    @patch("app.processor.time.sleep", side_effect=Exception("Simulated failure"))
    def test_process_video_failure(self, mock_sleep, mock_settings):
        mock_settings.PROCESSING_SIMULATE_TIME = 1
        result = process_video(1, "test_video.mp4")
        assert result is False
