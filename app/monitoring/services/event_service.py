import asyncio
import posthog
from typing import Dict, Any, Optional
from app.monitoring.events.event_taxonomy import EventType
from app.monitoring.events.event_schemas import EVENT_SCHEMAS
from app.monitoring.middleware.pii_scrubber import scrub_dict
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EventService:
    @staticmethod
    async def _track_async(event_name: str, distinct_id: str, properties: Dict[str, Any]):
        try:
            # Validate properties
            schema_class = EVENT_SCHEMAS.get(event_name)
            if schema_class:
                # Inject default props
                props_with_defaults = {
                    "app_version": settings.APP_VERSION,
                    "app_env": settings.APP_ENV,
                    **properties
                }
                # Validate, only keep whitelisted fields
                validated = schema_class(**props_with_defaults)
                properties = validated.model_dump(exclude_none=True)
            # Scrub just in case any PII slipped through
            properties, _ = scrub_dict(properties)

            # Capture with PostHog
            posthog.capture(
                distinct_id=distinct_id,
                event=event_name,
                properties=properties
            )
        except Exception as e:
            logger.warning(f"Failed to track event {event_name}: {e}")
            # Never raise, analytics failures shouldn't break user flow

    @staticmethod
    async def track(
        event_name: str,
        distinct_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        # Run in background task, don't block
        asyncio.create_task(
            EventService._track_async(
                event_name=event_name,
                distinct_id=distinct_id,
                properties=properties or {}
            )
        )

    @staticmethod
    async def track_batch(events: list[Dict]) -> None:
        try:
            for event in events:
                await EventService._track_async(
                    event_name=event.get("event"),
                    distinct_id=event.get("distinct_id"),
                    properties=event.get("properties", {})
                )
            posthog.flush()
        except Exception as e:
            logger.warning(f"Failed to track batch events: {e}")

    @staticmethod
    async def alias(old_id: str, new_id: str) -> None:
        try:
            posthog.alias(previous_id=old_id, distinct_id=new_id)
        except Exception as e:
            logger.warning(f"Failed to alias user {old_id} → {new_id}: {e}")
