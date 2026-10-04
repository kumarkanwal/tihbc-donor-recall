"""Media upload response schemas."""

from pydantic import BaseModel

from app.models.enums import MediaType


class MediaUploadOut(BaseModel):
    """Public URL and detected kind of one uploaded media file."""

    url: str
    media_type: MediaType
