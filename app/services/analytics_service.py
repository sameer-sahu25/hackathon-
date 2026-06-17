from posthog import PostHog
from app.config import settings
import logging

logger = logging.getLogger(__name__)

if settings.POSTHOG_API_KEY:
    posthog = PostHog(
        project_api_key=settings.POSTHOG_API_KEY,
        host="https://app.posthog.com"
    )
else:
    posthog = None


async def track_event(user_id: str, event_name: str, properties: dict = None):
    """Track event in PostHog"""
    if posthog is None:
        logger.debug(f"PostHog not configured, skipping event {event_name}")
        return
    try:
        posthog.capture(
            distinct_id=user_id,
            event=event_name,
            properties=properties or {}
        )
    except Exception as e:
        logger.error(f"Failed to track event: {e}")


def get_impact_stats() -> dict:
    """Get aggregate impact stats (placeholder)"""
    return {
        "total_users": 0,
        "evictions_avoided": 0,
        "resources_connected": 0
    }
