from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import relationship
import enum
import uuid


class UrgencyLevel(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ActionPlan(Base):
    __tablename__ = "action_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intake_id = Column(UUID(as_uuid=True), ForeignKey("intakes.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    urgency_level = Column(SQLEnum(UrgencyLevel), nullable=False)
    action_steps = Column(JSONB, nullable=False, default=list)
    resources = Column(JSONB, nullable=False, default=list)
    documents_needed = Column(JSONB, nullable=False, default=list)
    rights_summary = Column(Text, nullable=True)
    escalation_flag = Column(Boolean, nullable=False, default=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_claude_response = Column(Text, nullable=True)

    intake = relationship("Intake")
    user = relationship("User")
