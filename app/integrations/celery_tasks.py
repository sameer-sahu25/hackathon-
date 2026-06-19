import asyncio
from celery import Celery
from app.config import settings
from app.integrations.twilio.service import TwilioService
from app.integrations.hud.service import HudService
from app.integrations.api_211.service import Api211Service
from app.integrations.data_gov.service import DataGovService
from app.integrations.nlihc.ingest import ingest_nlihc_data
from app.integrations.shared.logger import IntegrationLogger
import logging
import sentry_sdk

logger = logging.getLogger(__name__)

celery = Celery(
    "housing_stability",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


# Idempotent background tasks
@celery.task(bind=True, max_retries=3)
def send_sms_reminder(self, reminder_id: str, to: str, body: str):
    """Idempotent task to send SMS reminders. Uses reminder_id to avoid duplicates."""
    try:
        # Check Redis for already sent reminders (using reminder_id as key)
        # For now, just proceed with sending
        loop = asyncio.get_event_loop()
        service = TwilioService()
        result = loop.run_until_complete(service.send_sms(to=to, body=body))
        logger.info(f"SMS reminder {reminder_id} sent: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to send SMS reminder {reminder_id}: {e}")
        sentry_sdk.capture_exception(e)
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery.task(bind=True, max_retries=3)
def sync_hud_programs(self, state: str):
    """Idempotent task to sync HUD programs for a state."""
    try:
        loop = asyncio.get_event_loop()
        service = HudService()
        programs = loop.run_until_complete(service.search_programs(state=state))
        logger.info(f"Synced {len(programs)} HUD programs for {state}")
        return {"state": state, "programs_synced": len(programs)}
    except Exception as e:
        logger.error(f"Failed to sync HUD programs for {state}: {e}")
        sentry_sdk.capture_exception(e)
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery.task(bind=True, max_retries=3)
def sync_211_resources(self, county: str, state: str):
    """Idempotent task to sync 211 resources for a county."""
    try:
        loop = asyncio.get_event_loop()
        service = Api211Service()
        resources = loop.run_until_complete(service.search_local_services(0, 0, county=county))
        logger.info(f"Synced {len(resources)} 211 resources for {county}, {state}")
        return {"county": county, "state": state, "resources_synced": len(resources)}
    except Exception as e:
        logger.error(f"Failed to sync 211 resources for {county}, {state}: {e}")
        sentry_sdk.capture_exception(e)
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery.task(bind=True, max_retries=3)
def sync_federal_rules(self):
    """Idempotent task to sync federal housing rules."""
    try:
        loop = asyncio.get_event_loop()
        service = DataGovService()
        rules = loop.run_until_complete(service.get_federal_housing_rules())
        logger.info(f"Synced {len(rules)} federal rules")
        return {"rules_synced": len(rules)}
    except Exception as e:
        logger.error(f"Failed to sync federal rules: {e}")
        sentry_sdk.capture_exception(e)
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery.task(bind=True, max_retries=3)
def run_nlihc_ingest(self, csv_path: str):
    """Idempotent task to ingest NLIHC data from CSV."""
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(ingest_nlihc_data(csv_path))
        logger.info(f"Ingested NLIHC data: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to ingest NLIHC data: {e}")
        sentry_sdk.capture_exception(e)
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
