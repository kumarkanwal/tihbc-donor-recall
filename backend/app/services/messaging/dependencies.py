"""Composition helpers for messaging services outside HTTP requests."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.config import Settings
from app.messaging.factory import create_messaging_provider
from app.repositories.appointment import AppointmentRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.message import MessageRepository
from app.services.appointments.service import AppointmentService
from app.services.events.logging import LoggingEventPublisher
from app.services.messaging.delivery import DeliveryProgressionService
from app.services.messaging.service import MessagingService


def build_messaging_service(
    session: AsyncSession,
    settings: Settings,
    current_clock: Clock,
) -> MessagingService:
    """Build the configured step-sending service."""
    return MessagingService(
        session,
        EnrollmentRepository(session),
        MessageRepository(session),
        AppointmentService(AppointmentRepository(session), settings.timezone_display),
        create_messaging_provider(settings.messaging_provider),
        LoggingEventPublisher(),
        current_clock,
        settings.timezone_display,
    )


def build_delivery_service(
    session: AsyncSession,
    settings: Settings,
    current_clock: Clock,
) -> DeliveryProgressionService:
    """Build the configured simulator-delivery service."""
    return DeliveryProgressionService(
        session,
        MessageRepository(session),
        create_messaging_provider(settings.messaging_provider),
        LoggingEventPublisher(),
        current_clock,
        delivery_delay_seconds=settings.sim_delivery_delay_seconds,
        auto_read_delay_seconds=settings.sim_auto_read_delay_seconds,
        auto_read_rate=settings.sim_auto_read_rate,
    )
