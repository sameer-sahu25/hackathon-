from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Index,
    ForeignKey,
    Integer,
    Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base_model import BaseModel
import enum
import uuid
from typing import Optional, List


class ReminderType(str, enum.Enum):
    SEVEN_DAY = "SEVEN_DAY"
    THREE_DAY = "THREE_DAY"
    ONE_DAY = "ONE_DAY"
    MORNING_OF = "MORNING_OF"
    CUSTOM = "CUSTOM"


class SMSStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    OPTED_OUT = "OPTED_OUT"


class SMSReminder(BaseModel):
    __tablename__ = "sms_reminders"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    intake_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("intakes.id", ondelete="CASCADE"), nullable=False)
    phone_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_last_four: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    message_body: Mapped[str] = mapped_column(Text, nullable=False)
    reminder_type: Mapped[ReminderType] = mapped_column(SQLEnum(ReminderType), nullable=False)
    scheduled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SMSStatus] = mapped_column(SQLEnum(SMSStatus), default=SMSStatus.PENDING, nullable=False)
    twilio_message_sid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sms_reminders")
    intake: Mapped["Intake"] = relationship("Intake", back_populates="sms_reminders")

    # Indexes
    __table_args__ = (
        Index("idx_sms_user_id", "user_id"),
        Index("idx_sms_intake_id", "intake_id"),
        Index("idx_sms_status", "status"),
        Index("idx_sms_scheduled_at", "scheduled_at"),
        Index("idx_sms_pending_scheduled", "status", "scheduled_at", postgresql_where=(status == SMSStatus.PENDING)),
    )
