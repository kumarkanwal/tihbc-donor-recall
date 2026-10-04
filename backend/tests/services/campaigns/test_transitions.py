"""Tests for the complete campaign state-transition matrix."""

from uuid import uuid4

import pytest

from app.core.clock import clock
from app.core.errors import InvalidStateTransitionError
from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.services.campaigns.transitions import (
    ALLOWED_CAMPAIGN_TRANSITIONS,
    transition_campaign,
)


@pytest.mark.parametrize(
    ("current", "target"),
    [(current, target) for current in CampaignStatus for target in CampaignStatus],
)
def test_campaign_transition_matrix(
    current: CampaignStatus,
    target: CampaignStatus,
) -> None:
    campaign = _campaign(current)

    if target in ALLOWED_CAMPAIGN_TRANSITIONS[current]:
        transition_campaign(campaign, target)
        assert campaign.status == target
        return

    with pytest.raises(InvalidStateTransitionError) as error:
        transition_campaign(campaign, target)

    assert campaign.status == current
    assert error.value.details == {"from": current.value, "to": target.value}


def _campaign(status: CampaignStatus) -> Campaign:
    return Campaign(
        name="Transition Test",
        batch_id=uuid4(),
        primary_series_id=uuid4(),
        secondary_series_id=uuid4(),
        status=status,
        start_at=clock.now(),
        created_by_id=uuid4(),
    )
