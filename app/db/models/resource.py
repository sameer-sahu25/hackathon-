from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Index,
    Integer,
    Float,
    Text,
    ARRAY
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base_model import BaseModel
import enum
import uuid
from typing import Optional, List


class ResourceType(str, enum.Enum):
    LEGAL_AID = "LEGAL_AID"
    RENTAL_ASSISTANCE = "RENTAL_ASSISTANCE"
    SHELTER = "SHELTER"
    FOOD_BANK = "FOOD_BANK"
    MEDIATION = "MEDIATION"
    COURT = "COURT"
    HOTLINE = "HOTLINE"
    UTILITY_ASSISTANCE = "UTILITY_ASSISTANCE"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    CHILDCARE = "CHILDCARE"


class Source(str, enum.Enum):
    HUD = "HUD"
    API_211 = "API_211"
    NLIHC = "NLIHC"
    MANUAL = "MANUAL"
    SCRAPED = "SCRAPED"


class Resource(BaseModel):
    __tablename__ = "resources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[ResourceType] = mapped_column(SQLEnum(ResourceType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    county: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hours_of_operation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eligibility_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    income_limit_percent_ami: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_household_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    serves_undocumented: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    serves_domestic_violence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    languages_supported: Mapped[List[str]] = mapped_column(ARRAY(String), default=["EN"], nullable=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[Source] = mapped_column(SQLEnum(Source), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_verified_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_resources_state", "state"),
        Index("idx_resources_county", "county"),
        Index("idx_resources_type", "resource_type"),
        Index("idx_resources_state_type", "state", "resource_type"),
        Index("idx_resources_is_active", "is_active", postgresql_where=(is_active == True)),
        Index("idx_resources_location", "latitude", "longitude"),
        Index("idx_resources_source", "source"),
    )
