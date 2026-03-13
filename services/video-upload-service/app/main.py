import logging
import uuid
from typing import List

import redis as redis_lib
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.auth_middleware import get_current_user_id
from app.config import settings
from app.database import Base, engine, get_db
from app.messaging import publish_video_event
from app.models import Video
from app.schemas import VideoResponse, VideoStatusUpdate
from app.storage import ensure_bucket_exists, upload_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FIAP X - Video Upload Service", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis for caching
redis_client = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)

# Prometheus metrics
UPLOAD_COUNT = Counter("video_uploads_total", "Total video uploads")
UPLOAD_DURATION = Histogram("video_upload_duration_seconds", "Upload duration")

# Ensure MinIO bucket exists on startup
try:
    ensure_bucket_exists()
except Exception as e:
    logger.warning(f"Could not ensure bucket exists on startup: {e}")


@app.post("/upload", response_model=VideoResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    UPLOAD_COUNT.inc()

    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only video files are allowed",
        )

    # Generate unique filename
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "mp4"
    unique_filename = f"{user_id}/{uuid.uuid4()}.{ext}"

    # Upload to MinIO
    success = upload_file(file.file, unique_filename, file.content_type)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error storing video",
        )

    # Read file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    # Save metadata to DB
    video = Video(
        filename=unique_filename,
        original_filename=file.filename,
        user_id=user_id,
        status="uploaded",
        file_size=file_size,
        content_type=file.content_type,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Publish event to RabbitMQ
    publish_video_event(
        "video.uploaded",
        {
            "video_id": video.id,
            "filename": video.filename,
            "user_id": user_id,
            "original_filename": video.original_filename,
        },
    )

    # Invalidate cache
    redis_client.delete(f"videos:user:{user_id}")

    logger.info(f"Video {video.id} uploaded by user {user_id}")
    return video


@app.get("/videos", response_model=List[VideoResponse])
def list_user_videos(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # Try cache first
    import json

    cached = redis_client.get(f"videos:user:{user_id}")
    if cached:
        return json.loads(cached)

    videos = (
        db.query(Video)
        .filter(Video.user_id == user_id)
        .order_by(Video.created_at.desc())
        .all()
    )

    # Cache for 30 seconds
    video_list = [VideoResponse.model_validate(v).model_dump(mode="json") for v in videos]
    redis_client.setex(f"videos:user:{user_id}", 30, json.dumps(video_list))

    return videos


@app.get("/videos/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.user_id == user_id)
        .first()
    )
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    return video


@app.patch("/videos/{video_id}/status", response_model=VideoResponse)
def update_video_status(
    video_id: int,
    status_update: VideoStatusUpdate,
    db: Session = Depends(get_db),
):
    """Internal endpoint for updating video status (called by processing service)."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    video.status = status_update.status
    if status_update.error_message:
        video.error_message = status_update.error_message

    db.commit()
    db.refresh(video)

    # Invalidate cache
    redis_client.delete(f"videos:user:{video.user_id}")

    return video


@app.get("/health")
def health():
    return {"status": "healthy", "service": "video-upload-service"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
