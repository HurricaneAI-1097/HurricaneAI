"""LangChain chains powering lead scoring, enrichment, campaign generation,
and personalized outreach generation.

Each `build_*_chain()` factory returns a Runnable (prompt | llm | parser)
that can be awaited via `.ainvoke(...)` and always yields a plain Python
dict conforming to the JSON schema documented in `app.ai.prompts`.
"""

from functools import lru_cache

from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from app.ai.prompts import (
    CAMPAIGN_GENERATION_PROMPT,
    LEAD_ENRICHMENT_PROMPT,
    LEAD_SCORING_PROMPT,
    OUTREACH_EMAIL_PROMPT,
)
from app.config import get_settings

settings = get_settings()


@lru_cache
def get_llm(temperature: float | None = None) -> ChatOpenAI:
    """Return a cached ChatOpenAI client configured from settings."""
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=temperature if temperature is not None else settings.OPENAI_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
        model_kwargs={"response_format": {"type": "json_object"}},
    )


def build_lead_scoring_chain():
    """Chain: lead fields -> {score, reasoning}."""
    llm = get_llm(temperature=0.0)
    parser = JsonOutputParser()
    return LEAD_SCORING_PROMPT | llm | parser


def build_lead_enrichment_chain():
    """Chain: name/company/title/email -> structured enrichment payload."""
    llm = get_llm(temperature=0.3)
    parser = JsonOutputParser()
    return LEAD_ENRICHMENT_PROMPT | llm | parser


def build_campaign_generation_chain():
    """Chain: campaign criteria/brief -> list of ideal buyer personas."""
    llm = get_llm(temperature=0.5)
    parser = JsonOutputParser()
    return CAMPAIGN_GENERATION_PROMPT | llm | parser


def build_outreach_chain():
    """Chain: lead + campaign context -> personalized outreach email."""
    llm = get_llm(temperature=0.6)
    parser = JsonOutputParser()
    return OUTREACH_EMAIL_PROMPT | llm | parser
