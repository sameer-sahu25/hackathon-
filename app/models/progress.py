from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import relationship
import enum
import uuid


class Outcome(str, enum.Enum):
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"


class Progress(Base):
    __tablename__ = "progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action_plan_id = Column(UUID(as_uuid=True), ForeignKey("action_plans.id"), nullable=False)
    step_index = Column(Integer, nullable=False)
    step_title = Column(String(255), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(SQLEnum(Outcome), default=Outcome.PENDING, nullable=False)

    user = relationship("User")
    action_plan = relationship("ActionPlan")
