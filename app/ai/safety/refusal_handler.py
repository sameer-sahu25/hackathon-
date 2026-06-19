import json
import logging
from typing import Any, Type
from pydantic import BaseModel
from app.ai.schemas.action_plan import (
    ActionPlanResponse,
    ActionStep,
    Resource,
    RightsSummary,
    DocumentNeeded,
    UrgencyLevel,
    UrgencyColor,
    ResourceType,
    ResponsibleParty
)
from datetime import datetime, UTC
from app.ai.safety.disclaimer import get_disclaimer

logger = logging.getLogger(__name__)


class RefusalHandler:
    """Handle invalid, unsafe, or failed AI responses"""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def _validate_json(self, text: str) -> dict | None:
        """Attempt to parse JSON from Claude response"""
        try:
            # Try to extract JSON from the response (in case of extra text)
            text = text.strip()
            if text.startswith("```json"):
                text = text.split("```json", 1)[1].rsplit("```", 1)[0]
            elif text.startswith("```"):
                text = text.split("```", 1)[1].rsplit("```", 1)[0]
            
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {str(e)}")
            return None

    def _validate_pydantic(self, data: dict, model: Type[BaseModel]) -> BaseModel | None:
        """Validate JSON against Pydantic model"""
        try:
            return model(**data)
        except Exception as e:
            logger.warning(f"Pydantic validation error: {str(e)}")
            return None

    def get_fallback_response(self) -> ActionPlanResponse:
        """Get a safe fallback response when all else fails"""
        return ActionPlanResponse(
            urgency_level=UrgencyLevel.CRITICAL,
            urgency_reason="We're having trouble generating a personalized plan right now. Please contact emergency services immediately.",
            urgency_color=UrgencyColor.RED,
            action_steps=[
                ActionStep(
                    step_number=1,
                    title="Call 211 Immediately",
                    description="211 is a free, 24/7 hotline that can connect you with emergency housing assistance, legal aid, and other resources in your area.",
                    deadline_description="Right now",
                    deadline_hours=1,
                    contact_name="211 Hotline",
                    contact_phone="211",
                    contact_url=None,
                    responsible_party=ResponsibleParty.RENTER,
                    is_critical=True,
                    estimated_time_minutes=5
                )
            ],
            resources=[
                Resource(
                    name="211 Emergency Hotline",
                    type=ResourceType.HOTLINE,
                    description="24/7 free and confidential service for housing, food, and emergency assistance",
                    phone="211",
                    url=None,
                    hours="24/7",
                    eligibility_notes="Everyone eligible",
                    is_free=True,
                    priority=1
                ),
                Resource(
                    name="Legal Services Corporation",
                    type=ResourceType.LEGAL_AID,
                    description="Find free legal aid in your area for housing issues",
                    phone=None,
                    url=None,
                    hours="Mon-Fri 9AM-5PM",
                    eligibility_notes="Low-income individuals and families",
                    is_free=True,
                    priority=2
                )
            ],
            rights_summary=RightsSummary(
                headline="You have rights as a tenant",
                notice_requirement="Varies by state - contact legal aid for details",
                can_be_evicted_for=["Non-payment of rent", "Lease violations"],
                cannot_be_evicted_for=["Retaliation", "Discrimination", "Reporting health/safety issues"],
                key_protections=["Right to receive proper eviction notice", "Right to a court hearing"],
                rent_control_applies=False,
                just_cause_required=False
            ),
            documents_needed=[
                DocumentNeeded(
                    document="Lease agreement",
                    why_needed="Proves your tenancy and its terms",
                    where_to_get="Your landlord or your own records",
                    is_critical=True
                ),
                DocumentNeeded(
                    document="Eviction notice (if received)",
                    why_needed="Important for your legal case",
                    where_to_get="The notice you received",
                    is_critical=True
                ),
                DocumentNeeded(
                    document="Proof of income",
                    why_needed="May be needed for assistance programs",
                    where_to_get="Pay stubs, bank statements",
                    is_critical=False
                )
            ],
            escalation_flag=True,
            escalation_reason="Fallback plan activated - immediate assistance needed",
            escalation_contact="211",
            disclaimer=get_disclaimer("EN"),
            estimated_resolution_days=30,
            confidence_score=0.5,
            language="EN",
            generated_at=datetime.now(UTC)
        )

    async def handle_response(
        self,
        raw_response: str,
        model: Type[BaseModel],
        retry_callback=None
    ) -> BaseModel:
        """
        Handle AI response with retries and fallback
        """
        for attempt in range(self.max_retries):
            json_data = self._validate_json(raw_response)
            if json_data:
                validated = self._validate_pydantic(json_data, model)
                if validated:
                    return validated

            if retry_callback and attempt < self.max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                raw_response = await retry_callback()

        logger.error(f"All {self.max_retries} attempts failed, returning fallback")
        if model == ActionPlanResponse:
            return self.get_fallback_response()
        raise ValueError("Failed to get valid response from AI")
