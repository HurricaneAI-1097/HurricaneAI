"""Campaign domain enums (mirrors `Campaign` model in schema.prisma)."""

from enum import Enum


class CampaignStatus(str, Enum):
    """Lifecycle status of an outbound lead-generation campaign."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


CAMPAIGN_STATUS_TRANSITIONS: dict[CampaignStatus, set[CampaignStatus]] = {
    CampaignStatus.DRAFT: {CampaignStatus.ACTIVE},
    CampaignStatus.ACTIVE: {CampaignStatus.PAUSED, CampaignStatus.COMPLETED},
    CampaignStatus.PAUSED: {CampaignStatus.ACTIVE, CampaignStatus.COMPLETED},
    CampaignStatus.COMPLETED: set(),
}
