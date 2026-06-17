from fastapi import APIRouter
from app.api.v1 import auth, intake, action_plan, resources, rights, checklist, sms, tracker

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(intake.router)
api_router.include_router(action_plan.router)
api_router.include_router(resources.router)
api_router.include_router(rights.router)
api_router.include_router(checklist.router)
api_router.include_router(sms.router)
api_router.include_router(tracker.router)


@api_router.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "message": "Housing Stability API is running"}
