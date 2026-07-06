"""Prompt templates used by the LangChain chains in `app.ai.chains`."""

from langchain.prompts import PromptTemplate

# ---------------------------------------------------------------------------
# Lead scoring
# ---------------------------------------------------------------------------
LEAD_SCORING_PROMPT = PromptTemplate(
    input_variables=["first_name", "last_name", "company", "title", "email", "source"],
    template="""You are an expert B2B sales development representative who
scores inbound and sourced leads for sales-readiness.

Evaluate the following lead and assign a score from 0 to 100, where:
- 0-20: Poor fit, unlikely to convert
- 21-50: Weak fit, needs significant nurturing
- 51-75: Good fit, worth prioritizing for outreach
- 76-100: Excellent fit, high-intent decision maker

Lead details:
- Name: {first_name} {last_name}
- Company: {company}
- Title: {title}
- Email: {email}
- Source: {source}

Consider factors such as: seniority implied by the job title, whether the
email domain matches the company (suggesting a verified corporate lead),
and how the lead source typically correlates with intent (e.g. demo request
vs. cold list).

Respond ONLY with a JSON object matching this exact schema:
{{
  "score": <integer 0-100>,
  "reasoning": "<concise 2-3 sentence explanation of the score>"
}}
""",
)

# ---------------------------------------------------------------------------
# Lead enrichment
# ---------------------------------------------------------------------------
LEAD_ENRICHMENT_PROMPT = PromptTemplate(
    input_variables=["first_name", "last_name", "company", "title", "email"],
    template="""You are a B2B data enrichment analyst. Given limited
information about a lead, infer likely firmographic and professional
context using general industry knowledge. Be conservative and note
uncertainty where relevant, but always return your best estimate for
every field.

Lead details:
- Name: {first_name} {last_name}
- Company: {company}
- Title: {title}
- Email: {email}

Respond ONLY with a JSON object matching this exact schema:
{{
  "summary": "<2-3 sentence professional summary of this person/role>",
  "industry": "<best-guess industry for the company>",
  "company_size": "<one of: '1-10', '11-50', '51-200', '201-1000', '1000+', 'unknown'>",
  "potential_fit_score": <integer 0-100 estimating ICP fit>,
  "seniority": "<one of: 'entry', 'mid', 'senior', 'executive', 'unknown'>"
}}
""",
)

# ---------------------------------------------------------------------------
# Campaign / persona generation
# ---------------------------------------------------------------------------
CAMPAIGN_GENERATION_PROMPT = PromptTemplate(
    input_variables=["campaign_name", "target_criteria", "ai_prompt"],
    template="""You are a go-to-market strategist designing an ideal
customer profile (ICP) and target persona list for a new outbound lead
generation campaign.

Campaign name: {campaign_name}
Structured targeting criteria (JSON): {target_criteria}
Campaign brief: {ai_prompt}

Generate a list of 5 distinct, realistic buyer personas that fit this
campaign's targeting criteria and brief. Each persona should represent a
plausible job title/company profile combination worth prospecting.

Respond ONLY with a JSON object matching this exact schema:
{{
  "personas": [
    {{
      "title": "<job title>",
      "seniority": "<entry|mid|senior|executive>",
      "company_size_range": "<e.g. '51-200'>",
      "industry": "<likely industry>",
      "pain_points": ["<pain point 1>", "<pain point 2>"],
      "value_proposition": "<one sentence on why this persona would care>"
    }}
  ]
}}
""",
)

# ---------------------------------------------------------------------------
# Outreach email generation
# ---------------------------------------------------------------------------
OUTREACH_EMAIL_PROMPT = PromptTemplate(
    input_variables=[
        "first_name",
        "last_name",
        "company",
        "title",
        "campaign_name",
        "campaign_brief",
        "sender_name",
    ],
    template="""You are an SDR writing a highly personalized, concise
first-touch cold outreach email. Avoid generic filler, avoid being overly
salesy, and keep the tone conversational and human.

Recipient:
- Name: {first_name} {last_name}
- Title: {title}
- Company: {company}

Campaign context: {campaign_name}
Campaign brief / value proposition: {campaign_brief}

Sender name: {sender_name}

Write a short outreach email (under 120 words) with a clear, low-friction
call to action (e.g. asking for 15 minutes, not demanding a meeting).

Respond ONLY with a JSON object matching this exact schema:
{{
  "subject": "<compelling, non-clickbait subject line, under 60 chars>",
  "body": "<plain-text email body, use \\n for line breaks>",
  "call_to_action": "<the specific CTA used in the email>"
}}
""",
)
