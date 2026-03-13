from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VideoResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    user_id: int
    status: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoStatusUpdate(BaseModel):
    status: str
    error_message: Optional[str] = None
