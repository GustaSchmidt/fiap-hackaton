import logging
import os
import subprocess
import tempfile

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


def _get_s3_client():
    """Create and return a boto3 S3 client configured for MinIO."""
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
    )


def _download_video(s3_client, filename: str, local_path: str) -> bool:
    """Download a video file from MinIO to a local path."""
    try:
        s3_client.download_file(settings.MINIO_BUCKET, filename, local_path)
        return True
    except ClientError as e:
        logger.error(f"Failed to download {filename} from MinIO: {e}")
        return False


def _upload_processed_video(s3_client, local_path: str, output_key: str) -> bool:
    """Upload a processed video file back to MinIO."""
    try:
        s3_client.upload_file(
            local_path,
            settings.MINIO_BUCKET,
            output_key,
            ExtraArgs={"ContentType": "video/mp4"},
        )
        return True
    except ClientError as e:
        logger.error(f"Failed to upload {output_key} to MinIO: {e}")
        return False


def _run_ffmpeg(input_path: str, output_path: str, resolution: int) -> bool:
    """Run ffmpeg to transcode the video to the target resolution."""
    command = [
        "ffmpeg",
        "-i", input_path,
        "-vf", f"scale=-2:{resolution}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        "-y",
        output_path,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=settings.FFMPEG_TIMEOUT,
        )
        if result.returncode != 0:
            logger.error(f"ffmpeg failed with code {result.returncode}: {result.stderr[-500:]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"ffmpeg timed out after {settings.FFMPEG_TIMEOUT}s")
        return False
    except FileNotFoundError:
        logger.error("ffmpeg not found. Make sure ffmpeg is installed.")
        return False


def process_video(video_id: int, filename: str) -> bool:
    """Download video from MinIO, transcode with ffmpeg, and upload the result.

    Steps:
        1. Download the original video from MinIO
        2. Transcode to H.264/AAC MP4 at the configured resolution
        3. Upload the processed file to MinIO under processed/ prefix
        4. Clean up temporary files
    """
    logger.info(f"Starting processing for video {video_id}: {filename}")
    resolution = settings.FFMPEG_OUTPUT_RESOLUTION

    with tempfile.TemporaryDirectory() as tmpdir:
        # Use only the basename to avoid subdirectory issues in temp paths
        basename = os.path.basename(filename)
        input_path = os.path.join(tmpdir, f"input_{basename}")
        output_path = os.path.join(tmpdir, f"output_{basename}")

        s3_client = _get_s3_client()

        logger.info(f"Video {video_id}: Downloading from MinIO")
        if not _download_video(s3_client, filename, input_path):
            return False

        logger.info(f"Video {video_id}: Transcoding to {resolution}p")
        if not _run_ffmpeg(input_path, output_path, resolution):
            return False

        output_key = f"processed/{filename}"
        logger.info(f"Video {video_id}: Uploading processed file to {output_key}")
        if not _upload_processed_video(s3_client, output_path, output_key):
            return False

    logger.info(f"Video {video_id}: Processing completed successfully")
    return True
