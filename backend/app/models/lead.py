"""Lead domain enums and helper constants (mirrors `Lead` model in schema.prisma)."""

from enum import Enum


class LeadStatus(str, Enum):
    """Lifecycle status of a lead within the pipeline."""

    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    CONVERTED = "CONVERTED"
    LOST = "LOST"


# Valid forward-moving transitions used for lightweight state-machine checks
# in `lead_service.py`. Not exhaustive/enforced everywhere, but prevents
# obviously invalid transitions (e.g. CONVERTED -> NEW).
LEAD_STATUS_TRANSITIONS: dict[LeadStatus, set[LeadStatus]] = {
    LeadStatus.NEW: {LeadStatus.CONTACTED, LeadStatus.LOST},
    LeadStatus.CONTACTED: {LeadStatus.QUALIFIED, LeadStatus.LOST},
    LeadStatus.QUALIFIED: {LeadStatus.CONVERTED, LeadStatus.LOST},
    LeadStatus.CONVERTED: set(),
    LeadStatus.LOST: {LeadStatus.NEW},
}

MIN_LEAD_SCORE = 0
MAX_LEAD_SCORE = 100
