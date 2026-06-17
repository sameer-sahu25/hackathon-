from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import relationship
import enum
import uuid


class SmsStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class SmsReminder(Base):
    __tablename__ = "sms_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    phone_number = Column(String(50), nullable=False)
    intake_id = Column(UUID(as_uuid=True), ForeignKey("intakes.id"), nullable=False)
    message_body = Column(Text, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(SmsStatus), default=SmsStatus.PENDING, nullable=False)
    twilio_sid = Column(String(100), nullable=True)

    user = relationship("User")
    intake = relationship("Intake")
