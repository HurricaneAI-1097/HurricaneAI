"""Campaign CRUD, lifecycle, and analytics routes."""

import logging
from typing import Any, Dict

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, Query, status
from prisma import Prisma

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.schemas.campaign import (
    CampaignAnalytics,
    CampaignCreate,
    CampaignRead,
    CampaignUpdate,
    CampaignWithLeads,
)
from app.schemas.common import ApiResponse, PaginatedResponse
from app.services.campaign_service import CampaignService

logger = logging.getLogger("app.api.v1.campaigns")
settings = get_settings()

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


async def _get_arq_pool():
    return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))


@router.get("", response_model=PaginatedResponse[CampaignRead])
async def list_campaigns(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> PaginatedResponse[CampaignRead]:
    """List campaigns owned by the current user, most recent first."""
    service = CampaignService(db)
    campaigns, total = await service.list_campaigns(
        user_id=current_user["id"], page=page, page_size=page_size
    )
    items = [CampaignRead.model_validate(c) for c in campaigns]
    return PaginatedResponse.build(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ApiResponse[CampaignRead], status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[CampaignRead]:
    """Create a new campaign in DRAFT status with an AI targeting brief."""
    service = CampaignService(db)
    campaign = await service.create_campaign(payload, user_id=current_user["id"])
    return ApiResponse(data=CampaignRead.model_validate(campaign), message="Campaign created")


@router.get("/{campaign_id}", response_model=ApiResponse[CampaignWithLeads])
async def get_campaign(
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[CampaignWithLeads]:
    """Fetch a campaign along with its associated leads."""
    service = CampaignService(db)
    campaign = await service.get_campaign_with_leads(campaign_id, user_id=current_user["id"])

    data = CampaignWithLeads.model_validate(campaign)
    data.leads = [
        {
            "id": lead.id,
            "email": lead.email,
            "firstName": lead.firstName,
            "lastName": lead.lastName,
            "company": lead.company,
            "status": lead.status,
            "score": lead.score,
        }
        for lead in campaign.leads
    ]
    return ApiResponse(data=data)


@router.patch("/{campaign_id}", response_model=ApiResponse[CampaignRead])
async def update_campaign(
    campaign_id: str,
    payload: CampaignUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[CampaignRead]:
    """Update campaign fields and/or transition its status."""
    service = CampaignService(db)
    campaign = await service.update_campaign(
        campaign_id, user_id=current_user["id"], payload=payload
    )
    return ApiResponse(data=CampaignRead.model_validate(campaign), message="Campaign updated")


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> None:
    """Permanently delete a campaign (leads are un-linked, not deleted)."""
    service = CampaignService(db)
    await service.delete_campaign(campaign_id, user_id=current_user["id"])


@router.post("/{campaign_id}/start", response_model=ApiResponse[CampaignRead])
async def start_campaign(
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[CampaignRead]:
    """Activate a campaign and enqueue the AI lead-generation task."""
    service = CampaignService(db)
    campaign = await service.start_campaign(campaign_id, user_id=current_user["id"])

    pool = await _get_arq_pool()
    try:
        await pool.enqueue_job("process_campaign_task", campaign_id)
    finally:
        await pool.close()

    return ApiResponse(
        data=CampaignRead.model_validate(campaign),
        message="Campaign started; AI lead generation queued",
    )


@router.get("/{campaign_id}/analytics", response_model=ApiResponse[CampaignAnalytics])
async def get_campaign_analytics(
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[CampaignAnalytics]:
    """Return conversion-funnel statistics for a campaign."""
    service = CampaignService(db)
    analytics = await service.get_analytics(campaign_id, user_id=current_user["id"])
    return ApiResponse(data=analytics)
