from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.intake import Intake
from app.schemas.intake import IntakeCreate, IntakeUpdate, IntakeResponse
from app.core.exceptions import create_success_response, AppException
from app.services.analytics_service import track_event

router = APIRouter(prefix="/intake", tags=["Intake"])


@router.post("/submit", response_model=dict)
async def submit_intake(
    data: IntakeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a new intake form"""
    intake = Intake(
        user_id=current_user.id,
        **data.model_dump()
    )
    db.add(intake)
    await db.commit()
    await db.refresh(intake)

    await track_event(str(current_user.id), "intake_submitted", {
        "state": data.state,
        "situation_type": data.situation_type,
        "urgency_days": data.urgency_days
    })

    return create_success_response(
        IntakeResponse.model_validate(intake).model_dump(),
        "Intake submitted successfully"
    )


@router.get("/{intake_id}", response_model=dict)
async def get_intake(
    intake_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get an existing intake by ID"""
    result = await db.execute(
        select(Intake).where(
            (Intake.id == intake_id) &
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

    return create_success_response(
        IntakeResponse.model_validate(intake).model_dump(),
        "Intake retrieved successfully"
    )


@router.put("/{intake_id}", response_model=dict)
async def update_intake(
    intake_id: UUID,
    data: IntakeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing intake"""
    result = await db.execute(
        select(Intake).where(
            (Intake.id == intake_id) &
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

    for key, value in data.model_dump().items():
        setattr(intake, key, value)

    await db.commit()
    await db.refresh(intake)

    return create_success_response(
        IntakeResponse.model_validate(intake).model_dump(),
        "Intake updated successfully"
    )
