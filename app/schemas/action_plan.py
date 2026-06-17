from pydantic import BaseModel  # type: ignore[reportMissingImports]
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.models.action_plan import UrgencyLevel


class ActionStep(BaseModel):
    step_number: int
    title: str
    description: str
    deadline: str
    contact: str
    responsible_party: str


class ResourceItem(BaseModel):
    name: str
    type: str
    phone: str
    url: str
    eligibility_notes: str
    distance_miles: float


class ActionPlanGenerateRequest(BaseModel):
    intake_id: UUID


class ActionPlanResponse(BaseModel):
    id: UUID
    intake_id: UUID
    user_id: UUID
    urgency_level: UrgencyLevel
    urgency_reason: Optional[str] = None
    action_steps: List[ActionStep]
    resources: List[ResourceItem]
    rights_summary: Optional[str] = None
    documents_needed: List[str]
    escalation_flag: bool
    escalation_reason: Optional[str] = None
    generated_at: datetime

    class Config:
        from_attributes = True
