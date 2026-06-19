from app.ai.services import ClaudeService, ActionPlanService
from app.ai.schemas import ActionPlanContext
from app.schemas.action_plan import ActionPlanResponse as APResponse, ActionStep, ResourceItem
from app.models.action_plan import UrgencyLevel
from app.models.user import Language
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

claude = ClaudeService()
action_plan_service = ActionPlanService()


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
) -> Dict[str, Any]:
    """Generate action plan using our new AI core and convert to API schema"""
    context = ActionPlanContext(
        state=state,
        county=county,
        urgency_days=urgency_days,
        income_monthly=income_monthly,
        household_size=household_size,
        situation_type=situation_type,
        has_received_notice=has_received_notice,
        language=language.value if hasattr(language, 'value') else str(language),
        prior_steps=str(prior_steps) if prior_steps else ""
    )

    plan = await claude.generate_action_plan(context)

    # Convert to API's expected format
    compatible_plan = {
        "urgency_level": plan.urgency_level.value if hasattr(plan.urgency_level, 'value') else str(plan.urgency_level),
        "urgency_reason": plan.urgency_reason,
        "action_steps": [
            ActionStep(
                step_number=step.step_number,
                title=step.title,
                description=step.description,
                deadline=step.deadline_description,
                contact=step.contact_name or "",
                responsible_party=step.responsible_party.value if hasattr(step.responsible_party, 'value') else str(step.responsible_party)
            ).model_dump()
            for step in plan.action_steps
        ],
        "resources": [
            ResourceItem(
                name=res.name,
                type=res.type.value if hasattr(res.type, 'value') else str(res.type),
                phone=res.phone or "",
                url=str(res.url) if res.url else "",
                eligibility_notes=res.eligibility_notes or "",
                distance_miles=0.0
            ).model_dump()
            for res in plan.resources
        ],
        "rights_summary": plan.rights_summary.headline,
        "documents_needed": [doc.document for doc in plan.documents_needed],
        "escalation_flag": plan.escalation_flag,
        "escalation_reason": plan.escalation_reason or "",
        "raw_claude_response": plan.model_dump_json()
    }

    return compatible_plan
