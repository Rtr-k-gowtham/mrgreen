"""
MR.GREEN — Memory Routes

GET /api/memory — List all active memories
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Memory
from app.database.session import get_db_session

router = APIRouter(prefix="/api")


class MemoryResponse(BaseModel):
    """A single memory entry."""
    id: str
    memory_type: str
    key: str
    content: str
    confidence: float
    access_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("/memory", response_model=list[MemoryResponse])
async def list_memories(
    memory_type: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> list[MemoryResponse]:
    """List all active memories, optionally filtered by type."""
    query = (
        select(Memory)
        .where(Memory.is_active.is_(True))
        .order_by(Memory.updated_at.desc())
        .limit(limit)
    )

    if memory_type:
        query = query.where(Memory.memory_type == memory_type)

    result = await db.execute(query)
    memories = result.scalars().all()

    return [
        MemoryResponse(
            id=mem.id,
            memory_type=mem.memory_type.value,
            key=mem.key,
            content=mem.content,
            confidence=mem.confidence,
            access_count=mem.access_count or 0,
            created_at=mem.created_at,
            updated_at=mem.updated_at,
        )
        for mem in memories
    ]
