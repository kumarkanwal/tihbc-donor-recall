"""Tests for content-derived media validation and storage."""

import asyncio
from pathlib import Path

import pytest

from app.core.errors import UploadInvalidError
from app.models.enums import MediaType
from app.services.media_service import (
    IMAGE_MAX_BYTES,
    VIDEO_MAX_BYTES,
    MediaService,
    detect_media,
)


@pytest.mark.parametrize(
    ("content", "media_type", "extension"),
    [
        (b"\xff\xd8\xffimage\xff\xd9", MediaType.IMAGE, ".jpg"),
        (b"\x89PNG\r\n\x1a\npayload", MediaType.IMAGE, ".png"),
        (b"RIFF1234WEBPpayload", MediaType.IMAGE, ".webp"),
        (b"\x00\x00\x00\x18ftypmp42payload", MediaType.VIDEO, ".mp4"),
    ],
)
def test_detect_media_uses_file_content(
    content: bytes, media_type: MediaType, extension: str
) -> None:
    detected = detect_media(content)

    assert detected.media_type == media_type
    assert detected.extension == extension


@pytest.mark.asyncio
async def test_upload_stores_random_name_with_detected_extension(tmp_path: Path) -> None:
    service = MediaService(tmp_path, "https://api.example.test/media/")

    uploaded = await service.upload(b"\x89PNG\r\n\x1a\npayload")

    assert uploaded.media_type == MediaType.IMAGE
    assert uploaded.url.startswith("https://api.example.test/media/")
    stored = await asyncio.to_thread(lambda: list(tmp_path.iterdir()))
    assert len(stored) == 1
    assert stored[0].suffix == ".png"


def test_unknown_file_content_is_rejected() -> None:
    with pytest.raises(UploadInvalidError, match="JPG, PNG, WebP, or MP4"):
        detect_media(b"not really an image.jpg")


@pytest.mark.asyncio
async def test_image_size_limit_is_enforced(tmp_path: Path) -> None:
    oversized = b"\xff\xd8\xff" + bytes(IMAGE_MAX_BYTES - 2) + b"\xff\xd9"

    with pytest.raises(UploadInvalidError, match="5 MB"):
        await MediaService(tmp_path, "http://test/media").upload(oversized)


@pytest.mark.asyncio
async def test_video_size_limit_is_enforced(tmp_path: Path) -> None:
    oversized = b"\x00\x00\x00\x18ftypmp42" + bytes(VIDEO_MAX_BYTES)

    with pytest.raises(UploadInvalidError, match="16 MB"):
        await MediaService(tmp_path, "http://test/media").upload(oversized)
