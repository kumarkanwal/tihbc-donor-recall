"""Unauthenticated liveness and dependency readiness probes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.redis import get_redis

router = APIRouter(prefix="/health", tags=["health"])


class LiveResponse(BaseModel):
    """Liveness probe payload."""

    status: Literal["ok"]


class ReadyResponse(BaseModel):
    """Successful readiness probe payload."""

    status: Literal["ready"]
    checks: dict[str, Literal["ok"]]


async def _database_is_ready(db: AsyncSession) -> bool:
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        return False
    return True


async def _redis_is_ready(redis: Redis) -> bool:
    try:
        return bool(await redis.ping())
    except Exception:
        return False


@router.get(
    "/live",
    response_model=LiveResponse,
    summary="Check API process liveness",
)
async def live() -> LiveResponse:
    """Return success whenever the API process can answer requests."""
    return LiveResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={503: {"description": "A required dependency is unavailable"}},
    summary="Check database and Redis readiness",
)
async def ready(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> ReadyResponse | JSONResponse:
    """Report whether both required data services are reachable."""
    database_ready = await _database_is_ready(db)
    redis_ready = await _redis_is_ready(redis)
    failed = [
        dependency
        for dependency, is_ready in (("database", database_ready), ("redis", redis_ready))
        if not is_ready
    ]
    if failed:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "details": {"failed": failed},
            },
        )
    return ReadyResponse(status="ready", checks={"database": "ok", "redis": "ok"})
