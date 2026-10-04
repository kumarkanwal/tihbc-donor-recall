"""Single campaign status-transition policy."""

from app.core.errors import InvalidStateTransitionError
from app.models.campaign import Campaign
from app.models.enums import CampaignStatus

ALLOWED_CAMPAIGN_TRANSITIONS: dict[CampaignStatus, frozenset[CampaignStatus]] = {
    CampaignStatus.DRAFT: frozenset({CampaignStatus.SCHEDULED, CampaignStatus.RUNNING}),
    CampaignStatus.SCHEDULED: frozenset({CampaignStatus.RUNNING}),
    CampaignStatus.RUNNING: frozenset({CampaignStatus.PAUSED, CampaignStatus.COMPLETED}),
    CampaignStatus.PAUSED: frozenset({CampaignStatus.RUNNING}),
    CampaignStatus.COMPLETED: frozenset(),
}


def validate_campaign_transition(current: CampaignStatus, target: CampaignStatus) -> None:
    """Validate one campaign transition without changing state."""
    if target not in ALLOWED_CAMPAIGN_TRANSITIONS[current]:
        raise InvalidStateTransitionError(
            f"Campaign cannot transition from {current.value} to {target.value}",
            {"from": current.value, "to": target.value},
        )


def transition_campaign(campaign: Campaign, target: CampaignStatus) -> None:
    """Apply one allowed campaign transition or raise a domain error."""
    validate_campaign_transition(campaign.status, target)
    campaign.status = target


def require_campaign_status(campaign: Campaign, required: CampaignStatus, action: str) -> None:
    """Require one status for a non-transition campaign action."""
    if campaign.status == required:
        return
    raise InvalidStateTransitionError(
        f"Campaign must be {required.value} to {action}",
        {"status": campaign.status.value, "required": required.value},
    )
