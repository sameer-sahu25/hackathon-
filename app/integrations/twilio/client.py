from twilio.rest import Client
from app.config import settings
import phonenumbers
from typing import Optional

_twilio_client: Optional[Client] = None
_from_number: Optional[str] = None


def get_twilio_client() -> Client:
    global _twilio_client
    if _twilio_client is None:
        _twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    return _twilio_client


def get_from_number() -> str:
    global _from_number
    if _from_number is None:
        _from_number = settings.TWILIO_PHONE_NUMBER
    return _from_number


def validate_phone_number(phone: str) -> bool:
    try:
        parsed = phonenumbers.parse(phone, "US")
        return phonenumbers.is_valid_number(parsed)
    except Exception:
        return False
