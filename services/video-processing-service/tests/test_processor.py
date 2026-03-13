import os
from unittest.mock import MagicMock, patch

import pytest

from app.processor import (
    _download_video,
    _run_ffmpeg,
    _upload_processed_video,
    process_video,
)


class TestDownloadVideo:
    @patch("app.processor.settings")
    def test_download_success(self, mock_settings):
        mock_settings.MINIO_BUCKET = "videos"
        mock_client = MagicMock()
        assert _download_video(mock_client, "test.mp4", "/tmp/test.mp4") is True
        mock_client.download_file.assert_called_once_with("videos", "test.mp4", "/tmp/test.mp4")

    @patch("app.processor.settings")
    def test_download_failure(self, mock_settings):
        from botocore.exceptions import ClientError

        mock_settings.MINIO_BUCKET = "videos"
        mock_client = MagicMock()
        mock_client.download_file.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "GetObject"
        )
        assert _download_video(mock_client, "missing.mp4", "/tmp/missing.mp4") is False


class TestUploadProcessedVideo:
    @patch("app.processor.settings")
    def test_upload_success(self, mock_settings):
        mock_settings.MINIO_BUCKET = "videos"
        mock_client = MagicMock()
        assert _upload_processed_video(mock_client, "/tmp/out.mp4", "processed/test.mp4") is True
        mock_client.upload_file.assert_called_once()

    @patch("app.processor.settings")
    def test_upload_failure(self, mock_settings):
        from botocore.exceptions import ClientError

        mock_settings.MINIO_BUCKET = "videos"
        mock_client = MagicMock()
        mock_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Internal"}}, "PutObject"
        )
        assert _upload_processed_video(mock_client, "/tmp/out.mp4", "processed/test.mp4") is False


class TestRunFfmpeg:
    @patch("app.processor.settings")
    @patch("app.processor.subprocess.run")
    def test_ffmpeg_success(self, mock_run, mock_settings):
        mock_settings.FFMPEG_TIMEOUT = 600
        mock_run.return_value = MagicMock(returncode=0)
        assert _run_ffmpeg("/tmp/in.mp4", "/tmp/out.mp4", 720) is True

    @patch("app.processor.settings")
    @patch("app.processor.subprocess.run")
    def test_ffmpeg_nonzero_exit(self, mock_run, mock_settings):
        mock_settings.FFMPEG_TIMEOUT = 600
        mock_run.return_value = MagicMock(returncode=1, stderr="encoding error")
        assert _run_ffmpeg("/tmp/in.mp4", "/tmp/out.mp4", 720) is False

    @patch("app.processor.settings")
    @patch("app.processor.subprocess.run", side_effect=FileNotFoundError)
    def test_ffmpeg_not_found(self, mock_run, mock_settings):
        mock_settings.FFMPEG_TIMEOUT = 600
        assert _run_ffmpeg("/tmp/in.mp4", "/tmp/out.mp4", 720) is False

    @patch("app.processor.settings")
    @patch("app.processor.subprocess.run", side_effect=__import__("subprocess").TimeoutExpired(cmd="ffmpeg", timeout=600))
    def test_ffmpeg_timeout(self, mock_run, mock_settings):
        mock_settings.FFMPEG_TIMEOUT = 600
        assert _run_ffmpeg("/tmp/in.mp4", "/tmp/out.mp4", 720) is False


class TestProcessVideo:
    @patch("app.processor._upload_processed_video", return_value=True)
    @patch("app.processor._run_ffmpeg", return_value=True)
    @patch("app.processor._download_video", return_value=True)
    @patch("app.processor._get_s3_client")
    @patch("app.processor.settings")
    def test_process_video_success(self, mock_settings, mock_s3, mock_dl, mock_ffmpeg, mock_ul):
        mock_settings.FFMPEG_OUTPUT_RESOLUTION = 720
        assert process_video(1, "test.mp4") is True
        mock_dl.assert_called_once()
        mock_ffmpeg.assert_called_once()
        mock_ul.assert_called_once()

    @patch("app.processor._download_video", return_value=False)
    @patch("app.processor._get_s3_client")
    @patch("app.processor.settings")
    def test_process_video_download_fails(self, mock_settings, mock_s3, mock_dl):
        mock_settings.FFMPEG_OUTPUT_RESOLUTION = 720
        assert process_video(1, "test.mp4") is False

    @patch("app.processor._run_ffmpeg", return_value=False)
    @patch("app.processor._download_video", return_value=True)
    @patch("app.processor._get_s3_client")
    @patch("app.processor.settings")
    def test_process_video_ffmpeg_fails(self, mock_settings, mock_s3, mock_dl, mock_ffmpeg):
        mock_settings.FFMPEG_OUTPUT_RESOLUTION = 720
        assert process_video(1, "test.mp4") is False

    @patch("app.processor._upload_processed_video", return_value=False)
    @patch("app.processor._run_ffmpeg", return_value=True)
    @patch("app.processor._download_video", return_value=True)
    @patch("app.processor._get_s3_client")
    @patch("app.processor.settings")
    def test_process_video_upload_fails(self, mock_settings, mock_s3, mock_dl, mock_ffmpeg, mock_ul):
        mock_settings.FFMPEG_OUTPUT_RESOLUTION = 720
        assert process_video(1, "test.mp4") is False
