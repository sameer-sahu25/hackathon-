from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Index,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base_model import BaseModel
import enum
import uuid
from typing import Optional


class StepOutcome(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


class ProgressStep(BaseModel):
    __tablename__ = "progress_steps"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("action_plans.id", ondelete="CASCADE"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_title: Mapped[str] = mapped_column(String(255), nullable=False)
    step_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skipped_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[StepOutcome] = mapped_column(SQLEnum(StepOutcome), default=StepOutcome.PENDING, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="progress_steps")
    action_plan: Mapped["ActionPlan"] = relationship("ActionPlan", back_populates="progress_steps")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("step_number >= 1", name="check_step_number_positive"),
        UniqueConstraint("action_plan_id", "step_number", name="uix_action_plan_step_number"),
        Index("idx_progress_user_id", "user_id"),
        Index("idx_progress_action_plan_id", "action_plan_id"),
        Index("idx_progress_is_completed", "is_completed"),
        Index("idx_progress_outcome", "outcome"),
    )
