"""Standalone enrichment routes for manual scoring/enrichment operations
and inspecting enrichment records outside the leads router.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from prisma import Prisma

from app.api.deps import get_current_user, get_db
from app.schemas.common import ApiResponse
from app.schemas.lead import EnrichmentRead
from app.services.enrichment_service import EnrichmentService
from app.services.lead_service import LeadService

logger = logging.getLogger("app.api.v1.enrichment")

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.get("/{lead_id}", response_model=ApiResponse[EnrichmentRead])
async def get_enrichment(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[EnrichmentRead]:
    """Fetch the enrichment record for a given lead, if it has been enriched."""
    lead_service = LeadService(db)
    lead = await lead_service.get_lead(lead_id, user_id=current_user["id"])

    if lead.enrichment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead has not been enriched yet",
        )

    return ApiResponse(data=EnrichmentRead.model_validate(lead.enrichment))


@router.post("/{lead_id}/score", response_model=ApiResponse[dict])
async def score_lead_now(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[dict]:
    """Synchronously run the AI scoring chain for a lead (blocking call)."""
    lead_service = LeadService(db)
    await lead_service.get_lead(lead_id, user_id=current_user["id"])  # 404 guard

    enrichment_service = EnrichmentService(db)
    score = await enrichment_service.score_lead(lead_id)

    return ApiResponse(data={"lead_id": lead_id, "score": score}, message="Lead scored")


@router.post("/{lead_id}/run", response_model=ApiResponse[EnrichmentRead])
async def run_enrichment_now(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[EnrichmentRead]:
    """Synchronously run the AI enrichment chain for a lead (blocking call)."""
    lead_service = LeadService(db)
    await lead_service.get_lead(lead_id, user_id=current_user["id"])  # 404 guard

    enrichment_service = EnrichmentService(db)
    enrichment = await enrichment_service.enrich_lead(lead_id)

    return ApiResponse(
        data=EnrichmentRead.model_validate(enrichment), message="Lead enriched"
    )
