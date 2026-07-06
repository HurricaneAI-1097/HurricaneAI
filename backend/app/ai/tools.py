"""LangChain tools exposing lead/campaign data operations to agentic chains.

These tools wrap the Prisma-backed services so that future LangChain agents
(e.g. an autonomous research agent) can look up or mutate lead data via a
standard tool-calling interface.
"""

import json
import logging
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.database import get_client

logger = logging.getLogger("app.ai.tools")


class LeadLookupInput(BaseModel):
    lead_id: str = Field(description="UUID of the lead to look up")


async def _lookup_lead(lead_id: str) -> str:
    """Fetch a lead by id and return a JSON string summary."""
    db = get_client()
    lead = await db.lead.find_unique(where={"id": lead_id}, include={"enrichment": True})
    if lead is None:
        return json.dumps({"error": "Lead not found"})
    return json.dumps(
        {
            "id": lead.id,
            "name": f"{lead.firstName} {lead.lastName}",
            "company": lead.company,
            "title": lead.title,
            "status": lead.status,
            "score": lead.score,
            "enriched": lead.enriched,
        }
    )


class CompanyDomainInput(BaseModel):
    company_name: str = Field(description="Company name to infer a likely domain for")


async def _infer_company_domain(company_name: str) -> str:
    """Best-effort heuristic to guess a company's primary domain name.

    This is a lightweight offline heuristic intended as a placeholder for a
    real data-provider integration (e.g. Clearbit, Apollo). It normalizes the
    company name into a plausible `.com` slug.
    """
    slug = "".join(ch.lower() for ch in company_name if ch.isalnum())
    if not slug:
        return json.dumps({"error": "Could not derive domain from company name"})
    return json.dumps({"company_name": company_name, "guessed_domain": f"{slug}.com"})


class SearchLeadsInput(BaseModel):
    query: str = Field(description="Free-text search across name/company/email")
    user_id: str = Field(description="Owner user id to scope the search to")
    limit: int = Field(default=5, ge=1, le=25)


async def _search_leads(query: str, user_id: str, limit: int = 5) -> str:
    """Search leads belonging to a user by free-text query."""
    db = get_client()
    leads = await db.lead.find_many(
        where={
            "userId": user_id,
            "isDeleted": False,
            "OR": [
                {"email": {"contains": query, "mode": "insensitive"}},
                {"company": {"contains": query, "mode": "insensitive"}},
                {"firstName": {"contains": query, "mode": "insensitive"}},
                {"lastName": {"contains": query, "mode": "insensitive"}},
            ],
        },
        take=limit,
    )
    return json.dumps(
        [
            {
                "id": lead.id,
                "name": f"{lead.firstName} {lead.lastName}",
                "company": lead.company,
                "status": lead.status,
            }
            for lead in leads
        ]
    )


def get_lead_lookup_tool() -> StructuredTool:
    return StructuredTool.from_function(
        coroutine=_lookup_lead,
        name="lookup_lead",
        description="Look up a single lead's details by its UUID.",
        args_schema=LeadLookupInput,
    )


def get_company_domain_tool() -> StructuredTool:
    return StructuredTool.from_function(
        coroutine=_infer_company_domain,
        name="infer_company_domain",
        description="Guess a company's primary web domain from its name.",
        args_schema=CompanyDomainInput,
    )


def get_search_leads_tool() -> StructuredTool:
    return StructuredTool.from_function(
        coroutine=_search_leads,
        name="search_leads",
        description="Search a user's leads by free-text query across name/company/email.",
        args_schema=SearchLeadsInput,
    )


def get_all_tools() -> list[StructuredTool]:
    """Return the full toolkit for use by agentic LangChain runnables."""
    return [
        get_lead_lookup_tool(),
        get_company_domain_tool(),
        get_search_leads_tool(),
    ]
