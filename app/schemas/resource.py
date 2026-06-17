from pydantic import BaseModel  # type: ignore[reportMissingImports]
from typing import Optional
from uuid import UUID
from app.models.resource import ResourceType, Source


class ResourceResponse(BaseModel):
    id: UUID
    name: str
    resource_type: ResourceType
    address: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    state: str
    county: Optional[str] = None
    eligibility_notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool
    source: Source

    class Config:
        from_attributes = True


class NearbyResourcesRequest(BaseModel):
    lat: float
    lng: float
    state: str
    county: str
    income: Optional[int] = None
    household_size: Optional[int] = None
