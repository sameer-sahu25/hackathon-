from pydantic import BaseModel, Field
from app.ai.schemas.action_plan import UrgencyLevel, UrgencyColor


class UrgencyClassificationResponse(BaseModel):
    urgency_level: UrgencyLevel = Field(..., description="Urgency level of the situation")
    urgency_reason: str = Field(..., description="Reason for the urgency level")
    urgency_color: UrgencyColor = Field(..., description="Color code for urgency")
    show_911: bool = Field(default=False, description="Whether to show 911")
    show_211: bool = Field(default=True, description="Whether to show 211")
    hours_to_act: int = Field(..., description="Hours to take action")


class IntakeData(BaseModel):
    state: str = Field(..., description="State code")
    county: str = Field(..., description="County name")
    urgency_days: int = Field(..., description="Days to eviction")
    income_monthly: int = Field(..., description="Monthly income")
    household_size: int = Field(..., description="Household size")
    situation_type: str = Field(..., description="Situation type")
    has_received_notice: bool = Field(..., description="Has received notice?")
    language: str = Field(default="EN", description="Language preference")
