from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.exceptions import create_success_response
from app.services.rag_service import retrieve_relevant_docs

router = APIRouter(prefix="/rights", tags=["Tenant Rights"])

US_STATES_LIST = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]


@router.get("/state/{state_code}", response_model=dict)
async def get_state_rights(
    state_code: str,
    current_user: User = Depends(get_current_user)
):
    """Get tenant rights information for a specific state"""
    state_upper = state_code.upper()
    if state_upper not in US_STATES_LIST:
        return create_success_response(
            {
                "state": state_upper,
                "summary": "Please contact a local legal aid organization for state-specific tenant rights information.",
                "rights": []
            },
            "Rights information retrieved successfully"
        )

    docs = await retrieve_relevant_docs(
        query=f"tenant rights eviction rental assistance",
        state=state_upper,
        situation_type="general"
    )

    summary = "\n".join(docs[:3]) if docs else f"Tenant rights information for {state_upper} - please contact legal aid for details."

    return create_success_response(
        {
            "state": state_upper,
            "summary": summary,
            "sources": docs
        },
        "Tenant rights retrieved successfully"
    )


@router.get("/states", response_model=dict)
async def list_states():
    """List all available states"""
    return create_success_response(
        US_STATES_LIST,
        "States list retrieved successfully"
    )
