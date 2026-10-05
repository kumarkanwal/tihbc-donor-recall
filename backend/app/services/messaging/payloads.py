"""Build event payloads for messaging state changes."""

from app.models.campaign import Enrollment
from app.models.message import Message


def message_created_payload(message: Message) -> dict[str, object]:
    """Return the simulator-facing outbound message payload."""
    return {
        "id": str(message.id),
        "donor_id": str(message.donor_id),
        "direction": message.direction.value,
        "kind": message.kind.value,
        "body": message.body,
        "media_type": message.media_type.value,
        "media_url": message.media_url,
        "buttons": _public_buttons(message.buttons),
        "button_id": message.button_id,
        "reply_to_message_id": (
            str(message.reply_to_message_id) if message.reply_to_message_id else None
        ),
        "status": message.status.value,
        "created_at": message.created_at.isoformat(),
        "sent_at": message.sent_at.isoformat() if message.sent_at else None,
        "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
        "read_at": message.read_at.isoformat() if message.read_at else None,
    }


def _public_buttons(
    buttons: list[dict[str, object]] | None,
) -> list[dict[str, object]] | None:
    if buttons is None:
        return None
    return [{"id": button["id"], "label": button["label"]} for button in buttons]


def message_status_payload(message: Message) -> dict[str, object]:
    """Return the documented message-status event payload."""
    return {
        "id": str(message.id),
        "donor_id": str(message.donor_id),
        "status": message.status.value,
        "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
        "read_at": message.read_at.isoformat() if message.read_at else None,
        "failed_reason": message.failed_reason,
    }


def enrollment_payload(enrollment: Enrollment) -> dict[str, object]:
    """Return the documented enrollment-update event payload."""
    return {
        "id": str(enrollment.id),
        "campaign_id": str(enrollment.campaign_id),
        "donor_id": str(enrollment.donor_id),
        "status": enrollment.status.value,
        "current_series_kind": (
            enrollment.current_series_kind.value if enrollment.current_series_kind else None
        ),
        "current_step_order": enrollment.current_step_order,
    }
