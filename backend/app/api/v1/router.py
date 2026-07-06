"""Aggregates all v1 API routers into a single APIRouter."""

from fastapi import APIRouter

from app.api.v1 import analytics, campaigns, enrichment, leads

api_router = APIRouter()

api_router.include_router(leads.router)
api_router.include_router(campaigns.router)
api_router.include_router(enrichment.router)
api_router.include_router(analytics.router)
