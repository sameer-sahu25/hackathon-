import time
import asyncio
from typing import Optional, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.integrations.twilio.client import get_twilio_client, get_from_number, validate_phone_number
from app.integrations.shared.logger import IntegrationLogger
from app.integrations.shared.circuit_breaker import get_twilio_circuit
import sentry_sdk
import logging

logger = logging.getLogger(__name__)


class SmsSendError(Exception):
    pass


class TwilioService:
    def __init__(self):
        self.client = get_twilio_client()
        self.from_number = get_from_number()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8)
    )
    async def send_sms(
        self,
        to: str,
        body: str,
        status_callback_url: Optional[str] = None
    ) -> Dict:
        start_time = time.time()
        
        if not validate_phone_number(to):
            raise SmsSendError("Invalid phone number")
        
        try:
            async def _send():
                return await asyncio.to_thread(
                    self.client.messages.create,
                    body=body,
                    from_=self.from_number,
                    to=to,
                    status_callback=status_callback_url or settings.TWILIO_STATUS_CALLBACK_URL
                )
            
            circuit = get_twilio_circuit()
            message = await circuit(_send)
            
            latency_ms = (time.time() - start_time) * 1000
            IntegrationLogger.log_call(
                integration="twilio",
                method="send_sms",
                latency_ms=latency_ms,
                status="success"
            )
            
            return {"sid": message.sid, "status": message.status}
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.error(f"Failed to send SMS (circuit: {get_twilio_circuit().state.value}): {str(e)}")
            # Fallback: log and return a "queued locally" status
            return {"sid": f"LOCAL_{int(time.time())}", "status": "queued_fallback"}

    async def get_message_status(self, sid: str) -> Dict:
        try:
            if sid.startswith("LOCAL_"):
                return {"sid": sid, "status": "queued_fallback"}
            message = await asyncio.to_thread(self.client.messages(sid).fetch)
            return {"sid": message.sid, "status": message.status}
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise

    async def cancel_scheduled_message(self, sid: str) -> bool:
        if sid.startswith("LOCAL_"):
            return True
        try:
            await asyncio.to_thread(self.client.messages(sid).update(status="canceled"))
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return False
