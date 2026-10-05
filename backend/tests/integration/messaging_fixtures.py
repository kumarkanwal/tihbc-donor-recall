"""PostgreSQL fixture builders and test doubles for messaging flows."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.messaging.base import MessagingProvider, OutboundButton, ProviderSendResult
from app.models.campaign import AppointmentSlot, Campaign, Enrollment
from app.models.enums import (
    CampaignStatus,
    EnrollmentStatus,
    LanguageCode,
    MediaType,
    MessageCategory,
    MessageStatus,
    SeriesKind,
)
from app.models.series import ContentSeries, SeriesStep, SeriesStepContent
from app.services.appointments.centers import KORANGI_CENTER
from app.services.appointments.service import AppointmentService, default_appointment_start
from tests.integration.campaign_fixtures import CampaignFixture, add_campaign_fixture


@dataclass(frozen=True)
class MessagingFixture:
    """Persisted enrollment, series steps, and default slot."""

    campaign_fixture: CampaignFixture
    campaign: Campaign
    enrollment: Enrollment
    primary_steps: tuple[SeriesStep, SeriesStep]
    secondary_step: SeriesStep
    default_slot: AppointmentSlot


class FixedClock(Clock):
    """Clock returning one mutable test-controlled timestamp."""

    def __init__(self, value: datetime) -> None:
        super().__init__()
        self.value = value

    def now(self) -> datetime:
        return self.value


@dataclass
class RecordingProvider(MessagingProvider):
    """Record provider sends and delivery reports."""

    sends: list[tuple[str, UUID]] = field(default_factory=list)
    status_reports: list[tuple[str, MessageStatus]] = field(default_factory=list)

    async def send_template_message(
        self,
        *,
        message_id: UUID,
        recipient: str,
        body: str,
        media_type: MediaType,
        media_url: str | None,
    ) -> ProviderSendResult:
        del recipient, body, media_type, media_url
        return self._record("template", message_id)

    async def send_text_message(
        self,
        *,
        message_id: UUID,
        recipient: str,
        body: str,
    ) -> ProviderSendResult:
        del recipient, body
        return self._record("text", message_id)

    async def send_interactive_message(
        self,
        *,
        message_id: UUID,
        recipient: str,
        body: str,
        buttons: tuple[OutboundButton, ...],
        media_type: MediaType,
        media_url: str | None,
    ) -> ProviderSendResult:
        del recipient, body, buttons, media_type, media_url
        return self._record("interactive", message_id)

    async def report_status_update(
        self,
        *,
        provider_message_id: str,
        status: MessageStatus,
    ) -> None:
        self.status_reports.append((provider_message_id, status))

    def _record(self, kind: str, message_id: UUID) -> ProviderSendResult:
        self.sends.append((kind, message_id))
        return ProviderSendResult(provider_message_id=f"test-{message_id}")


class RecordingPublisher:
    """Record events and verify no transaction remains open at publication."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.events: list[tuple[str, Mapping[str, object]]] = []

    async def publish(self, event_type: str, payload: Mapping[str, object]) -> None:
        assert not self._session.in_transaction()
        self.events.append((event_type, payload))


class UnavailableAppointmentService(AppointmentService):
    """Return no slot to exercise the non-blocking send fallback."""

    def __init__(self) -> None:
        pass

    async def book_default(self, enrollment: Enrollment) -> None:
        del enrollment
        return None


async def add_messaging_fixture(
    session: AsyncSession,
    now: datetime,
    *,
    language: LanguageCode = LanguageCode.EN,
    reachable: bool = True,
    read_receipts: bool = True,
) -> MessagingFixture:
    """Create one running campaign with ordered bilingual series steps."""
    base = await add_campaign_fixture(session, donor_languages=(language,))
    donor = base.donors[0]
    donor.sim_reachable = reachable
    donor.sim_read_receipts = read_receipts
    donor.city = "Karachi"
    primary_steps = (
        _step(
            base.primary,
            1,
            0,
            "Hello {{donor_name}} at {{center_name}} on {{appointment_date}}",
            "سلام {{donor_name}}، {{center_name}}، {{appointment_date}}",
            buttons=True,
        ),
        _step(
            base.primary,
            2,
            3,
            "Primary reminder for {{donor_name}}",
            "{{donor_name}} کے لیے بنیادی یاددہانی",
        ),
    )
    secondary_step = _step(
        base.secondary,
        1,
        0,
        "Final follow-up for {{donor_name}} at {{center_name}} on {{appointment_date}}",
        "{{donor_name}}، {{center_name}}، {{appointment_date}}",
    )
    campaign = Campaign(
        name="Messaging Campaign",
        batch=base.batch,
        primary_series=base.primary,
        secondary_series=base.secondary,
        status=CampaignStatus.RUNNING,
        start_at=now,
        launched_at=now,
        created_by=base.user,
    )
    enrollment = Enrollment(
        campaign=campaign,
        donor=donor,
        status=EnrollmentStatus.PENDING,
        current_series_kind=SeriesKind.PRIMARY,
        current_step_order=None,
        next_action_at=now,
    )
    default_slot = AppointmentSlot(
        center_name=KORANGI_CENTER,
        starts_at=default_appointment_start(now, ZoneInfo("Asia/Karachi")),
        capacity=4,
        booked_count=0,
    )
    session.add_all((*primary_steps, secondary_step, campaign, enrollment, default_slot))
    await session.flush()
    return MessagingFixture(
        campaign_fixture=base,
        campaign=campaign,
        enrollment=enrollment,
        primary_steps=primary_steps,
        secondary_step=secondary_step,
        default_slot=default_slot,
    )


def _step(
    series: ContentSeries,
    order: int,
    delay_days: int,
    english: str,
    urdu: str,
    *,
    buttons: bool = False,
) -> SeriesStep:
    button_data: list[dict[str, object]] = []
    if buttons:
        button_data = [
            {
                "id": "btn_confirm",
                "intent": "confirm",
                "labels": {"en": "Confirm", "ur": "تصدیق کریں"},
            }
        ]
    return SeriesStep(
        series=series,
        step_order=order,
        delay_days=delay_days,
        category=MessageCategory.UTILITY,
        media_type=MediaType.NONE,
        buttons=button_data,
        contents=[
            SeriesStepContent(language=LanguageCode.EN, body=english),
            SeriesStepContent(language=LanguageCode.UR, body=urdu),
        ],
    )
