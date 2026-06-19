from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    CheckConstraint,
    Index,
    ForeignKey,
    Integer,
    Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base_model import BaseModel
from app.db.models.user import Language
import enum
import uuid
from typing import Optional, List


class SituationType(str, enum.Enum):
    EVICTION_NOTICE = "EVICTION_NOTICE"
    BEHIND_RENT = "BEHIND_RENT"
    LEASE_VIOLATION = "LEASE_VIOLATION"
    PREVENTIVE = "PREVENTIVE"
    LOCKOUT = "LOCKOUT"
    UTILITY_SHUTOFF = "UTILITY_SHUTOFF"


class Intake(BaseModel):
    __tablename__ = "intakes"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    county: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    situation_type: Mapped[SituationType] = mapped_column(SQLEnum(SituationType), nullable=False)
    has_received_notice: Mapped[bool] = mapped_column(Boolean, nullable=False)
    urgency_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    income_monthly: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    household_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    has_children: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_disability: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_domestic_violence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prior_evictions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    language: Mapped[Language] = mapped_column(SQLEnum(Language), default=Language.EN, nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ip_country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    session_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="intakes")
    action_plans: Mapped[List["ActionPlan"]] = relationship("ActionPlan", back_populates="intake", cascade="all, delete-orphan")
    sms_reminders: Mapped[List["SMSReminder"]] = relationship("SMSReminder", back_populates="intake", cascade="all, delete-orphan")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("urgency_days >= 0 OR urgency_days IS NULL", name="check_urgency_days_positive"),
        CheckConstraint("income_monthly >= 0 OR income_monthly IS NULL", name="check_income_positive"),
        CheckConstraint("household_size >= 1 AND household_size <= 20", name="check_household_size"),
        Index("idx_intakes_user_id", "user_id"),
        Index("idx_intakes_state", "state"),
        Index("idx_intakes_situation_type", "situation_type"),
        Index("idx_intakes_urgency_days", "urgency_days"),
        Index("idx_intakes_created_at", "created_at"),
        Index("idx_intakes_state_situation", "state", "situation_type"),
    )
