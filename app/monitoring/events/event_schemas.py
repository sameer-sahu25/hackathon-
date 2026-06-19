from pydantic import BaseModel, Field
from typing import Literal, Optional
from uuid import UUID


class BaseEventProps(BaseModel):
    """Base props shared by all events"""
    app_version: str
    app_env: str


class SessionStartedProps(BaseEventProps):
    language: Literal["EN", "ES"]
    is_anonymous: bool
    state: Optional[str] = None


class IntakeStartedProps(BaseEventProps):
    language: Literal["EN", "ES"]
    state: Optional[str] = None


class IntakeSubmittedProps(BaseEventProps):
    state: str
    language: Literal["EN", "ES"]
    urgency_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]


class ActionPlanGeneratedProps(BaseEventProps):
    state: str
    urgency_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    language: Literal["EN", "ES"]
    confidence_score: float
    generation_latency_ms: int
    cache_hit: bool


class ActionPlanViewedProps(BaseEventProps):
    action_plan_id: UUID


class ResourceClickedProps(BaseEventProps):
    resource_id: UUID
    resource_type: str
    state: Optional[str] = None


class ResourceCalledProps(BaseEventProps):
    resource_id: UUID


class RightsCardViewedProps(BaseEventProps):
    card_id: str
    state: str
    language: Literal["EN", "ES"]


class RightsCardSharedProps(BaseEventProps):
    card_id: str


class ChecklistGeneratedProps(BaseEventProps):
    language: Literal["EN", "ES"]
    checklist_id: UUID


class PdfDownloadedProps(BaseEventProps):
    checklist_id: UUID


class SmsScheduledProps(BaseEventProps):
    reminder_id: UUID
    phone_last_four: str  # Only last four for privacy!


class SmsSentProps(BaseEventProps):
    reminder_id: UUID


class SmsDeliveryFailedProps(BaseEventProps):
    reminder_id: UUID
    failure_reason: Optional[str] = None


class SmsOptedOutProps(BaseEventProps):
    pass


class StepCompletedProps(BaseEventProps):
    step_id: UUID
    action_plan_id: UUID
    step_number: int


class StepSkippedProps(BaseEventProps):
    step_id: UUID
    action_plan_id: UUID


class OutcomeResolvedProps(BaseEventProps):
    action_plan_id: UUID
    outcome_notes: Optional[str] = None


class OutcomeEscalatedProps(BaseEventProps):
    action_plan_id: UUID
    escalated_to: str


class EvictionAvoidedProps(BaseEventProps):
    action_plan_id: UUID


class UserReturnedProps(BaseEventProps):
    days_since_last_session: int


class AiSafetyCheckFailedProps(BaseEventProps):
    check_name: str
    state: Optional[str] = None


class AiRetryTriggeredProps(BaseEventProps):
    component: str
    attempt_number: int


class EscalationTriggeredProps(BaseEventProps):
    reason: str


class CacheHitProps(BaseEventProps):
    cache_key: str
    cache_type: str


class LanguageSwitchedProps(BaseEventProps):
    old_language: Literal["EN", "ES"]
    new_language: Literal["EN", "ES"]


class AnonymousToRegisteredProps(BaseEventProps):
    pass


# Map events to their schemas
EVENT_SCHEMAS = {
    "session_started": SessionStartedProps,
    "intake_started": IntakeStartedProps,
    "intake_submitted": IntakeSubmittedProps,
    "action_plan_generated": ActionPlanGeneratedProps,
    "action_plan_viewed": ActionPlanViewedProps,
    "resource_clicked": ResourceClickedProps,
    "resource_called": ResourceCalledProps,
    "rights_card_viewed": RightsCardViewedProps,
    "rights_card_shared": RightsCardSharedProps,
    "checklist_generated": ChecklistGeneratedProps,
    "pdf_downloaded": PdfDownloadedProps,
    "sms_scheduled": SmsScheduledProps,
    "sms_sent": SmsSentProps,
    "sms_delivery_failed": SmsDeliveryFailedProps,
    "sms_opted_out": SmsOptedOutProps,
    "step_completed": StepCompletedProps,
    "step_skipped": StepSkippedProps,
    "outcome_resolved": OutcomeResolvedProps,
    "outcome_escalated": OutcomeEscalatedProps,
    "eviction_avoided": EvictionAvoidedProps,
    "user_returned": UserReturnedProps,
    "ai_safety_check_failed": AiSafetyCheckFailedProps,
    "ai_retry_triggered": AiRetryTriggeredProps,
    "escalation_triggered": EscalationTriggeredProps,
    "cache_hit": CacheHitProps,
    "language_switched": LanguageSwitchedProps,
    "anonymous_to_registered": AnonymousToRegisteredProps,
}
