"""
MR.GREEN — Conversations Routes

GET /api/conversations — List all conversations
GET /api/conversations/{id} — Get a specific conversation with messages
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Conversation, Message
from app.database.session import get_db_session

router = APIRouter(prefix="/api")


class MessageResponse(BaseModel):
    """A single message in a conversation."""
    id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    """Summary of a conversation (for listing)."""
    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    """Full conversation with messages."""
    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
) -> list[ConversationSummary]:
    """List all conversations, most recent first."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    conversations = result.scalars().all()

    return [
        ConversationSummary(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            is_active=conv.is_active,
            message_count=len(conv.messages),
        )
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> ConversationDetail:
    """Get a specific conversation with all its messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        is_active=conversation.is_active,
        messages=[
            MessageResponse(
                id=msg.id,
                role=msg.role.value,
                content=msg.content,
                created_at=msg.created_at,
            )
            for msg in conversation.messages
        ],
    )
