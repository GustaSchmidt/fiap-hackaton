import os


class Settings:
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    VIDEO_UPLOAD_SERVICE_URL: str = os.getenv(
        "VIDEO_UPLOAD_SERVICE_URL", "http://video-upload-service:8002"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/2")
    MAX_CONCURRENT_WORKERS: int = int(os.getenv("MAX_CONCURRENT_WORKERS", "3"))

    # MinIO / S3 settings
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "password123")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "videos")

    # ffmpeg settings
    FFMPEG_OUTPUT_RESOLUTION: int = int(os.getenv("FFMPEG_OUTPUT_RESOLUTION", "720"))
    FFMPEG_TIMEOUT: int = int(os.getenv("FFMPEG_TIMEOUT", "600"))


settings = Settings()
