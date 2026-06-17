from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import relationship
import enum
import uuid


class SituationType(str, enum.Enum):
    EVICTION_NOTICE = "EVICTION_NOTICE"
    BEHIND_RENT = "BEHIND_RENT"
    LEASE_VIOLATION = "LEASE_VIOLATION"
    PREVENTIVE = "PREVENTIVE"


class Intake(Base):
    __tablename__ = "intakes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    state = Column(String(2), nullable=False)
    county = Column(String(255), nullable=False)
    urgency_days = Column(Integer, nullable=False)
    income_monthly = Column(Integer, nullable=False)
    household_size = Column(Integer, nullable=False)
    situation_type = Column(SQLEnum(SituationType), nullable=False)
    has_received_notice = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
