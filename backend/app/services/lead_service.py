"""Business logic for creating, querying, and mutating leads."""

import csv
import io
import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from prisma import Prisma

from app.models.lead import LEAD_STATUS_TRANSITIONS, LeadStatus
from app.schemas.lead import LeadBulkImportResult, LeadCreate, LeadUpdate

logger = logging.getLogger("app.services.lead_service")

REQUIRED_CSV_COLUMNS = {"email", "first_name", "last_name", "company", "title"}


class LeadService:
    """Encapsulates all Lead-related data access and domain rules."""

    def __init__(self, db: Prisma):
        self.db = db

    async def list_leads(
        self,
        user_id: str,
        page: int,
        page_size: int,
        status_filter: Optional[LeadStatus] = None,
        campaign_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Any], int]:
        """Return a page of leads for a user, applying optional filters."""
        where: Dict[str, Any] = {"userId": user_id, "isDeleted": False}

        if status_filter is not None:
            where["status"] = status_filter.value
        if campaign_id is not None:
            where["campaignId"] = campaign_id
        if search:
            where["OR"] = [
                {"email": {"contains": search, "mode": "insensitive"}},
                {"firstName": {"contains": search, "mode": "insensitive"}},
                {"lastName": {"contains": search, "mode": "insensitive"}},
                {"company": {"contains": search, "mode": "insensitive"}},
            ]

        total = await self.db.lead.count(where=where)
        leads = await self.db.lead.find_many(
            where=where,
            skip=(page - 1) * page_size,
            take=page_size,
            order={"createdAt": "desc"},
            include={"enrichment": True},
        )
        return leads, total

    async def get_lead(self, lead_id: str, user_id: str) -> Any:
        lead = await self.db.lead.find_first(
            where={"id": lead_id, "userId": user_id, "isDeleted": False},
            include={"enrichment": True},
        )
        if lead is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
            )
        return lead

    async def create_lead(self, payload: LeadCreate, user_id: str) -> Any:
        data = {
            "email": payload.email,
            "firstName": payload.first_name,
            "lastName": payload.last_name,
            "company": payload.company,
            "title": payload.title,
            "phone": payload.phone,
            "linkedinUrl": payload.linkedin_url,
            "website": payload.website,
            "source": payload.source,
            "tags": payload.tags,
            "notes": payload.notes,
            "userId": user_id,
        }
        if payload.campaign_id:
            data["campaignId"] = payload.campaign_id

        lead = await self.db.lead.create(data=data)

        if payload.campaign_id:
            await self.db.campaign.update(
                where={"id": payload.campaign_id},
                data={"totalLeads": {"increment": 1}},
            )

        return lead

    async def update_lead(
        self, lead_id: str, user_id: str, payload: LeadUpdate
    ) -> Any:
        existing = await self.get_lead(lead_id, user_id)

        update_data: Dict[str, Any] = {}
        field_map = {
            "email": "email",
            "first_name": "firstName",
            "last_name": "lastName",
            "company": "company",
            "title": "title",
            "phone": "phone",
            "linkedin_url": "linkedinUrl",
            "website": "website",
            "notes": "notes",
            "tags": "tags",
            "campaign_id": "campaignId",
            "score": "score",
        }
        payload_dict = payload.model_dump(exclude_unset=True)

        for field, prisma_field in field_map.items():
            if field in payload_dict:
                update_data[prisma_field] = payload_dict[field]

        if "status" in payload_dict and payload_dict["status"] is not None:
            new_status = LeadStatus(payload_dict["status"])
            current_status = LeadStatus(existing.status)
            allowed = LEAD_STATUS_TRANSITIONS.get(current_status, set())
            if new_status != current_status and new_status not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Invalid status transition: {current_status} -> {new_status}"
                    ),
                )
            update_data["status"] = new_status.value

        if not update_data:
            return existing

        return await self.db.lead.update(where={"id": lead_id}, data=update_data)

    async def soft_delete_lead(self, lead_id: str, user_id: str) -> None:
        await self.get_lead(lead_id, user_id)
        await self.db.lead.update(
            where={"id": lead_id}, data={"isDeleted": True}
        )

    async def bulk_import_from_csv(
        self, file_bytes: bytes, user_id: str, campaign_id: Optional[str] = None
    ) -> LeadBulkImportResult:
        """Parse a CSV file and bulk-create leads, skipping invalid rows."""
        text_stream = io.StringIO(file_bytes.decode("utf-8-sig"))
        reader = csv.DictReader(text_stream)

        if reader.fieldnames is None or not REQUIRED_CSV_COLUMNS.issubset(
            {f.strip().lower() for f in reader.fieldnames}
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "CSV must include columns: "
                    + ", ".join(sorted(REQUIRED_CSV_COLUMNS))
                ),
            )

        created = 0
        skipped = 0
        errors: List[str] = []
        rows_to_create: List[Dict[str, Any]] = []
        total_rows = 0

        for idx, row in enumerate(reader, start=2):  # header is row 1
            total_rows += 1
            normalized = {k.strip().lower(): (v or "").strip() for k, v in row.items()}

            if not normalized.get("email") or not normalized.get("company"):
                skipped += 1
                errors.append(f"Row {idx}: missing required email/company")
                continue

            rows_to_create.append(
                {
                    "email": normalized["email"],
                    "firstName": normalized.get("first_name", ""),
                    "lastName": normalized.get("last_name", ""),
                    "company": normalized["company"],
                    "title": normalized.get("title", ""),
                    "phone": normalized.get("phone") or None,
                    "linkedinUrl": normalized.get("linkedin_url") or None,
                    "website": normalized.get("website") or None,
                    "source": "csv_import",
                    "userId": user_id,
                    "campaignId": campaign_id,
                }
            )

        for row_data in rows_to_create:
            try:
                await self.db.lead.create(data=row_data)
                created += 1
            except Exception as exc:  # noqa: BLE001 - surface row-level errors
                skipped += 1
                errors.append(f"{row_data.get('email')}: {exc}")

        if campaign_id and created:
            await self.db.campaign.update(
                where={"id": campaign_id},
                data={"totalLeads": {"increment": created}},
            )

        return LeadBulkImportResult(
            total_rows=total_rows, created=created, skipped=skipped, errors=errors
        )
