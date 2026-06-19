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
    Float,
    Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base_model import BaseModel
from app.db.models.user import Language
import enum
import uuid
from typing import Optional, List


class UrgencyLevel(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UrgencyColor(str, enum.Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class ActionPlan(BaseModel):
    __tablename__ = "action_plans"

    intake_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("intakes.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    urgency_level: Mapped[UrgencyLevel] = mapped_column(SQLEnum(UrgencyLevel), nullable=False)
    urgency_reason: Mapped[str] = mapped_column(Text, nullable=False)
    urgency_color: Mapped[UrgencyColor] = mapped_column(SQLEnum(UrgencyColor), nullable=False)
    action_steps: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)
    resources: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)
    rights_summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    documents_needed: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)
    escalation_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escalation_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_resolution_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    language: Mapped[Language] = mapped_column(SQLEnum(Language), default=Language.EN, nullable=False)
    claude_model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens_input: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generation_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rag_chunks_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retries_needed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_claude_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    intake: Mapped["Intake"] = relationship("Intake", back_populates="action_plans")
    user: Mapped["User"] = relationship("User")
    progress_steps: Mapped[List["ProgressStep"]] = relationship("ProgressStep", back_populates="action_plan", cascade="all, delete-orphan")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("confidence_score >= 0.0 AND confidence_score <= 1.0", name="check_confidence_range"),
        Index("idx_action_plans_intake_id", "intake_id"),
        Index("idx_action_plans_user_id", "user_id"),
        Index("idx_action_plans_urgency_level", "urgency_level"),
        Index("idx_action_plans_generated_at", "generated_at"),
        Index("idx_action_plans_escalation_flag", "escalation_flag", postgresql_where=(escalation_flag == True)),
    )
