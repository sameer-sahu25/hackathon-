from pydantic import BaseModel, field_validator  # type: ignore[reportMissingImports]
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.intake import SituationType
from app.models.user import Language

US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]


class IntakeBase(BaseModel):
    state: str
    county: str
    urgency_days: int
    income_monthly: int
    household_size: int
    situation_type: SituationType
    has_received_notice: bool

    @field_validator('state')
    def validate_state(cls, v):
        v_upper = v.upper()
        if v_upper not in US_STATES:
            raise ValueError('Must be a valid 2-letter US state code')
        return v_upper

    @field_validator('urgency_days')
    def validate_days(cls, v):
        if v < 0 or v > 365:
            raise ValueError('Days must be between 0 and 365')
        return v

    @field_validator('income_monthly')
    def validate_income(cls, v):
        if v < 0:
            raise ValueError('Income must be positive')
        return v

    @field_validator('household_size')
    def validate_household(cls, v):
        if v < 1:
            raise ValueError('Household size must be at least 1')
        return v


class IntakeCreate(IntakeBase):
    pass


class IntakeUpdate(IntakeBase):
    pass


class IntakeResponse(IntakeBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
