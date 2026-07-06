"""Pydantic schemas for Campaign resources."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.campaign import CampaignStatus


class CampaignBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    target_criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured targeting criteria, e.g. industry, company size, geography",
    )
    ai_prompt: str = Field(
        min_length=1,
        description="Natural-language brief describing the ideal customer profile",
    )


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    target_criteria: Optional[Dict[str, Any]] = None
    ai_prompt: Optional[str] = None


class CampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    status: CampaignStatus
    target_criteria: Dict[str, Any] = Field(validation_alias="targetCriteria")
    ai_prompt: str = Field(validation_alias="aiPrompt")
    total_leads: int = Field(validation_alias="totalLeads")
    converted_leads: int = Field(validation_alias="convertedLeads")
    user_id: str = Field(validation_alias="userId")
    created_at: datetime = Field(validation_alias="createdAt")
    updated_at: datetime = Field(validation_alias="updatedAt")


class CampaignAnalytics(BaseModel):
    """Conversion funnel / performance stats for a single campaign."""

    campaign_id: str
    total_leads: int
    new_count: int
    contacted_count: int
    qualified_count: int
    converted_count: int
    lost_count: int
    conversion_rate: float
    average_score: float


class CampaignWithLeads(CampaignRead):
    """Campaign detail response including nested leads."""

    leads: List[dict] = Field(default_factory=list)
