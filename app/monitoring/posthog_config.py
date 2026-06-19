import posthog
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def init_posthog():
    if not settings.POSTHOG_API_KEY:
        logger.warning("POSTHOG_API_KEY not set, skipping PostHog initialization")
        return
    posthog.api_key = settings.POSTHOG_API_KEY
    posthog.host = settings.POSTHOG_HOST
    posthog.debug = settings.POSTHOG_DEBUG
    posthog.disable_geoip = True
    posthog.flush_interval = 1.0
    posthog.max_queue_size = 1000
    logger.info("PostHog initialized successfully")
