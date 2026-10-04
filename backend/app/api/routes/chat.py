"""
MR.GREEN — Chat Route

POST /api/chat — The primary chat endpoint.

Receives a user message, runs it through the full agent loop
(memory → AI → tools → verify), and returns the response.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent import Agent, AgentResponse
from app.ai.provider import AIProvider
from app.api.dependencies import get_ai_provider, get_memory_manager, get_tool_registry
from app.database.session import get_db_session
from app.memory.memory_manager import MemoryManager
from app.tools.registry import ToolRegistry

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: str | None = Field(None, description="Existing conversation ID to continue")


class MemoryItem(BaseModel):
    """A single extracted memory."""
    type: str
    key: str
    content: str


class ChatResponse(BaseModel):
    """Response body from the chat endpoint."""
    response: str
    conversation_id: str
    message_id: str
    extracted_memories: list[MemoryItem] = []
    agent_run_id: str | None = None
    iterations: int = 0
    duration_ms: int = 0


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
    ai_provider: AIProvider = Depends(get_ai_provider),
    memory_manager: MemoryManager = Depends(get_memory_manager),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ChatResponse:
    """
    Send a message to MR.GREEN and receive a response.

    The full agent loop:
    1. Receive message
    2. Load relevant memory
    3. Send context to AI
    4. Detect tool requirement
    5. Execute approved tool (if needed)
    6. Observe result
    7. Verify response quality
    8. Return final response
    9. Log interaction
    10. Extract possible memory
    """
    agent = Agent(
        ai_provider=ai_provider,
        tool_registry=registry,
        db_session=db,
        memory_manager=memory_manager,
    )

    result: AgentResponse = await agent.process_message(
        user_message=request.message,
        conversation_id=request.conversation_id,
    )

    return ChatResponse(
        response=result.content,
        conversation_id=result.conversation_id,
        message_id=result.message_id,
        extracted_memories=[
            MemoryItem(**mem) for mem in result.extracted_memories
        ],
        agent_run_id=result.agent_run_id,
        iterations=result.iterations,
        duration_ms=result.duration_ms,
    )
