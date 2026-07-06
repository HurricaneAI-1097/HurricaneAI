"""Pydantic schemas for Lead resources."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.lead import LeadStatus


class EnrichmentRead(BaseModel):
    """Read-only representation of a Lead's enrichment record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    lead_id: str = Field(validation_alias="leadId")
    linkedin_data: Optional[dict] = Field(default=None, validation_alias="linkedinData")
    company_data: Optional[dict] = Field(default=None, validation_alias="companyData")
    email_verified: bool = Field(default=False, validation_alias="emailVerified")
    phone_verified: bool = Field(default=False, validation_alias="phoneVerified")
    ai_summary: Optional[str] = Field(default=None, validation_alias="aiSummary")
    ai_score: Optional[int] = Field(default=None, validation_alias="aiScore")
    created_at: datetime = Field(validation_alias="createdAt")
    updated_at: datetime = Field(validation_alias="updatedAt")


class LeadBase(BaseModel):
    """Fields shared by create/update payloads."""

    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    company: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    source: str = Field(default="manual", max_length=100)
    tags: List[str] = Field(default_factory=list)
    campaign_id: Optional[str] = None


class LeadCreate(LeadBase):
    """Payload for creating a single lead."""

    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    """Partial update payload (PATCH) — all fields optional."""

    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    status: Optional[LeadStatus] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    campaign_id: Optional[str] = None


class LeadRead(BaseModel):
    """Full read representation of a Lead."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    first_name: str = Field(validation_alias="firstName")
    last_name: str = Field(validation_alias="lastName")
    company: str
    title: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = Field(default=None, validation_alias="linkedinUrl")
    website: Optional[str] = None
    score: int
    status: LeadStatus
    source: str
    enriched: bool
    enriched_at: Optional[datetime] = Field(default=None, validation_alias="enrichedAt")
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    user_id: str = Field(validation_alias="userId")
    campaign_id: Optional[str] = Field(default=None, validation_alias="campaignId")
    created_at: datetime = Field(validation_alias="createdAt")
    updated_at: datetime = Field(validation_alias="updatedAt")
    enrichment: Optional[EnrichmentRead] = None


class LeadBulkImportResult(BaseModel):
    """Result summary returned from the bulk CSV import endpoint."""

    total_rows: int
    created: int
    skipped: int
    errors: List[str] = Field(default_factory=list)
