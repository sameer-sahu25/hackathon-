from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.intake import Intake
from app.models.action_plan import ActionPlan, UrgencyLevel
from app.schemas.action_plan import ActionPlanGenerateRequest, ActionPlanResponse
from app.core.exceptions import create_success_response, AppException
from app.services.ai_service import generate_action_plan
from app.services.analytics_service import track_event

router = APIRouter(prefix="/action-plan", tags=["Action Plan"])


@router.post("/generate", response_model=dict)
async def generate_plan(
    request: ActionPlanGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a new action plan from an existing intake"""
    result = await db.execute(
        select(Intake).where(
            (Intake.id == request.intake_id) &
            (Intake.user_id == current_user.id)
        )
    )
    intake = result.scalar_one_or_none()
    if not intake:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="INTAKE_NOT_FOUND",
            message="Intake not found"
        )

    ai_result = await generate_action_plan(
        state=intake.state,
        county=intake.county,
        urgency_days=intake.urgency_days,
        income_monthly=intake.income_monthly,
        household_size=intake.household_size,
        situation_type=intake.situation_type.value,
        has_received_notice=intake.has_received_notice,
        language=current_user.language
    )

    plan = ActionPlan(
        intake_id=intake.id,
        user_id=current_user.id,
        urgency_level=UrgencyLevel(ai_result["urgency_level"]),
        action_steps=ai_result["action_steps"],
        resources=ai_result["resources"],
        documents_needed=ai_result["documents_needed"],
        rights_summary=ai_result["rights_summary"],
        escalation_flag=ai_result["escalation_flag"],
        raw_claude_response=ai_result.get("raw_claude_response")
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    await track_event(str(current_user.id), "action_plan_generated", {
        "urgency_level": ai_result["urgency_level"],
        "escalation_flag": ai_result["escalation_flag"]
    })

    response_data = {
        **ActionPlanResponse.model_validate(plan).model_dump(),
        "urgency_reason": ai_result.get("urgency_reason"),
        "escalation_reason": ai_result.get("escalation_reason")
    }
    return create_success_response(
        response_data,
        "Action plan generated successfully"
    )


@router.get("/{plan_id}", response_model=dict)
async def get_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get an existing action plan"""
    result = await db.execute(
        select(ActionPlan).where(
            (ActionPlan.id == plan_id) &
            (ActionPlan.user_id == current_user.id)
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PLAN_NOT_FOUND",
            message="Action plan not found"
        )
    return create_success_response(
        ActionPlanResponse.model_validate(plan).model_dump(),
        "Action plan retrieved successfully"
    )


@router.get("/by-intake/{intake_id}", response_model=dict)
async def get_plan_by_intake(
    intake_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get action plan by intake ID"""
    result = await db.execute(
        select(ActionPlan).where(
            (ActionPlan.intake_id == intake_id) &
            (ActionPlan.user_id == current_user.id)
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PLAN_NOT_FOUND",
            message="No action plan found for this intake"
        )
    return create_success_response(
        ActionPlanResponse.model_validate(plan).model_dump(),
        "Action plan retrieved successfully"
    )
