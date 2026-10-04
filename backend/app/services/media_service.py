"""Validate and persist content-series media uploads."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.core.errors import UploadInvalidError
from app.models.enums import MediaType
from app.schemas.media import MediaUploadOut

IMAGE_MAX_BYTES = 5 * 1024 * 1024
VIDEO_MAX_BYTES = 16 * 1024 * 1024
MAX_MEDIA_BYTES = VIDEO_MAX_BYTES


@dataclass(frozen=True)
class DetectedMedia:
    """Content-derived media metadata."""

    media_type: MediaType
    extension: str


class MediaService:
    """Store validated media with non-guessable filenames."""

    def __init__(self, storage_dir: Path, public_url: str) -> None:
        self._storage_dir = storage_dir
        self._public_url = public_url.rstrip("/")

    async def upload(self, content: bytes) -> MediaUploadOut:
        """Validate file bytes and persist one media asset."""
        detected = detect_media(content)
        _validate_size(content, detected.media_type)
        filename = f"{uuid4().hex}{detected.extension}"
        await asyncio.to_thread(self._write, filename, content)
        return MediaUploadOut(
            url=f"{self._public_url}/{filename}",
            media_type=detected.media_type,
        )

    def _write(self, filename: str, content: bytes) -> None:
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        destination = self._storage_dir / filename
        temporary = destination.with_suffix(f"{destination.suffix}.tmp")
        temporary.write_bytes(content)
        temporary.replace(destination)


def detect_media(content: bytes) -> DetectedMedia:
    """Detect an allowed image or MP4 from its binary signature."""
    if content.startswith(b"\xff\xd8\xff") and content.endswith(b"\xff\xd9"):
        return DetectedMedia(MediaType.IMAGE, ".jpg")
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return DetectedMedia(MediaType.IMAGE, ".png")
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return DetectedMedia(MediaType.IMAGE, ".webp")
    if len(content) >= 12 and content[4:8] == b"ftyp":
        return DetectedMedia(MediaType.VIDEO, ".mp4")
    raise UploadInvalidError("File content must be JPG, PNG, WebP, or MP4")


def _validate_size(content: bytes, media_type: MediaType) -> None:
    limit = IMAGE_MAX_BYTES if media_type == MediaType.IMAGE else VIDEO_MAX_BYTES
    if len(content) > limit:
        label = "Image" if media_type == MediaType.IMAGE else "Video"
        limit_mb = limit // (1024 * 1024)
        raise UploadInvalidError(f"{label} must be {limit_mb} MB or smaller")
