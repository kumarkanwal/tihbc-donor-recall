"""Map campaign and enrollment query records to API schemas."""

from app.core.logging import mask_phone_number
from app.models.campaign import Enrollment
from app.models.enums import EnrollmentStatus, FollowUpStatus
from app.repositories.campaign import CampaignRecord, EnrollmentRecord
from app.schemas.campaign import (
    AppointmentSlotSummary,
    CampaignDetail,
    CampaignOut,
    EnrollmentDetail,
    EnrollmentDonorOut,
    EnrollmentOut,
    EnrollmentTimelineItem,
    FollowUpSummary,
    MessageTimelineEntry,
    NamedResourceSummary,
    ResponseTimelineEntry,
)
from app.schemas.donor_batch import UploadedBySummary


def campaign_out(record: CampaignRecord) -> CampaignOut:
    """Map a query-computed campaign summary."""
    campaign = record.campaign
    response_rate = (
        round(record.responded_count * 100 / record.enrollment_count, 1)
        if record.enrollment_count
        else 0.0
    )
    return CampaignOut(
        id=campaign.id,
        name=campaign.name,
        batch=NamedResourceSummary(id=campaign.batch_id, name=record.batch_name),
        primary_series=NamedResourceSummary(
            id=campaign.primary_series_id, name=record.primary_series_name
        ),
        secondary_series=NamedResourceSummary(
            id=campaign.secondary_series_id, name=record.secondary_series_name
        ),
        status=campaign.status,
        start_at=campaign.start_at,
        launched_at=campaign.launched_at,
        completed_at=campaign.completed_at,
        enrollment_count=record.enrollment_count,
        responded_count=record.responded_count,
        response_rate=response_rate,
        created_by=UploadedBySummary(
            id=record.created_by.id,
            full_name=record.created_by.full_name,
        ),
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


def campaign_detail(record: CampaignRecord, counts: dict[EnrollmentStatus, int]) -> CampaignDetail:
    """Add complete status counts to a campaign summary."""
    summary = campaign_out(record)
    return CampaignDetail(**summary.model_dump(), enrollment_counts=counts)


def enrollment_out(record: EnrollmentRecord, *, mask_phone: bool) -> EnrollmentOut:
    """Map one enrollment row, optionally masking its donor phone."""
    enrollment = record.enrollment
    phone = mask_phone_number(record.donor.phone_e164) if mask_phone else record.donor.phone_e164
    return EnrollmentOut(
        id=enrollment.id,
        campaign_id=enrollment.campaign_id,
        donor=EnrollmentDonorOut(
            id=record.donor.id,
            full_name=record.donor.full_name,
            phone_e164=phone,
            segment=record.segment_key,
            language=record.donor.language,
            city=record.donor.city,
            blood_group=record.donor.blood_group,
            last_donation_date=record.donor.last_donation_date,
        ),
        status=enrollment.status,
        current_series_kind=enrollment.current_series_kind,
        current_step_order=enrollment.current_step_order,
        next_action_at=enrollment.next_action_at,
        responded_at=enrollment.responded_at,
        decline_reason=enrollment.decline_reason,
        created_at=enrollment.created_at,
        updated_at=enrollment.updated_at,
    )


def enrollment_detail(enrollment: Enrollment) -> EnrollmentDetail:
    """Map a fully loaded enrollment with full donor phone and activity."""
    record = EnrollmentRecord(
        enrollment=enrollment,
        donor=enrollment.donor,
        segment_key=enrollment.donor.segment.key,
    )
    summary = enrollment_out(record, mask_phone=False)
    return EnrollmentDetail(
        **summary.model_dump(),
        campaign=NamedResourceSummary(
            id=enrollment.campaign.id,
            name=enrollment.campaign.name,
        ),
        timeline=_timeline(enrollment),
        follow_up=_follow_up(enrollment),
        appointment=(
            AppointmentSlotSummary(
                id=enrollment.appointment_slot.id,
                center_name=enrollment.appointment_slot.center_name,
                starts_at=enrollment.appointment_slot.starts_at,
            )
            if enrollment.appointment_slot is not None
            else None
        ),
    )


def _timeline(enrollment: Enrollment) -> list[EnrollmentTimelineItem]:
    items = [
        EnrollmentTimelineItem(
            id=message.id,
            type="message",
            created_at=message.created_at,
            message=MessageTimelineEntry(
                direction=message.direction,
                kind=message.kind,
                body=message.body,
                media_type=message.media_type,
                media_url=message.media_url,
                status=message.status,
                scheduled_at=message.scheduled_at,
                sent_at=message.sent_at,
                delivered_at=message.delivered_at,
                read_at=message.read_at,
            ),
        )
        for message in enrollment.messages
    ]
    items.extend(
        EnrollmentTimelineItem(
            id=response.id,
            type="response",
            created_at=response.created_at,
            response=ResponseTimelineEntry(
                intent=response.intent,
                source=response.source,
                detected_language=response.detected_language,
                requested_date=response.requested_date,
                decline_reason=response.decline_reason,
                confidence=response.confidence,
            ),
        )
        for response in enrollment.responses
    )
    return sorted(items, key=lambda item: (item.created_at, str(item.id)))


def _follow_up(enrollment: Enrollment) -> FollowUpSummary | None:
    if not enrollment.follow_up_items:
        return None
    ordered = sorted(
        enrollment.follow_up_items,
        key=lambda item: (item.created_at, item.id),
        reverse=True,
    )
    follow_up = next(
        (item for item in ordered if item.status != FollowUpStatus.DONE),
        ordered[0],
    )
    return FollowUpSummary(
        id=follow_up.id,
        type=follow_up.type,
        status=follow_up.status,
        priority=follow_up.priority,
        assigned_to_id=follow_up.assigned_to_id,
        created_at=follow_up.created_at,
        updated_at=follow_up.updated_at,
    )
