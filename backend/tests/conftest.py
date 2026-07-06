"""Shared pytest fixtures: test client, auth headers, and mocked dependencies."""

import os
from typing import Any, AsyncGenerator, Dict
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.api.deps import get_current_user, get_db  # noqa: E402
from app.main import app  # noqa: E402

FAKE_USER: Dict[str, Any] = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "test@example.com",
    "name": "Test User",
    "role": "USER",
}


async def _override_get_current_user() -> Dict[str, Any]:
    return FAKE_USER


@pytest.fixture
def mock_db() -> AsyncMock:
    """A fully mocked Prisma client for isolated unit tests."""
    return AsyncMock()


@pytest_asyncio.fixture
async def client(mock_db: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    """An HTTPX AsyncClient wired to the FastAPI app with mocked auth/db."""

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
