from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.action_plan import ActionPlan
from app.models.progress import Progress, Outcome
from app.schemas.tracker import StepCompleteRequest, OutcomeUpdateRequest, DashboardResponse
from app.core.exceptions import create_success_response, AppException

router = APIRouter(prefix="/tracker", tags=["Progress Tracker"])


@router.post("/step/complete", response_model=dict)
async def complete_step(
    request: StepCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a step as completed"""
    result = await db.execute(
        select(Progress).where(
            (Progress.action_plan_id == request.action_plan_id) &
            (Progress.step_index == request.step_index) &
            (Progress.user_id == current_user.id)
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        # Get action plan to get step title
        plan_result = await db.execute(
            select(ActionPlan).where(
                (ActionPlan.id == request.action_plan_id) &
                (ActionPlan.user_id == current_user.id)
            )
        )
        plan = plan_result.scalar_one_or_none()
        if not plan:
            raise AppException(
                status_code=404,
                code="PLAN_NOT_FOUND",
                message="Action plan not found"
            )

        step_title = "Step"
        if request.step_index < len(plan.action_steps):
            step_title = plan.action_steps[request.step_index].get("title", "Step")

        progress = Progress(
            user_id=current_user.id,
            action_plan_id=request.action_plan_id,
            step_index=request.step_index,
            step_title=step_title,
            is_completed=request.is_completed,
            outcome=Outcome.IN_PROGRESS
        )
        db.add(progress)
    else:
        progress.is_completed = request.is_completed

    await db.commit()
    await db.refresh(progress)

    return create_success_response(
        {"step_completed": progress.is_completed},
        "Step updated successfully"
    )


@router.get("/dashboard/{user_id}", response_model=dict)
async def get_dashboard(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get progress dashboard"""
    if current_user.id != user_id:
        raise AppException(
            status_code=403,
            code="FORBIDDEN",
            message="Access to this dashboard is forbidden"
        )

    # Get latest action plan
    plan_result = await db.execute(
        select(ActionPlan).where(ActionPlan.user_id == user_id).order_by(ActionPlan.generated_at.desc()).limit(1)
    )
    plan = plan_result.scalar_one_or_none()

    if not plan:
        return create_success_response(
            {"steps_completed": 0, "total_steps": 0, "next_step": None, "outcome": Outcome.PENDING},
            "Dashboard retrieved successfully"
        )

    # Get completed steps
    progress_result = await db.execute(
        select(Progress).where(
            (Progress.action_plan_id == plan.id) &
            (Progress.is_completed == True)
        )
    )
    completed = progress_result.scalars().all()

    return create_success_response(
        {
            "user_id": str(user_id),
            "steps_completed": len(completed),
            "total_steps": len(plan.action_steps),
            "next_step": None,
            "outcome": Outcome.IN_PROGRESS
        },
        "Dashboard retrieved successfully"
    )


@router.put("/outcome", response_model=dict)
async def update_outcome(
    request: OutcomeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update final outcome"""
    # Update all progress entries for this plan
    await db.execute(
        Progress.__table__.update().where(
            (Progress.action_plan_id == request.action_plan_id) &
            (Progress.user_id == current_user.id)
        ).values(outcome=request.outcome)
    )
    await db.commit()

    return create_success_response(
        {"outcome": request.outcome.value},
        "Outcome updated successfully"
    )
