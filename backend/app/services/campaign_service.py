"""Business logic for campaigns: CRUD, lifecycle transitions, and analytics."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from prisma import Prisma

from app.models.campaign import CAMPAIGN_STATUS_TRANSITIONS, CampaignStatus
from app.schemas.campaign import CampaignAnalytics, CampaignCreate, CampaignUpdate

logger = logging.getLogger("app.services.campaign_service")


class CampaignService:
    """Encapsulates all Campaign-related data access and domain rules."""

    def __init__(self, db: Prisma):
        self.db = db

    async def list_campaigns(
        self, user_id: str, page: int, page_size: int
    ) -> Tuple[List[Any], int]:
        where = {"userId": user_id}
        total = await self.db.campaign.count(where=where)
        campaigns = await self.db.campaign.find_many(
            where=where,
            skip=(page - 1) * page_size,
            take=page_size,
            order={"createdAt": "desc"},
        )
        return campaigns, total

    async def get_campaign(self, campaign_id: str, user_id: str) -> Any:
        campaign = await self.db.campaign.find_first(
            where={"id": campaign_id, "userId": user_id}
        )
        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            )
        return campaign

    async def get_campaign_with_leads(self, campaign_id: str, user_id: str) -> Any:
        campaign = await self.db.campaign.find_first(
            where={"id": campaign_id, "userId": user_id},
            include={"leads": True},
        )
        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            )
        return campaign

    async def create_campaign(self, payload: CampaignCreate, user_id: str) -> Any:
        return await self.db.campaign.create(
            data={
                "name": payload.name,
                "description": payload.description,
                "targetCriteria": payload.target_criteria,
                "aiPrompt": payload.ai_prompt,
                "userId": user_id,
            }
        )

    async def update_campaign(
        self, campaign_id: str, user_id: str, payload: CampaignUpdate
    ) -> Any:
        existing = await self.get_campaign(campaign_id, user_id)

        update_data: Dict[str, Any] = {}
        payload_dict = payload.model_dump(exclude_unset=True)

        field_map = {
            "name": "name",
            "description": "description",
            "target_criteria": "targetCriteria",
            "ai_prompt": "aiPrompt",
        }
        for field, prisma_field in field_map.items():
            if field in payload_dict:
                update_data[prisma_field] = payload_dict[field]

        if "status" in payload_dict and payload_dict["status"] is not None:
            new_status = CampaignStatus(payload_dict["status"])
            current_status = CampaignStatus(existing.status)
            allowed = CAMPAIGN_STATUS_TRANSITIONS.get(current_status, set())
            if new_status != current_status and new_status not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status transition: {current_status} -> {new_status}",
                )
            update_data["status"] = new_status.value

        if not update_data:
            return existing

        return await self.db.campaign.update(
            where={"id": campaign_id}, data=update_data
        )

    async def delete_campaign(self, campaign_id: str, user_id: str) -> None:
        await self.get_campaign(campaign_id, user_id)
        await self.db.campaign.delete(where={"id": campaign_id})

    async def start_campaign(self, campaign_id: str, user_id: str) -> Any:
        """Transition a DRAFT/PAUSED campaign to ACTIVE and enqueue generation."""
        campaign = await self.get_campaign(campaign_id, user_id)
        current_status = CampaignStatus(campaign.status)

        if current_status not in (CampaignStatus.DRAFT, CampaignStatus.PAUSED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start a campaign in status {current_status}",
            )

        updated = await self.db.campaign.update(
            where={"id": campaign_id}, data={"status": CampaignStatus.ACTIVE.value}
        )
        return updated

    async def get_analytics(self, campaign_id: str, user_id: str) -> CampaignAnalytics:
        campaign = await self.get_campaign(campaign_id, user_id)

        leads = await self.db.lead.find_many(
            where={"campaignId": campaign_id, "isDeleted": False}
        )

        total = len(leads)
        counts = {"NEW": 0, "CONTACTED": 0, "QUALIFIED": 0, "CONVERTED": 0, "LOST": 0}
        score_sum = 0
        for lead in leads:
            counts[lead.status] = counts.get(lead.status, 0) + 1
            score_sum += lead.score

        conversion_rate = (counts["CONVERTED"] / total * 100) if total else 0.0
        average_score = (score_sum / total) if total else 0.0

        return CampaignAnalytics(
            campaign_id=campaign_id,
            total_leads=total,
            new_count=counts["NEW"],
            contacted_count=counts["CONTACTED"],
            qualified_count=counts["QUALIFIED"],
            converted_count=counts["CONVERTED"],
            lost_count=counts["LOST"],
            conversion_rate=round(conversion_rate, 2),
            average_score=round(average_score, 2),
        )
