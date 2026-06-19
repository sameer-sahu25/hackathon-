import sentry_sdk
from app.monitoring.middleware.pii_scrubber import scrub_dict
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def capture_ai_failure(error: Exception, context: dict) -> None:
    scrubbed_context, _ = scrub_dict(context)
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("component", "ai_core")
        scope.set_tag("state", context.get("state", "unknown"))
        scope.set_tag("urgency_level", context.get("urgency_level", "unknown"))
        scope.set_context("ai_context", scrubbed_context)
        # Fingerprint by error type and integration if present
        fingerprint = ["ai-failure", type(error).__name__]
        if "integration" in context:
            fingerprint.append(context["integration"])
        scope.fingerprint = fingerprint
        sentry_sdk.capture_exception(error)


def capture_integration_failure(integration: str, error: Exception, context: dict) -> None:
    scrubbed_context, _ = scrub_dict(context)
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("integration", integration)
        if "circuit_breaker_state" in context:
            scope.set_tag("circuit_breaker_state", context["circuit_breaker_state"])
        scope.set_context("integration_context", scrubbed_context)
        # If fallback succeeded: warning, else: error
        fallback_succeeded = context.get("fallback_succeeded", False)
        level = "warning" if fallback_succeeded else "error"
        sentry_sdk.capture_exception(error, level=level)


def capture_critical_user_path_failure(path: str, user_id: str, error: Exception) -> None:
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("critical_path", "true")
        scope.set_tag("user_id", user_id)
        scope.set_tag("path", path)
        sentry_sdk.capture_exception(error, level="error")
