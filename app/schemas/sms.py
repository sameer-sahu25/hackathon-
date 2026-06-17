from pydantic import BaseModel, field_validator  # type: ignore[reportMissingImports]
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.sms_reminder import SmsStatus
import phonenumbers  # type: ignore[reportMissingImports]


class SmsScheduleRequest(BaseModel):
    intake_id: UUID
    phone_number: str
    deadline_date: datetime

    @field_validator('phone_number')
    def validate_phone(cls, v):
        try:
            parsed = phonenumbers.parse(v, "US")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            raise ValueError("Invalid phone number")


class SmsReminderResponse(BaseModel):
    id: UUID
    user_id: UUID
    phone_number: str
    intake_id: UUID
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    status: SmsStatus
    twilio_sid: Optional[str] = None

    class Config:
        from_attributes = True
