"""
MR.GREEN — Memory Manager

Orchestrates all memory subsystems: short-term, long-term, and daily logs.
Handles memory extraction from conversations using the AI provider.

The memory extraction mechanism uses the AI model to determine whether
a user message contains information worth remembering. It does NOT
blindly store every message.
"""

import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import AIMessage, AIProvider
from app.database.models import MemoryType
from app.memory.daily_logs import DailyLogger
from app.memory.long_term import LongTermMemory
from app.memory.short_term import ShortTermMemory

logger = logging.getLogger(__name__)

# System prompt used to extract memories from conversation
MEMORY_EXTRACTION_PROMPT = """You are a memory extraction system for an AI assistant called MR.GREEN.

Analyze the following user message and determine if it contains information worth remembering.

Types of information to extract:
- PREFERENCE: User preferences (e.g., "I prefer concise answers", "I like dark mode")
- FACT: Important facts about the user (e.g., "I'm a Python developer", "My name is Gowtham")
- STYLE: Communication style preferences (e.g., "Don't be formal", "Use technical terms")
- PROJECT: Project-related information (e.g., "I'm working on a web app called X")
- WORKFLOW: Workflow preferences (e.g., "I always use Git flow", "I test before deploying")

If the message contains extractable information, respond with a JSON object:
{
    "has_memory": true,
    "memories": [
        {
            "type": "preference|fact|style|project|workflow",
            "key": "short_descriptive_key",
            "content": "what to remember"
        }
    ]
}

If the message is just a regular conversation with nothing worth remembering, respond with:
{
    "has_memory": false,
    "memories": []
}

IMPORTANT: Only extract genuinely useful information. Do NOT extract greetings, questions, or trivial statements.
Respond with ONLY the JSON object, nothing else."""


class MemoryManager:
    """
    Central orchestrator for all memory operations.

    Coordinates:
    - Short-term memory (conversation context)
    - Long-term memory (persistent preferences/facts)
    - Daily logging (activity audit trail)
    - Memory extraction (AI-powered analysis)
    """

    def __init__(
        self,
        db_session: AsyncSession,
        ai_provider: AIProvider,
        short_term_limit: int = 50,
        extraction_enabled: bool = True,
    ):
        self.short_term = ShortTermMemory(max_messages=short_term_limit)
        self.long_term = LongTermMemory(db_session)
        self.daily_logger = DailyLogger(db_session)
        self.ai_provider = ai_provider
        self.extraction_enabled = extraction_enabled
        self._db = db_session

    async def add_user_message(
        self,
        content: str,
        message_id: str | None = None,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Process a user message: add to short-term memory and extract memories.

        Returns:
            List of extracted memories (may be empty).
        """
        # Add to short-term memory
        self.short_term.add("user", content, message_id)

        # Extract memories if enabled
        extracted: list[dict[str, Any]] = []
        if self.extraction_enabled:
            extracted = await self._extract_memories(content, message_id, session_id)

        return extracted

    async def add_assistant_message(
        self,
        content: str,
        message_id: str | None = None,
    ) -> None:
        """Add an assistant response to short-term memory."""
        self.short_term.add("assistant", content, message_id)

    async def get_context_for_ai(self) -> str:
        """
        Build the complete memory context for the AI prompt.

        Combines long-term memories into a context string that gets
        injected into the system prompt.
        """
        return await self.long_term.retrieve_for_context()

    async def get_conversation_messages(self) -> list[dict[str, str]]:
        """Get recent conversation messages for AI context."""
        return self.short_term.get_context_messages()

    async def _extract_memories(
        self,
        user_message: str,
        message_id: str | None = None,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Use the AI to analyze a user message for extractable memories.

        This is the core of the learning system — it determines what's
        worth remembering without blindly storing everything.
        """
        try:
            response = await self.ai_provider.generate(
                messages=[
                    AIMessage(role="user", content=f"User message to analyze:\n\n{user_message}"),
                ],
                system_prompt=MEMORY_EXTRACTION_PROMPT,
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500,
            )

            # Parse the JSON response
            result = self._parse_extraction_response(response.content)

            if not result.get("has_memory", False):
                return []

            extracted = []
            for mem_data in result.get("memories", []):
                mem_type = self._map_memory_type(mem_data.get("type", ""))
                if mem_type is None:
                    continue

                key = mem_data.get("key", "").strip()
                content = mem_data.get("content", "").strip()

                if not key or not content:
                    continue

                memory = await self.long_term.store(
                    memory_type=mem_type,
                    key=key,
                    content=content,
                    source_message_id=message_id,
                )

                # Log the memory storage
                await self.daily_logger.log_memory_stored(
                    key=key,
                    memory_type=mem_type.value,
                    session_id=session_id,
                )

                extracted.append({
                    "type": mem_type.value,
                    "key": key,
                    "content": content,
                })

                logger.info(
                    "Extracted memory: type=%s, key=%s",
                    mem_type.value, key,
                )

            return extracted

        except Exception as e:
            logger.warning("Memory extraction failed: %s", str(e))
            return []

    def _parse_extraction_response(self, response: str) -> dict[str, Any]:
        """Parse the AI's memory extraction response as JSON."""
        # Try to extract JSON from the response
        response = response.strip()

        # Handle markdown code blocks
        if response.startswith("```"):
            lines = response.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            response = "\n".join(json_lines)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(response[start:end])
                except json.JSONDecodeError:
                    pass

            logger.warning("Could not parse memory extraction response")
            return {"has_memory": False, "memories": []}

    @staticmethod
    def _map_memory_type(type_str: str) -> MemoryType | None:
        """Map a string memory type to the MemoryType enum."""
        mapping = {
            "preference": MemoryType.PREFERENCE,
            "fact": MemoryType.FACT,
            "style": MemoryType.STYLE,
            "project": MemoryType.PROJECT,
            "workflow": MemoryType.WORKFLOW,
        }
        return mapping.get(type_str.lower())
