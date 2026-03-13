import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://fiapx:fiapx123@postgres:5432/fiapx_videos",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/1")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "password123")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "videos")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fiapx-secret-key-change-in-production")
    ALGORITHM: str = "HS256"


settings = Settings()
