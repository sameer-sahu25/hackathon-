from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.resource import Resource
from app.schemas.resource import ResourceResponse, NearbyResourcesRequest
from app.core.exceptions import create_success_response, AppException
from app.services.resource_service import (
    get_resources_nearby,
    get_resources_by_state,
    get_resource_by_id
)

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("/nearby", response_model=dict)
async def get_nearby_resources(
    lat: float = Query(...),
    lng: float = Query(...),
    state: str = Query(...),
    county: Optional[str] = None,
    income: Optional[int] = None,
    household_size: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get nearby resources by coordinates and filters"""
    resources = await get_resources_nearby(
        db=db,
        lat=lat,
        lng=lng,
        state=state,
        county=county,
        income=income,
        household_size=household_size
    )
    return create_success_response(
        [ResourceResponse.model_validate(r).model_dump() for r in resources],
        "Nearby resources retrieved successfully"
    )


@router.get("/state/{state_code}", response_model=dict)
async def get_state_resources(
    state_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all resources for a specific state"""
    resources = await get_resources_by_state(db, state_code)
    return create_success_response(
        [ResourceResponse.model_validate(r).model_dump() for r in resources],
        "State resources retrieved successfully"
    )


@router.get("/{resource_id}", response_model=dict)
async def get_resource_detail(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single resource detail by ID"""
    resource = await get_resource_by_id(db, str(resource_id))
    if not resource:
        raise AppException(
            status_code=404,
            code="RESOURCE_NOT_FOUND",
            message="Resource not found"
        )
    return create_success_response(
        ResourceResponse.model_validate(resource).model_dump(),
        "Resource retrieved successfully"
    )
