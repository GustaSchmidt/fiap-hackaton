import os


class Settings:
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    VIDEO_UPLOAD_SERVICE_URL: str = os.getenv(
        "VIDEO_UPLOAD_SERVICE_URL", "http://video-upload-service:8002"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/2")
    MAX_CONCURRENT_WORKERS: int = int(os.getenv("MAX_CONCURRENT_WORKERS", "3"))
    PROCESSING_SIMULATE_TIME: int = int(os.getenv("PROCESSING_SIMULATE_TIME", "10"))


settings = Settings()
