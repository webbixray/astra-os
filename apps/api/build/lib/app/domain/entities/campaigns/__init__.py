"""Campaign domain entities."""

from app.domain.entities.campaigns.campaign import Campaign


class CampaignStatus:
    """String-based status constants matching Campaign.VALID_STATUSES."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

    ALL = [DRAFT, PENDING_APPROVAL, ACTIVE, PAUSED, COMPLETED, ARCHIVED]

    def __iter__(self):
        return iter(self.ALL)


__all__ = ["Campaign", "CampaignStatus"]
