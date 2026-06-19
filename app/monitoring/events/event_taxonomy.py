from enum import Enum


class EventType(str, Enum):
    # Core funnel
    SESSION_STARTED = "session_started"
    INTAKE_STARTED = "intake_started"
    INTAKE_SUBMITTED = "intake_submitted"
    ACTION_PLAN_GENERATED = "action_plan_generated"
    ACTION_PLAN_VIEWED = "action_plan_viewed"

    # Engagement
    RESOURCE_CLICKED = "resource_clicked"
    RESOURCE_CALLED = "resource_called"
    RIGHTS_CARD_VIEWED = "rights_card_viewed"
    RIGHTS_CARD_SHARED = "rights_card_shared"
    CHECKLIST_GENERATED = "checklist_generated"
    PDF_DOWNLOADED = "pdf_downloaded"

    # SMS lifecycle
    SMS_SCHEDULED = "sms_scheduled"
    SMS_SENT = "sms_sent"
    SMS_DELIVERY_FAILED = "sms_delivery_failed"
    SMS_OPTED_OUT = "sms_opted_out"

    # Progress & outcomes
    STEP_COMPLETED = "step_completed"
    STEP_SKIPPED = "step_skipped"
    OUTCOME_RESOLVED = "outcome_resolved"
    OUTCOME_ESCALATED = "outcome_escalated"
    EVICTION_AVOIDED = "eviction_avoided"
    USER_RETURNED = "user_returned"

    # AI/system health
    AI_SAFETY_CHECK_FAILED = "ai_safety_check_failed"
    AI_RETRY_TRIGGERED = "ai_retry_triggered"
    ESCALATION_TRIGGERED = "escalation_triggered"
    CACHE_HIT = "cache_hit"

    # Equity & accessibility
    LANGUAGE_SWITCHED = "language_switched"
    ANONYMOUS_TO_REGISTERED = "anonymous_to_registered"
