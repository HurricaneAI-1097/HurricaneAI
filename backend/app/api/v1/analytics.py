"""Account-wide analytics: cross-campaign lead funnel and performance stats."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from prisma import Prisma

from app.api.deps import get_current_user, get_db
from app.schemas.common import ApiResponse

logger = logging.getLogger("app.api.v1.analytics")

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=ApiResponse[dict])
async def get_overview(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[dict]:
    """Return account-wide lead/campaign KPIs for the dashboard overview."""
    user_id = current_user["id"]

    total_leads = await db.lead.count(where={"userId": user_id, "isDeleted": False})
    converted_leads = await db.lead.count(
        where={"userId": user_id, "isDeleted": False, "status": "CONVERTED"}
    )
    qualified_leads = await db.lead.count(
        where={"userId": user_id, "isDeleted": False, "status": "QUALIFIED"}
    )
    active_campaigns = await db.campaign.count(
        where={"userId": user_id, "status": "ACTIVE"}
    )
    total_campaigns = await db.campaign.count(where={"userId": user_id})

    conversion_rate = (converted_leads / total_leads * 100) if total_leads else 0.0

    return ApiResponse(
        data={
            "total_leads": total_leads,
            "qualified_leads": qualified_leads,
            "converted_leads": converted_leads,
            "conversion_rate": round(conversion_rate, 2),
            "active_campaigns": active_campaigns,
            "total_campaigns": total_campaigns,
        }
    )


@router.get("/leads-by-status", response_model=ApiResponse[dict])
async def get_leads_by_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[dict]:
    """Return a breakdown of lead counts grouped by status."""
    user_id = current_user["id"]
    statuses = ["NEW", "CONTACTED", "QUALIFIED", "CONVERTED", "LOST"]

    counts = {}
    for status_value in statuses:
        counts[status_value] = await db.lead.count(
            where={"userId": user_id, "isDeleted": False, "status": status_value}
        )

    return ApiResponse(data=counts)


@router.get("/leads-by-source", response_model=ApiResponse[dict])
async def get_leads_by_source(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[dict]:
    """Return lead counts grouped by acquisition source."""
    user_id = current_user["id"]
    leads = await db.lead.find_many(
        where={"userId": user_id, "isDeleted": False}
    )

    counts: Dict[str, int] = {}
    for lead in leads:
        counts[lead.source] = counts.get(lead.source, 0) + 1

    return ApiResponse(data=counts)
