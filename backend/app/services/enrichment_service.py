"""Business logic for enriching leads with AI-derived and third-party data."""

import logging
from typing import Any, Optional

from fastapi import HTTPException, status
from prisma import Prisma

from app.ai.chains import build_lead_enrichment_chain, build_lead_scoring_chain

logger = logging.getLogger("app.services.enrichment_service")


class EnrichmentService:
    """Coordinates AI enrichment/scoring chains with persistence."""

    def __init__(self, db: Prisma):
        self.db = db

    async def enrich_lead(self, lead_id: str) -> Any:
        """Run the AI enrichment chain for a lead and persist the result."""
        lead = await self.db.lead.find_unique(where={"id": lead_id})
        if lead is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
            )

        chain = build_lead_enrichment_chain()
        result = await chain.ainvoke(
            {
                "first_name": lead.firstName,
                "last_name": lead.lastName,
                "company": lead.company,
                "title": lead.title,
                "email": lead.email,
            }
        )

        enrichment = await self.db.enrichment.upsert(
            where={"leadId": lead_id},
            data={
                "create": {
                    "leadId": lead_id,
                    "companyData": {
                        "industry": result.get("industry"),
                        "company_size": result.get("company_size"),
                    },
                    "aiSummary": result.get("summary"),
                    "aiScore": result.get("potential_fit_score"),
                },
                "update": {
                    "companyData": {
                        "industry": result.get("industry"),
                        "company_size": result.get("company_size"),
                    },
                    "aiSummary": result.get("summary"),
                    "aiScore": result.get("potential_fit_score"),
                },
            },
        )

        await self.db.lead.update(
            where={"id": lead_id},
            data={"enriched": True, "enrichedAt": __import__("datetime").datetime.utcnow()},
        )

        logger.info("Lead %s enriched successfully", lead_id)
        return enrichment

    async def score_lead(self, lead_id: str) -> int:
        """Run the AI scoring chain for a lead and persist the score."""
        lead = await self.db.lead.find_unique(where={"id": lead_id})
        if lead is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
            )

        chain = build_lead_scoring_chain()
        result = await chain.ainvoke(
            {
                "first_name": lead.firstName,
                "last_name": lead.lastName,
                "company": lead.company,
                "title": lead.title,
                "email": lead.email,
                "source": lead.source,
            }
        )

        score = int(result.get("score", 0))
        score = max(0, min(100, score))

        await self.db.lead.update(where={"id": lead_id}, data={"score": score})
        logger.info("Lead %s scored: %d", lead_id, score)
        return score
