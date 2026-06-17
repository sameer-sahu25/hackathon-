from pydantic import BaseModel  # type: ignore[reportMissingImports]
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.progress import Outcome


class StepCompleteRequest(BaseModel):
    action_plan_id: UUID
    step_index: int
    is_completed: bool


class ProgressStepResponse(BaseModel):
    id: UUID
    action_plan_id: UUID
    step_index: int
    step_title: str
    is_completed: bool
    completed_at: Optional[datetime] = None
    outcome: Outcome

    class Config:
        from_attributes = True


class OutcomeUpdateRequest(BaseModel):
    action_plan_id: UUID
    outcome: Outcome


class DashboardResponse(BaseModel):
    user_id: UUID
    steps_completed: int
    total_steps: int
    next_step: Optional[ProgressStepResponse] = None
    outcome: Outcome
