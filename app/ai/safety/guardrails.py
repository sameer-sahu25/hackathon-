import re
import phonenumbers
from typing import List
from app.ai.schemas.action_plan import (
    ActionPlanResponse,
    ActionStep,
    Resource,
    ResourceType,
    UrgencyLevel
)
import logging

logger = logging.getLogger(__name__)

FORBIDDEN_PHRASES = [
    ("you will win", "you may have legal options"),
    ("you will not be evicted", "you may be able to avoid eviction"),
    ("guaranteed", "possible"),
    ("i promise", "i believe"),
    ("definitely", "likely"),
    ("court will rule in your favor", "the court may consider your case"),
    ("landlord is breaking the law", "the landlord's actions may be unlawful"),
    ("you should sue", "you may want to consult an attorney about legal options"),
    ("file a lawsuit", "consult an attorney about legal options"),
]


class SafetyGuardrails:
    """Safety and compliance checks for AI outputs"""

    def __init__(self):
        pass

    def _sanitize_text(self, text: str) -> str:
        """Replace forbidden phrases with safe alternatives"""
        sanitized = text
        for phrase, replacement in FORBIDDEN_PHRASES:
            # Case-insensitive replacement
            sanitized = re.compile(re.escape(phrase), re.IGNORECASE).sub(replacement, sanitized)
        return sanitized

    async def check_output(self, response: ActionPlanResponse) -> ActionPlanResponse:
        """Apply all safety checks and sanitize response"""
        # Sanitize all text fields
        for step in response.action_steps:
            step.description = self._sanitize_text(step.description)
            step.title = self._sanitize_text(step.title)
            if step.contact_name:
                step.contact_name = self._sanitize_text(step.contact_name)

        for resource in response.resources:
            resource.description = self._sanitize_text(resource.description)
            resource.name = self._sanitize_text(resource.name)

        response.rights_summary.headline = self._sanitize_text(response.rights_summary.headline)
        response.rights_summary.notice_requirement = self._sanitize_text(response.rights_summary.notice_requirement)
        response.urgency_reason = self._sanitize_text(response.urgency_reason)

        # Check escalation
        await self.check_escalation(response)

        # Validate phone numbers
        await self.validate_phone_numbers(response)

        return response

    async def check_escalation(self, response: ActionPlanResponse) -> None:
        """Check if escalation is needed and add resources if necessary"""
        if response.urgency_level == UrgencyLevel.CRITICAL and not response.escalation_flag:
            logger.warning("CRITICAL situation without escalation flag, forcing escalation")
            response.escalation_flag = True
            response.escalation_reason = "Critical situation requires immediate escalation"
            response.escalation_contact = "211"

            # Add 211 as a top-priority resource if not present
            has_211 = any(r.name.lower() == "211" or r.phone == "211" for r in response.resources)
            if not has_211:
                emergency_resource = Resource(
                    name="211 Emergency Hotline",
                    type=ResourceType.HOTLINE,
                    description="24/7 free and confidential service for housing, food, and emergency assistance",
                    phone="211",
                    url="https://www.211.org",
                    hours="24/7",
                    eligibility_notes="Everyone eligible",
                    is_free=True,
                    priority=1
                )
                response.resources.insert(0, emergency_resource)

    async def validate_phone_numbers(self, response: ActionPlanResponse) -> None:
        """Validate and normalize phone numbers"""
        for resource in response.resources:
            if resource.phone and resource.phone != "211":
                try:
                    parsed = phonenumbers.parse(resource.phone, "US")
                    if phonenumbers.is_valid_number(parsed):
                        resource.phone = phonenumbers.format_number(
                            parsed,
                            phonenumbers.PhoneNumberFormat.E164
                        )
                    else:
                        resource.phone = None
                except Exception:
                    resource.phone = None

        for step in response.action_steps:
            if step.contact_phone and step.contact_phone != "211":
                try:
                    parsed = phonenumbers.parse(step.contact_phone, "US")
                    if phonenumbers.is_valid_number(parsed):
                        step.contact_phone = phonenumbers.format_number(
                            parsed,
                            phonenumbers.PhoneNumberFormat.E164
                        )
                    else:
                        step.contact_phone = None
                except Exception:
                    step.contact_phone = None

    async def check_legal_predictions(self, text: str) -> tuple[bool, str]:
        """Check for forbidden legal predictions"""
        issues = []
        text_lower = text.lower()
        for phrase, _ in FORBIDDEN_PHRASES:
            if phrase.lower() in text_lower:
                issues.append(f"Forbidden phrase: '{phrase}'")
        
        return len(issues) == 0, ", ".join(issues)
