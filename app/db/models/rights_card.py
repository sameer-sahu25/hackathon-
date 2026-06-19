from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Index,
    Integer,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base_model import BaseModel
from app.db.models.user import Language
import uuid
from typing import Optional, List


class RightsCard(BaseModel):
    __tablename__ = "rights_cards"

    state: Mapped[str] = mapped_column(String(2), nullable=False)
    language: Mapped[Language] = mapped_column(SQLEnum(Language), default=Language.EN, nullable=False)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    notice_requirement: Mapped[str] = mapped_column(String(255), nullable=False)
    can_be_evicted_for: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    cannot_be_evicted_for: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    key_protections: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    rent_control_applies: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    just_cause_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    full_content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    generated_by_model: Mapped[str] = mapped_column(String(100), nullable=False)
    last_reviewed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("state", "language", name="uix_state_language"),
        Index("idx_rights_state_language", "state", "language", unique=True),
        Index("idx_rights_is_current", "is_current", postgresql_where=(is_current == True)),
    )
