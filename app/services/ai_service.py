from anthropic import AsyncAnthropic
from app.config import settings
from app.services.rag_service import retrieve_relevant_docs
from app.schemas.action_plan import ActionPlanResponse, ActionStep, ResourceItem
from app.models.action_plan import UrgencyLevel
from app.models.user import Language
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """
You are a Housing Stability Navigator for the United States.
Your role is to help renters understand their options and take action early when facing housing instability.
You are NOT providing legal advice — you help users understand pathways and connect to resources.

Always:
1. Prioritize immediate safety first
2. Surface state-specific tenant rights
3. Provide concrete next steps with deadlines
4. Refer complex cases to local legal aid
5. Never give specific legal predictions or court outcomes
6. Respond in plain language at a 6th-grade reading level
7. If language = ES, respond entirely in Spanish

Respond ONLY in JSON, matching the EXACT schema provided below, no other text.
"""

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "urgency_level": {"type": "string", "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]},
        "urgency_reason": {"type": "string"},
        "action_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_number": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "deadline": {"type": "string"},
                    "contact": {"type": "string"},
                    "responsible_party": {"type": "string"}
                },
                "required": ["step_number", "title", "description", "deadline", "contact", "responsible_party"]
            }
        },
        "resources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["LEGAL_AID", "RENTAL_ASSISTANCE", "SHELTER", "FOOD_BANK", "MEDIATION"]},
                    "phone": {"type": "string"},
                    "url": {"type": "string"},
                    "eligibility_notes": {"type": "string"},
                    "distance_miles": {"type": "number"}
                },
                "required": ["name", "type", "phone", "url", "eligibility_notes", "distance_miles"]
            }
        },
        "rights_summary": {"type": "string"},
        "documents_needed": {"type": "array", "items": {"type": "string"}},
        "escalation_flag": {"type": "boolean"},
        "escalation_reason": {"type": "string"}
    },
    "required": [
        "urgency_level",
        "urgency_reason",
        "action_steps",
        "resources",
        "rights_summary",
        "documents_needed",
        "escalation_flag",
        "escalation_reason"
    ]
}


async def generate_action_plan(
    state: str,
    county: str,
    urgency_days: int,
    income_monthly: int,
    household_size: int,
    situation_type: str,
    has_received_notice: bool,
    language: Language = Language.EN,
    prior_steps: Optional[list] = None
) -> dict:
    relevant_docs = await retrieve_relevant_docs(
        query=f"eviction rights rental assistance {situation_type.lower().replace('_', ' ')}",
        state=state,
        situation_type=situation_type
    )
    rag_context = "\n\n".join(relevant_docs) if relevant_docs else "No specific state law data available."

    user_context = f"""
User Context:
- State/County: {state}, {county}
- Days until eviction: {urgency_days}
- Monthly Income: ${income_monthly}
- Household Size: {household_size}
- Situation Type: {situation_type}
- Received Notice: {has_received_notice}
- Language: {language}
- Prior Steps Taken: {prior_steps or "None"}

Relevant Legal/Resource Information:
{rag_context}

Remember: NO LEGAL ADVICE, ONLY PATHWAYS AND RESOURCES.
"""

    try:
        response = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_context}]
        )

        raw_text = response.content[0].text
        try:
            result = json.loads(raw_text)
            result["raw_claude_response"] = raw_text
            return result
        except json.JSONDecodeError:
            logger.error(f"Claude returned invalid JSON: {raw_text}")
            return _fallback_plan(state, situation_type, urgency_days)
    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        return _fallback_plan(state, situation_type, urgency_days)


def _fallback_plan(state: str, situation_type: str, urgency_days: int) -> dict:
    urgency = UrgencyLevel.HIGH if urgency_days < 14 else UrgencyLevel.MEDIUM
    if urgency_days <= 3:
        urgency = UrgencyLevel.CRITICAL

    return {
        "urgency_level": urgency.value,
        "urgency_reason": "Time-sensitive situation - please act quickly",
        "action_steps": [
            {
                "step_number": 1,
                "title": "Contact Legal Aid Immediately",
                "description": "Call your local legal aid society for free advice.",
                "deadline": "Within 24 hours",
                "contact": "Find local legal aid at LawHelp.org",
                "responsible_party": "User"
            },
            {
                "step_number": 2,
                "title": "Gather Documents",
                "description": "Collect lease, eviction notice, pay stubs, and ID.",
                "deadline": "Within 3 days",
                "contact": "N/A",
                "responsible_party": "User"
            }
        ],
        "resources": [
            {
                "name": "LawHelp.org",
                "type": "LEGAL_AID",
                "phone": "N/A",
                "url": "https://www.lawhelp.org",
                "eligibility_notes": "Free legal help for low-income individuals",
                "distance_miles": 0.0
            }
        ],
        "rights_summary": f"Tenants in {state} have rights. Contact legal aid immediately.",
        "documents_needed": ["Lease agreement", "Eviction notice", "Pay stubs", "Government-issued ID"],
        "escalation_flag": True,
        "escalation_reason": "Fallback plan activated - please connect to legal aid.",
        "raw_claude_response": "Fallback plan"
    }
