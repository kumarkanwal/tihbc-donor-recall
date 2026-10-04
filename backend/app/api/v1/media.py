"""Validated content-series media uploads."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import get_media_service, require_role
from app.models.enums import UserRole
from app.schemas.media import MediaUploadOut
from app.schemas.user import UserOut
from app.services.media_service import MAX_MEDIA_BYTES, MediaService

router = APIRouter(prefix="/media", tags=["Media"])
admin_access = require_role(UserRole.ADMIN)


@router.post(
    "",
    response_model=MediaUploadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload content-series media",
)
async def upload_media(
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[MediaService, Depends(get_media_service)],
    file: Annotated[UploadFile, File(description="JPG, PNG, WebP, or MP4 media")],
) -> MediaUploadOut:
    """Validate media bytes and store the asset under a random filename."""
    del current_user
    content = await file.read(MAX_MEDIA_BYTES + 1)
    return await service.upload(content)
