from twilio.rest import Client as TwilioClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

twilio_client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


async def send_sms(phone_number: str, message: str) -> str | None:
    """Send SMS via Twilio and return SID"""
    try:
        sent_message = twilio_client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return sent_message.sid
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {e}")
        return None


def build_sms_message(deadline_date, court_address=None, checklist=None):
    """Build reminder message"""
    message = f"Housing Stability Reminder: Your deadline is {deadline_date.strftime('%m/%d/%Y')}."
    if court_address:
        message += f"\nCourt address: {court_address}"
    if checklist:
        message += f"\nDon't forget: {', '.join(checklist[:3])}"
    return message
