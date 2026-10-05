"""Shared API dependencies for authentication and role access."""

from collections.abc import Awaitable, Callable
from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock, get_clock
from app.core.config import Settings, get_settings
from app.core.db import DatabaseResources, get_db
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.redis import get_redis
from app.models.enums import UserRole
from app.repositories.campaign import CampaignRepository
from app.repositories.content_series import ContentSeriesRepository
from app.repositories.donor import DonorRepository, SegmentRepository
from app.repositories.donor_batch import DonorBatchRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.user import UserRepository
from app.scheduler.factory import build_scheduler_tick
from app.scheduler.tick import SchedulerTick
from app.schemas.user import UserOut
from app.services.auth_service import INVALID_TOKEN_MESSAGE, AuthService
from app.services.batch_upload.preview_store import PreviewCache, PreviewStore
from app.services.batch_upload.query_service import DonorBatchQueryService
from app.services.batch_upload.service import BatchUploadService
from app.services.campaigns.query_service import CampaignQueryService
from app.services.campaigns.service import CampaignService
from app.services.content_series.access import ContentSeriesAccess
from app.services.content_series.query_service import ContentSeriesQueryService
from app.services.content_series.service import ContentSeriesService
from app.services.content_series.step_service import SeriesStepService
from app.services.demo_clock import DemoClockService
from app.services.events.base import EventPublisher
from app.services.events.redis import RedisEventPublisher
from app.services.media_service import MediaService
from app.services.user_service import UserService

bearer_scheme = HTTPBearer(auto_error=False)


def get_event_publisher(
    redis: Annotated[Redis, Depends(get_redis)],
    current_clock: Annotated[Clock, Depends(get_clock)],
) -> EventPublisher:
    """Return the application transport for committed domain changes."""
    return RedisEventPublisher(redis, current_clock)


def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    """Build the request-scoped authentication service."""
    return AuthService(
        UserRepository(db),
        jwt_secret=settings.jwt_secret,
        jwt_expires_minutes=settings.jwt_expires_minutes,
    )


def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """Build the request-scoped user lookup service."""
    return UserService(UserRepository(db))


def get_batch_upload_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_clock: Annotated[Clock, Depends(get_clock)],
) -> BatchUploadService:
    """Build the request-scoped donor batch upload service."""
    return BatchUploadService(
        db,
        DonorBatchRepository(db),
        DonorRepository(db),
        SegmentRepository(db),
        PreviewStore(cast(PreviewCache, redis), current_clock, settings.preview_ttl_minutes),
        current_clock,
        max_size_mb=settings.upload_max_mb,
        max_rows=settings.upload_max_rows,
    )


def get_donor_batch_query_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DonorBatchQueryService:
    """Build the request-scoped donor batch query service."""
    return DonorBatchQueryService(DonorBatchRepository(db), DonorRepository(db))


def get_content_series_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ContentSeriesService:
    """Build the request-scoped content-series mutation service."""
    repository = ContentSeriesRepository(db)
    return ContentSeriesService(ContentSeriesAccess(db, repository))


def get_series_step_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SeriesStepService:
    """Build the request-scoped series-step mutation service."""
    repository = ContentSeriesRepository(db)
    return SeriesStepService(ContentSeriesAccess(db, repository))


def get_content_series_query_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    current_clock: Annotated[Clock, Depends(get_clock)],
) -> ContentSeriesQueryService:
    """Build the request-scoped content-series query service."""
    return ContentSeriesQueryService(
        ContentSeriesRepository(db),
        DonorRepository(db),
        current_clock,
        settings.timezone_display,
    )


def get_campaign_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_clock: Annotated[Clock, Depends(get_clock)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
) -> CampaignService:
    """Build the request-scoped campaign mutation service."""
    return CampaignService(
        db,
        CampaignRepository(db),
        EnrollmentRepository(db),
        current_clock,
        publisher,
    )


def get_campaign_query_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CampaignQueryService:
    """Build the request-scoped campaign query service."""
    return CampaignQueryService(CampaignRepository(db), EnrollmentRepository(db))


def get_scheduler_tick(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    current_clock: Annotated[Clock, Depends(get_clock)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> SchedulerTick:
    """Build a tick against the application's shared database resources."""
    resources = cast(DatabaseResources, request.app.state.database)
    return build_scheduler_tick(
        resources.session_factory,
        settings,
        current_clock,
        RedisEventPublisher(redis, current_clock),
    )


def get_demo_clock_service(
    settings: Annotated[Settings, Depends(get_settings)],
    current_clock: Annotated[Clock, Depends(get_clock)],
    tick: Annotated[SchedulerTick, Depends(get_scheduler_tick)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> DemoClockService:
    """Build the request-scoped demo-clock service."""
    return DemoClockService(
        current_clock,
        tick,
        RedisEventPublisher(redis, current_clock),
        demo_mode=settings.demo_mode,
    )


def get_media_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> MediaService:
    """Build the configured media storage service."""
    return MediaService(settings.media_storage_dir, settings.media_public_url)


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    """Extract a bearer token before constructing database-backed dependencies."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError(INVALID_TOKEN_MESSAGE)
    return credentials.credentials


async def get_current_user(
    token: Annotated[str, Depends(get_bearer_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserOut:
    """Resolve one required bearer access token to an active user."""
    return await auth_service.get_current_user(token)


def require_role(*allowed_roles: UserRole) -> Callable[[UserOut], Awaitable[UserOut]]:
    """Create a dependency that permits only the listed current roles."""
    if not allowed_roles:
        raise ValueError("At least one role is required")
    allowed = frozenset(allowed_roles)

    async def role_dependency(
        current_user: Annotated[UserOut, Depends(get_current_user)],
    ) -> UserOut:
        if current_user.role not in allowed:
            raise ForbiddenError()
        return current_user

    return role_dependency
