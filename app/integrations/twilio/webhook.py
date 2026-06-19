from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from app.config import settings
import sentry_sdk
import logging

logger = logging.getLogger(__name__)


async def handle_status_webhook(request: Request) -> None:
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    form_data = await request.form()
    url = str(request.url)
    
    signature = request.headers.get("X-Twilio-Signature", "")
    
    if not validator.validate(url, form_data, signature):
        logger.warning("Invalid Twilio webhook signature verification failed")
        sentry_sdk.capture_message("Twilio webhook signature invalid", level="warning")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    logger.info("Twilio webhook received and verified")
    
    message_sid = form_data.get("MessageSid")
    message_status = form_data.get("MessageStatus")
    
    logger.info(f"Message {message_sid} status: {message_status}")
