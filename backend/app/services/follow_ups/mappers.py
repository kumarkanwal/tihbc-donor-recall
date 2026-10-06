"""Map loaded follow-up aggregates to public schemas."""

from app.models.enums import MessageDirection
from app.models.follow_up import FollowUpItem
from app.schemas.follow_up import (
    FollowUpActivityOut,
    FollowUpAppointment,
    FollowUpAssignee,
    FollowUpDetail,
    FollowUpDonorDetail,
    FollowUpDonorList,
    FollowUpEnrollment,
    FollowUpListItem,
    LatestReply,
    LatestResponse,
    NamedResource,
)


def follow_up_list_item(item: FollowUpItem) -> FollowUpListItem:
    """Return the compact queue representation."""
    enrollment = item.enrollment
    donor = enrollment.donor
    latest_reply = max(
        (
            message
            for message in enrollment.messages
            if message.direction == MessageDirection.INBOUND
        ),
        key=lambda message: (message.created_at, message.id),
        default=None,
    )
    return FollowUpListItem(
        id=item.id,
        enrollment_id=item.enrollment_id,
        donor=FollowUpDonorList(id=donor.id, name=donor.full_name, phone=donor.phone_e164),
        campaign=NamedResource(id=enrollment.campaign.id, name=enrollment.campaign.name),
        type=item.type,
        status=item.status,
        priority=item.priority,
        latest_reply=(
            LatestReply(body=latest_reply.body, created_at=latest_reply.created_at)
            if latest_reply
            else None
        ),
        assigned_to=(
            FollowUpAssignee(id=item.assigned_to.id, full_name=item.assigned_to.full_name)
            if item.assigned_to
            else None
        ),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def follow_up_detail(item: FollowUpItem) -> FollowUpDetail:
    """Return the complete coordinator context."""
    base = follow_up_list_item(item)
    enrollment = item.enrollment
    donor = enrollment.donor
    response = max(enrollment.responses, key=lambda value: value.created_at, default=None)
    appointment = enrollment.appointment_slot
    return FollowUpDetail(
        **base.model_dump(exclude={"donor"}),
        donor=FollowUpDonorDetail(
            id=donor.id,
            name=donor.full_name,
            phone=donor.phone_e164,
            language=donor.language,
            segment=donor.segment.label,
            city=donor.city,
            blood_group=donor.blood_group,
            last_donation_date=donor.last_donation_date,
        ),
        enrollment=FollowUpEnrollment(id=enrollment.id, status=enrollment.status.value),
        latest_response=(
            LatestResponse(
                intent=response.intent.value,
                requested_date=response.requested_date,
                decline_reason=response.decline_reason.value if response.decline_reason else None,
                confidence=float(response.confidence),
                raw_text=response.message.body,
                created_at=response.created_at,
            )
            if response
            else None
        ),
        appointment=(
            FollowUpAppointment(
                center_name=appointment.center_name, slot_start=appointment.starts_at
            )
            if appointment
            else None
        ),
        activities=[
            FollowUpActivityOut(
                id=activity.id,
                action=activity.action,
                note=activity.note,
                user_name=activity.user.full_name if activity.user else None,
                created_at=activity.created_at,
            )
            for activity in sorted(
                item.activities, key=lambda value: value.created_at, reverse=True
            )
        ],
    )
