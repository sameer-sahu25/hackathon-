import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.config import settings
from app.monitoring.middleware.pii_scrubber import scrub_dict
import logging

logger = logging.getLogger(__name__)


def scrub_event(event, hint):
    """Scrub PII from Sentry events before sending"""
    scrubbed_count =0
    # Scrub extra data
    if "extra" in event:
        event["extra"], count = scrub_dict(event["extra"])
        scrubbed_count += count
    # Scrub request body
    if "request" in event and "data" in event["request"]:
        event["request"]["data"], count = scrub_dict(event["request"]["data"])
        scrubbed_count += count
    # Scrub user context: keep only id
    if "user" in event:
        if isinstance(event["user"], dict):
            user_id = event["user"].get("id")
            event["user"] = {"id": user_id}
            scrubbed_count += 1
    # Scrub request headers
    if "request" in event and "headers" in event["request"]:
        for header_key in list(event["request"]["headers"].keys()):
            if header_key.lower() in ["authorization", "cookie", "x-forwarded-for"]:
                event["request"]["headers"][header_key] = "[REDACTED]"
                scrubbed_count +=1
    if scrubbed_count >0:
        logger.debug(f"Scrubbed {scrubbed_count} PII fields from Sentry event")
    return event


def scrub_transaction(event, hint):
    """Scrub PII from Sentry transactions before sending"""
    return scrub_event(event, hint)


def init_sentry():
    if not settings.SENTRY_DSN:
        logger.warning("SENTRY_DSN not set, skipping Sentry initialization")
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        release=settings.APP_VERSION,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            CeleryIntegration(),
            RedisIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=False,
        before_send=scrub_event,
        before_send_transaction=scrub_transaction,
        max_breadcrumbs=50,
        attach_stacktrace=True,
    )
    logger.info("Sentry initialized successfully")
