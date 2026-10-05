"""Build public follow-up event payloads."""

from app.models.follow_up import FollowUpItem


def follow_up_created_payload(item: FollowUpItem) -> dict[str, object]:
    """Return the documented follow-up list representation."""
    return {
        "id": str(item.id),
        "enrollment_id": str(item.enrollment_id),
        "type": item.type.value,
        "status": item.status.value,
        "priority": item.priority.value,
        "assigned_to_id": str(item.assigned_to_id) if item.assigned_to_id else None,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }
