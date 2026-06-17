from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.intake import Intake
from app.models.sms_reminder import SmsReminder
from app.schemas.sms import SmsScheduleRequest, SmsReminderResponse
from app.core.exceptions import create_success_response, AppException
from app.tasks.sms_tasks import schedule_sms_reminders_task

router = APIRouter(prefix="/sms", tags=["SMS Reminders"])


@router.post("/schedule", response_model=dict)
async def schedule_reminders(
    request: SmsScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule SMS reminders for a deadline"""
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

    # Schedule Celery tasks
    schedule_sms_reminders_task.delay(
        str(request.intake_id),
        str(current_user.id),
        request.phone_number,
        request.deadline_date.isoformat()
    )

    return create_success_response(
        {"status": "scheduled", "intake_id": str(request.intake_id)},
        "SMS reminders scheduled successfully"
    )


@router.get("/status/{intake_id}", response_model=dict)
async def get_sms_status(
    intake_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check status of SMS reminders for an intake"""
    result = await db.execute(
        select(SmsReminder).where(
            (SmsReminder.intake_id == intake_id) &
            (SmsReminder.user_id == current_user.id)
        )
    )
    reminders = result.scalars().all()
    return create_success_response(
        [SmsReminderResponse.model_validate(r).model_dump() for r in reminders],
        "SMS status retrieved successfully"
    )


@router.delete("/cancel/{intake_id}", response_model=dict)
async def cancel_reminders(
    intake_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel pending SMS reminders"""
    result = await db.execute(
        select(Intake).where(
            (Intake.id == intake_id) &
            (Intake.user_id == current_user.id)
        )
    )
    if not result.scalar_one_or_none():
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="INTAKE_NOT_FOUND",
            message="Intake not found"
        )

    # Update pending reminders to canceled
    from app.models.sms_reminder import SmsStatus
    await db.execute(
        delete(SmsReminder).where(
            (SmsReminder.intake_id == intake_id) &
            (SmsReminder.status == SmsStatus.PENDING)
        )
    )
    await db.commit()

    return create_success_response(
        {"status": "canceled"},
        "Pending SMS reminders canceled successfully"
    )
