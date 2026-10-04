"""
MR.GREEN — Capabilities Routes

GET /api/capabilities — List all capabilities
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Capability
from app.database.session import get_db_session

router = APIRouter(prefix="/api")


class CapabilityResponse(BaseModel):
    """A capability entry."""
    id: str
    name: str
    description: str
    version: str
    is_approved: bool
    is_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/capabilities", response_model=list[CapabilityResponse])
async def list_capabilities(
    db: AsyncSession = Depends(get_db_session),
) -> list[CapabilityResponse]:
    """List all capabilities (approved and pending)."""
    result = await db.execute(
        select(Capability).order_by(Capability.created_at.desc())
    )
    capabilities = result.scalars().all()

    return [
        CapabilityResponse(
            id=cap.id,
            name=cap.name,
            description=cap.description,
            version=cap.version,
            is_approved=cap.is_approved,
            is_enabled=cap.is_enabled,
            created_at=cap.created_at,
        )
        for cap in capabilities
    ]
