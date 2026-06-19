from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    CheckConstraint,
    Index,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base_model import BaseModel
import enum
import uuid
from typing import Optional, List


class Language(str, enum.Enum):
    EN = "EN"
    ES = "ES"


class User(BaseModel):
    __tablename__ = "users"

    session_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[Language] = mapped_column(SQLEnum(Language), default=Language.EN, nullable=False)
    phone_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_active_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    data_deletion_requested_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    intakes: Mapped[List["Intake"]] = relationship("Intake", back_populates="user", cascade="all, delete-orphan")
    sms_reminders: Mapped[List["SMSReminder"]] = relationship("SMSReminder", back_populates="user", cascade="all, delete-orphan")
    progress_steps: Mapped[List["ProgressStep"]] = relationship("ProgressStep", back_populates="user", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(is_anonymous = false AND email IS NOT NULL) OR is_anonymous = true",
            name="check_non_anonymous_has_email"
        ),
        Index("idx_users_session_token", "session_token", unique=True),
        Index("idx_users_email", "email", unique=True, postgresql_where=(email.isnot(None))),
        Index("idx_users_is_anonymous", "is_anonymous"),
        Index("idx_users_created_at", "created_at"),
    )
