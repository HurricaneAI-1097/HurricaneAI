"""Lead CRUD, bulk import, and enrichment-trigger routes."""

import logging
from typing import Any, Dict, Optional

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from prisma import Prisma

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.models.lead import LeadStatus
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.lead import (
    LeadBulkImportResult,
    LeadCreate,
    LeadRead,
    LeadUpdate,
)
from app.services.lead_service import LeadService

logger = logging.getLogger("app.api.v1.leads")
settings = get_settings()

router = APIRouter(prefix="/leads", tags=["leads"])


async def _get_arq_pool():
    return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))


@router.get("", response_model=PaginatedResponse[LeadRead])
async def list_leads(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[LeadStatus] = Query(default=None, alias="status"),
    campaign_id: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> PaginatedResponse[LeadRead]:
    """Return a paginated, filterable list of the current user's leads."""
    service = LeadService(db)
    leads, total = await service.list_leads(
        user_id=current_user["id"],
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        campaign_id=campaign_id,
        search=search,
    )
    items = [LeadRead.model_validate(lead) for lead in leads]
    return PaginatedResponse.build(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ApiResponse[LeadRead], status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[LeadRead]:
    """Create a new lead and enqueue a background enrichment task."""
    service = LeadService(db)
    lead = await service.create_lead(payload, user_id=current_user["id"])

    pool = await _get_arq_pool()
    try:
        await pool.enqueue_job("enrich_lead_task", lead.id)
    finally:
        await pool.close()

    return ApiResponse(data=LeadRead.model_validate(lead), message="Lead created")


@router.get("/{lead_id}", response_model=ApiResponse[LeadRead])
async def get_lead(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[LeadRead]:
    """Fetch a single lead, including its enrichment record if present."""
    service = LeadService(db)
    lead = await service.get_lead(lead_id, user_id=current_user["id"])
    return ApiResponse(data=LeadRead.model_validate(lead))


@router.patch("/{lead_id}", response_model=ApiResponse[LeadRead])
async def update_lead(
    lead_id: str,
    payload: LeadUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[LeadRead]:
    """Partially update a lead's fields or status."""
    service = LeadService(db)
    lead = await service.update_lead(lead_id, user_id=current_user["id"], payload=payload)
    return ApiResponse(data=LeadRead.model_validate(lead), message="Lead updated")


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> None:
    """Soft-delete a lead (marks `is_deleted = true`, retains the row)."""
    service = LeadService(db)
    await service.soft_delete_lead(lead_id, user_id=current_user["id"])


@router.post("/bulk-import", response_model=ApiResponse[LeadBulkImportResult])
async def bulk_import_leads(
    file: UploadFile = File(..., description="CSV file with lead rows"),
    campaign_id: Optional[str] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[LeadBulkImportResult]:
    """Bulk-create leads from an uploaded CSV file."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a .csv"
        )

    content = await file.read()
    service = LeadService(db)
    result = await service.bulk_import_from_csv(
        content, user_id=current_user["id"], campaign_id=campaign_id
    )
    return ApiResponse(
        data=result, message=f"Imported {result.created} of {result.total_rows} rows"
    )


@router.post("/{lead_id}/enrich", response_model=ApiResponse[dict])
async def trigger_enrichment(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Prisma = Depends(get_db),
) -> ApiResponse[dict]:
    """Manually (re-)trigger AI enrichment for a lead via the task queue."""
    service = LeadService(db)
    await service.get_lead(lead_id, user_id=current_user["id"])  # 404 guard

    pool = await _get_arq_pool()
    try:
        job = await pool.enqueue_job("enrich_lead_task", lead_id)
    finally:
        await pool.close()

    return ApiResponse(
        data={"job_id": job.job_id if job else None},
        message="Enrichment task queued",
    )
