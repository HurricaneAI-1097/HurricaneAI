"""Tests for the /api/v1/leads endpoints."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def _make_lead(**overrides) -> SimpleNamespace:
    defaults = dict(
        id="lead-1",
        email="jane@acme.com",
        firstName="Jane",
        lastName="Doe",
        company="Acme Inc",
        title="VP Sales",
        phone=None,
        linkedinUrl=None,
        website=None,
        score=0,
        status="NEW",
        source="manual",
        enriched=False,
        enrichedAt=None,
        notes=None,
        tags=[],
        userId="00000000-0000-0000-0000-000000000001",
        campaignId=None,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
        enrichment=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


async def test_list_leads_returns_paginated_response(client: AsyncClient, mock_db: AsyncMock):
    mock_db.lead.count = AsyncMock(return_value=1)
    mock_db.lead.find_many = AsyncMock(return_value=[_make_lead()])

    response = await client.get(
        "/api/v1/leads", headers={"Authorization": "Bearer faketoken"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == "jane@acme.com"


async def test_get_lead_not_found_returns_404(client: AsyncClient, mock_db: AsyncMock):
    mock_db.lead.find_first = AsyncMock(return_value=None)

    response = await client.get(
        "/api/v1/leads/does-not-exist",
        headers={"Authorization": "Bearer faketoken"},
    )

    assert response.status_code == 404


async def test_create_lead_validation_error_on_bad_email(client: AsyncClient):
    payload = {
        "email": "not-an-email",
        "first_name": "Jane",
        "last_name": "Doe",
        "company": "Acme Inc",
        "title": "VP Sales",
    }

    response = await client.post(
        "/api/v1/leads",
        json=payload,
        headers={"Authorization": "Bearer faketoken"},
    )

    assert response.status_code == 422


async def test_delete_lead_soft_deletes(client: AsyncClient, mock_db: AsyncMock):
    mock_db.lead.find_first = AsyncMock(return_value=_make_lead())
    mock_db.lead.update = AsyncMock(return_value=_make_lead(isDeleted=True))

    response = await client.delete(
        "/api/v1/leads/lead-1",
        headers={"Authorization": "Bearer faketoken"},
    )

    assert response.status_code == 204
    mock_db.lead.update.assert_awaited_once()
