from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.action_plan import ActionPlan
from app.core.exceptions import create_success_response, AppException
from app.services.pdf_service import generate_checklist_pdf

router = APIRouter(prefix="/checklist", tags=["Checklist"])


@router.post("/generate", response_model=dict)
async def generate_checklist(
    intake_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate document checklist from action plan"""
    result = await db.execute(
        select(ActionPlan).where(
            (ActionPlan.intake_id == intake_id) &
            (ActionPlan.user_id == current_user.id)
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise AppException(
            status_code=404,
            code="PLAN_NOT_FOUND",
            message="Action plan not found. Please generate one first."
        )

    return create_success_response(
        {
            "documents_needed": plan.documents_needed,
            "checklist_id": str(plan.id)
        },
        "Checklist generated successfully"
    )


@router.get("/{checklist_id}/pdf")
async def get_checklist_pdf(
    checklist_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download checklist as PDF"""
    result = await db.execute(
        select(ActionPlan).where(
            (ActionPlan.id == checklist_id) &
            (ActionPlan.user_id == current_user.id)
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise AppException(
            status_code=404,
            code="CHECKLIST_NOT_FOUND",
            message="Checklist not found"
        )

    pdf_bytes = generate_checklist_pdf(
        documents=plan.documents_needed,
        user_name=str(current_user.id)
    )

    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=housing-stability-checklist.pdf"
        }
    )
