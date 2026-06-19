from pydantic import BaseModel
from typing import Optional


class ResourceResponse(BaseModel):
    name: str
    type: str
    description: str
    phone: str
    url: str
    hours: str
    eligibility_notes: str
    is_free: bool
    priority: int
