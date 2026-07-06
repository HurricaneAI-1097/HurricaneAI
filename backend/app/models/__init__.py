"""Domain model enums and constants mirroring the Prisma schema.

The actual database models/tables are defined in `prisma/schema.prisma` and
accessed at runtime through the generated Prisma Client Python (`prisma.models`).
The plain Python enums here are re-exported for use in FastAPI schemas,
services, and AI chains without requiring the generated client to be present
(e.g. during static analysis, linting, or before `prisma generate` has run).
"""

from app.models.lead import LeadStatus
from app.models.campaign import CampaignStatus
from app.models.user import UserRole

__all__ = ["LeadStatus", "CampaignStatus", "UserRole"]
