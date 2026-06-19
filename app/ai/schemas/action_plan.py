from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    HttpUrl,
    ConfigDict
)
from typing import List, Optional, Literal
from datetime import datetime, UTC
from enum import Enum
import phonenumbers


class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UrgencyColor(str, Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class ResourceType(str, Enum):
    LEGAL_AID = "LEGAL_AID"
    RENTAL_ASSISTANCE = "RENTAL_ASSISTANCE"
    SHELTER = "SHELTER"
    FOOD_BANK = "FOOD_BANK"
    MEDIATION = "MEDIATION"
    COURT = "COURT"
    HOTLINE = "HOTLINE"


class ResponsibleParty(str, Enum):
    RENTER = "Renter"
    LEGAL_AID = "Legal Aid"
    COURT = "Court"
    AGENCY = "Agency"
    LANDLORD = "Landlord"


class ActionStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    step_number: int = Field(..., description="Sequential step number (1-20)", ge=1, le=20)
    title: str = Field(..., description="Short action title (max 80 chars)", max_length=80)
    description: str = Field(..., description="Detailed instruction (max 500 chars)", max_length=500)
    deadline_description: str = Field(..., description="Human-readable deadline description")
    deadline_hours: Optional[int] = Field(None, description="Deadline in hours from now")
    contact_name: Optional[str] = Field(None, description="Name of contact person or organization")
    contact_phone: Optional[str] = Field(None, description="Phone number in E.164 format")
    contact_url: Optional[HttpUrl] = Field(None, description="Contact website URL")
    responsible_party: ResponsibleParty = Field(..., description="Who is responsible for this step")
    is_critical: bool = Field(..., description="Whether this step is time-critical")
    estimated_time_minutes: Optional[int] = Field(None, description="Estimated time to complete in minutes", ge=0)

    @field_validator('contact_phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        try:
            parsed = phonenumbers.parse(v, "US")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid US phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception as e:
            raise ValueError(f"Invalid phone number: {str(e)}")


class Resource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    name: str = Field(..., description="Full name of the resource organization")
    type: ResourceType = Field(..., description="Type of resource")
    description: str = Field(..., description="Brief description of what they do (max 200 chars)", max_length=200)
    phone: Optional[str] = Field(None, description="Contact phone number")
    url: Optional[HttpUrl] = Field(None, description="Resource website URL")
    hours: Optional[str] = Field(None, description="Operating hours (e.g., 'Mon-Fri 9AM-5PM' or '24/7')")
    eligibility_notes: Optional[str] = Field(None, description="Eligibility requirements")
    is_free: bool = Field(..., description="Whether this resource is free to use")
    priority: int = Field(..., description="Priority ranking (1 = highest, 10 = lowest)", ge=1, le=10)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v or v == "211":
            return v
        try:
            parsed = phonenumbers.parse(v, "US")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid US phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception as e:
            raise ValueError(f"Invalid phone number: {str(e)}")


class RightsSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    headline: str = Field(..., description="Key takeaway headline about tenant rights")
    notice_requirement: str = Field(..., description="State-specific eviction notice requirements")
    can_be_evicted_for: List[str] = Field(..., description="List of valid reasons for eviction in the state")
    cannot_be_evicted_for: List[str] = Field(..., description="List of prohibited reasons for eviction")
    key_protections: List[str] = Field(..., description="Important tenant protections")
    rent_control_applies: bool = Field(..., description="Whether rent control applies in this area")
    just_cause_required: bool = Field(..., description="Whether just cause is required for eviction")


class DocumentNeeded(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    document: str = Field(..., description="Name of required document")
    why_needed: str = Field(..., description="Why this document is needed")
    where_to_get: str = Field(..., description="Where to obtain this document")
    is_critical: bool = Field(..., description="Whether this document is critical to have")


class ActionPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    urgency_level: UrgencyLevel = Field(..., description="Urgency level of the situation")
    urgency_reason: str = Field(..., description="Explanation of why this urgency level was assigned")
    urgency_color: UrgencyColor = Field(..., description="Color-coded urgency indicator")
    action_steps: List[ActionStep] = Field(..., description="List of action steps (3-10 steps)", min_length=3, max_length=10)
    resources: List[Resource] = Field(..., description="List of relevant resources (1-8 resources)", min_length=1, max_length=8)
    rights_summary: RightsSummary = Field(..., description="Summary of tenant rights")
    documents_needed: List[DocumentNeeded] = Field(..., description="List of required documents")
    escalation_flag: bool = Field(..., description="Whether immediate human escalation is needed")
    escalation_reason: Optional[str] = Field(None, description="Why escalation is needed")
    escalation_contact: Optional[str] = Field(None, description="Who to contact for escalation")
    disclaimer: str = Field(..., description="Legal disclaimer")
    estimated_resolution_days: Optional[int] = Field(None, description="Estimated days to resolve situation", ge=0)
    confidence_score: float = Field(..., description="AI confidence score (0.0-1.0)", ge=0.0, le=1.0)
    language: Literal["EN", "ES"] = Field(..., description="Language of the response")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When this plan was generated")

    @model_validator(mode='after')
    def check_escalation_for_critical(self):
        if self.urgency_level == UrgencyLevel.CRITICAL and not self.escalation_flag:
            self.escalation_flag = True
            self.escalation_reason = "Critical situation requires immediate escalation"
            self.escalation_contact = "211"
        return self


class ActionPlanContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    state: str = Field(..., description="US state code (e.g., 'TX')", min_length=2, max_length=2)
    county: str = Field(..., description="County name")
    urgency_days: int = Field(..., description="Days until eviction deadline", ge=0)
    income_monthly: int = Field(..., description="Monthly household income", ge=0)
    household_size: int = Field(..., description="Number of people in household", ge=1)
    situation_type: str = Field(..., description="Type of housing situation")
    has_received_notice: bool = Field(..., description="Whether eviction notice has been received")
    language: Literal["EN", "ES"] = Field(default="EN", description="Preferred language")
    prior_steps: Optional[str] = Field(default="", description="Prior steps already taken")

    @field_validator('state')
    @classmethod
    def validate_state(cls, v: str) -> str:
        return v.upper()
