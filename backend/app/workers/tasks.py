"""ARQ background tasks: lead enrichment, scoring, and campaign processing.

Run the worker with:
    arq app.workers.tasks.WorkerSettings
"""

import logging
from typing import Any, Dict

from arq.connections import RedisSettings
from prisma import Prisma

from app.ai.chains import build_campaign_generation_chain
from app.config import get_settings
from app.services.enrichment_service import EnrichmentService

logger = logging.getLogger("app.workers.tasks")
settings = get_settings()


async def startup(ctx: Dict[str, Any]) -> None:
    """ARQ worker startup hook: open a dedicated Prisma connection."""
    db = Prisma(auto_register=True)
    await db.connect()
    ctx["db"] = db
    logger.info("ARQ worker started, DB connected")


async def shutdown(ctx: Dict[str, Any]) -> None:
    """ARQ worker shutdown hook: close the Prisma connection."""
    db: Prisma = ctx["db"]
    if db.is_connected():
        await db.disconnect()
    logger.info("ARQ worker shut down, DB disconnected")


async def enrich_lead_task(ctx: Dict[str, Any], lead_id: str) -> Dict[str, Any]:
    """Fetch a lead, run the AI enrichment chain, and persist the result."""
    db: Prisma = ctx["db"]
    logger.info("Starting enrichment for lead %s", lead_id)

    service = EnrichmentService(db)
    enrichment = await service.enrich_lead(lead_id)

    logger.info("Completed enrichment for lead %s", lead_id)
    return {"lead_id": lead_id, "enrichment_id": enrichment.id}


async def score_lead_task(ctx: Dict[str, Any], lead_id: str) -> Dict[str, Any]:
    """Fetch a lead, run the AI scoring chain, and persist the resulting score."""
    db: Prisma = ctx["db"]
    logger.info("Starting scoring for lead %s", lead_id)

    service = EnrichmentService(db)
    score = await service.score_lead(lead_id)

    logger.info("Completed scoring for lead %s -> %d", lead_id, score)
    return {"lead_id": lead_id, "score": score}


async def process_campaign_task(ctx: Dict[str, Any], campaign_id: str) -> Dict[str, Any]:
    """Run the campaign persona-generation chain and create seed leads.

    For each generated persona, we create a placeholder lead record that
    downstream enrichment/scoring tasks can further flesh out. In a full
    implementation this step would call out to a lead-sourcing data
    provider using the generated personas as search criteria.
    """
    db: Prisma = ctx["db"]
    logger.info("Processing campaign %s", campaign_id)

    campaign = await db.campaign.find_unique(where={"id": campaign_id})
    if campaign is None:
        logger.error("Campaign %s not found", campaign_id)
        return {"campaign_id": campaign_id, "error": "not_found"}

    chain = build_campaign_generation_chain()
    result = await chain.ainvoke(
        {
            "campaign_name": campaign.name,
            "target_criteria": campaign.targetCriteria,
            "ai_prompt": campaign.aiPrompt,
        }
    )

    personas = result.get("personas", [])
    created_count = 0

    for idx, persona in enumerate(personas):
        placeholder_email = f"persona-{idx}-{campaign_id[:8]}@placeholder.leads"
        await db.lead.create(
            data={
                "email": placeholder_email,
                "firstName": "Prospective",
                "lastName": persona.get("title", "Lead")[:50],
                "company": f"Target: {persona.get('industry', 'Unknown')}",
                "title": persona.get("title", "Unknown"),
                "source": "ai_campaign_generation",
                "notes": persona.get("value_proposition"),
                "tags": persona.get("pain_points", [])[:5],
                "userId": campaign.userId,
                "campaignId": campaign_id,
            }
        )
        created_count += 1

    await db.campaign.update(
        where={"id": campaign_id},
        data={"totalLeads": {"increment": created_count}},
    )

    logger.info(
        "Campaign %s processed: %d persona-based leads created",
        campaign_id,
        created_count,
    )
    return {"campaign_id": campaign_id, "leads_created": created_count}


class WorkerSettings:
    """ARQ worker configuration entrypoint."""

    functions = [enrich_lead_task, score_lead_task, process_campaign_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 300
