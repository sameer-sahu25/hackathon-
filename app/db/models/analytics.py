from sqlalchemy import (
    Column,
    String,
    DateTime,
    Index,
    ForeignKey,
    Integer
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
import uuid
from typing import Optional
from datetime import datetime, UTC


# AnalyticsEvent doesn't inherit from BaseModel (no soft delete, no updated_at)
class AnalyticsEvent(AsyncAttrs, DeclarativeBase):
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    intake_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("intakes.id"), nullable=True)
    action_plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("action_plans.id"), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    urgency_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    properties: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
    session_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_analytics_event_type", "event_type"),
        Index("idx_analytics_created_at", "created_at"),
        Index("idx_analytics_state", "state"),
        Index("idx_analytics_user_id", "user_id"),
        Index("idx_analytics_type_date", "event_type", "created_at"),
    )
