"""Tests for the /api/v1/campaigns endpoints."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def _make_campaign(**overrides) -> SimpleNamespace:
    defaults = dict(
        id="campaign-1",
        name="Q3 Enterprise Outbound",
        description="Target enterprise SaaS buyers",
        status="DRAFT",
        targetCriteria={"industry": "SaaS", "company_size": "201-1000"},
        aiPrompt="Find VP of Sales at mid-market SaaS companies",
        totalLeads=0,
        convertedLeads=0,
        userId="00000000-0000-0000-0000-000000000001",
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
        leads=[],
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


async def test_list_campaigns_returns_paginated_response(
    client: AsyncClient, mock_db: AsyncMock
):
    mock_db.campaign.count = AsyncMock(return_value=1)
    mock_db.campaign.find_many = AsyncMock(return_value=[_make_campaign()])

    response = await client.get(
        "/api/v1/campaigns", headers={"Authorization": "Bearer faketoken"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Q3 Enterprise Outbound"


async def test_create_campaign_success(client: AsyncClient, mock_db: AsyncMock):
    mock_db.campaign.create = AsyncMock(return_value=_make_campaign())

    payload = {
        "name": "Q3 Enterprise Outbound",
        "description": "Target enterprise SaaS buyers",
        "target_criteria": {"industry": "SaaS", "company_size": "201-1000"},
        "ai_prompt": "Find VP of Sales at mid-market SaaS companies",
    }

    response = await client.post(
        "/api/v1/campaigns",
        json=payload,
        headers={"Authorization": "Bearer faketoken"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["data"]["status"] == "DRAFT"


async def test_start_campaign_invalid_status_returns_400(
    client: AsyncClient, mock_db: AsyncMock
):
    mock_db.campaign.find_first = AsyncMock(
        return_value=_make_campaign(status="COMPLETED")
    )

    response = await client.post(
        "/api/v1/campaigns/campaign-1/start",
        headers={"Authorization": "Bearer faketoken"},
    )

    assert response.status_code == 400


async def test_get_campaign_analytics_with_no_leads(
    client: AsyncClient, mock_db: AsyncMock
):
    mock_db.campaign.find_first = AsyncMock(return_value=_make_campaign())
    mock_db.lead.find_many = AsyncMock(return_value=[])

    response = await client.get(
        "/api/v1/campaigns/campaign-1/analytics",
        headers={"Authorization": "Bearer faketoken"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total_leads"] == 0
    assert body["data"]["conversion_rate"] == 0.0
