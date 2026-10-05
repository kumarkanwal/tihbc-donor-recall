"""Request-scoped composition for simulator query and write services."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_event_publisher
from app.core.clock import Clock, get_clock
from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.messaging.factory import create_messaging_provider
from app.repositories.appointment import AppointmentRepository
from app.repositories.donor import DonorRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.follow_up import FollowUpRepository
from app.repositories.response import DonorResponseRepository
from app.repositories.simulator_conversations import ConversationRepository
from app.repositories.simulator_messages import SimulatorMessageRepository
from app.services.appointments.service import AppointmentService
from app.services.events.base import EventPublisher
from app.services.replies.flow import ReplyFlow
from app.services.reply_service import ReplyService
from app.services.simulator.query import SimulatorQueryService
from app.services.simulator.receipts import SimulatorReceiptService


def get_simulator_query_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SimulatorQueryService:
    """Build thread and cursor queries."""
    return SimulatorQueryService(
        DonorRepository(db), ConversationRepository(db), SimulatorMessageRepository(db)
    )


def get_simulator_receipt_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    current_clock: Annotated[Clock, Depends(get_clock)],
) -> SimulatorReceiptService:
    """Build delivered-to-read transitions."""
    return SimulatorReceiptService(
        db, DonorRepository(db), SimulatorMessageRepository(db), publisher, current_clock
    )


def get_simulator_reply_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    current_clock: Annotated[Clock, Depends(get_clock)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReplyService:
    """Build deterministic transactional reply handling."""
    appointments = AppointmentService(
        AppointmentRepository(db), current_clock, settings.timezone_display
    )
    return ReplyService(
        db,
        DonorRepository(db),
        SimulatorMessageRepository(db),
        EnrollmentRepository(db),
        ReplyFlow(
            appointments,
            FollowUpRepository(db),
            DonorResponseRepository(db),
            settings.timezone_display,
        ),
        create_messaging_provider(settings.messaging_provider),
        publisher,
        current_clock,
        settings.timezone_display,
        typing_seconds=settings.sim_typing_seconds,
        confidence_threshold=settings.agent_confidence_threshold or 0.7,
    )
