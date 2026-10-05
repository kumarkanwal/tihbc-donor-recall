"""FastAPI application factory."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.api.websocket import router as websocket_router
from app.core.clock import clock
from app.core.config import Settings, get_settings
from app.core.db import create_database_resources
from app.core.errors import register_exception_handlers
from app.core.logging import RequestIdMiddleware, configure_logging
from app.core.redis import create_redis_client
from app.repositories.demo_clock import DatabaseClockPersistence
from app.ws.manager import ConnectionManager
from app.ws.subscriber import EventDispatcher, RedisEventSubscriber


def _lifespan(
    settings: Settings,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.database = create_database_resources(settings.database_url)
        app.state.redis = create_redis_client(settings.redis_url)
        app.state.ws_manager = ConnectionManager()
        subscriber = RedisEventSubscriber(
            app.state.redis,
            EventDispatcher(app.state.ws_manager),
        )
        try:
            await clock.initialize(DatabaseClockPersistence(app.state.database.session_factory))
            await subscriber.start()
            yield
        finally:
            await subscriber.stop()
            await app.state.ws_manager.shutdown()
            await app.state.redis.aclose()
            await app.state.database.engine.dispose()

    return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    application = FastAPI(
        title="TIHBC Donor Recall API",
        lifespan=_lifespan(resolved_settings),
    )
    application.state.settings = resolved_settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)
    application.mount(
        "/media",
        StaticFiles(directory=resolved_settings.media_storage_dir, check_dir=False),
        name="media",
    )
    application.include_router(health_router)
    application.include_router(websocket_router)
    application.include_router(v1_router, prefix=resolved_settings.api_base_path)
    return application


app = create_app()
