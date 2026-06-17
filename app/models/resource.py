from sqlalchemy import Column, String, Boolean, Float, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import enum
import uuid


class ResourceType(str, enum.Enum):
    LEGAL_AID = "LEGAL_AID"
    RENTAL_ASSISTANCE = "RENTAL_ASSISTANCE"
    SHELTER = "SHELTER"
    FOOD_BANK = "FOOD_BANK"
    MEDIATION = "MEDIATION"


class Source(str, enum.Enum):
    HUD = "HUD"
    SOURCE_211 = "211"
    MANUAL = "MANUAL"


class Resource(Base):
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    resource_type = Column(SQLEnum(ResourceType), nullable=False)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    url = Column(String(500), nullable=True)
    state = Column(String(2), nullable=False)
    county = Column(String(255), nullable=True)
    eligibility_notes = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    source = Column(SQLEnum(Source), default=Source.MANUAL, nullable=False)
