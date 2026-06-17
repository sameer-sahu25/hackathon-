from celery import shared_task
from app.services.analytics_service import track_event
import logging

logger = logging.getLogger(__name__)


@shared_task
def track_event_task(user_id: str, event_name: str, properties: dict = None):
    """Async task to track events without blocking API response"""
    try:
        import asyncio
        asyncio.run(track_event(user_id, event_name, properties))
    except Exception as e:
        logger.error(f"Failed to track event {event_name}: {e}")
