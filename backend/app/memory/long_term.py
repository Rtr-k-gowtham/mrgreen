"""
MR.GREEN — Long-Term Memory

Persistent storage and retrieval of user preferences, facts, and patterns.
Uses PostgreSQL for storage and pgvector for semantic search.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from app.database.models import Memory, MemoryType

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    Manages persistent memories — preferences, facts, styles, projects, workflows.

    Memories are stored in PostgreSQL and can be retrieved by type, key, or
    semantic similarity (when embeddings are available).
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def store(
        self,
        memory_type: MemoryType,
        key: str,
        content: str,
        confidence: float = 1.0,
        source_message_id: str | None = None,
        metadata: dict | None = None,
    ) -> Memory:
        """
        Store a new memory or update an existing one.

        If a memory with the same key exists, it updates the content.
        This prevents duplicate memories for the same fact/preference.
        """
        # Check if memory with this key already exists
        existing = await self._get_by_key(key)

        if existing:
            # Update existing memory
            existing.content = content
            existing.confidence = confidence
            existing.updated_at = datetime.now(timezone.utc)
            if metadata:
                existing.metadata_ = {**(existing.metadata_ or {}), **metadata}
            logger.info("Updated memory: key=%s, type=%s", key, memory_type.value)
            return existing

        # Create new memory
        memory = Memory(
            id=str(ULID()),
            memory_type=memory_type,
            key=key,
            content=content,
            confidence=confidence,
            source_message_id=source_message_id,
            metadata_=metadata or {},
        )
        self.db.add(memory)
        logger.info("Stored new memory: key=%s, type=%s", key, memory_type.value)
        return memory

    async def retrieve_by_type(
        self,
        memory_type: MemoryType,
        limit: int = 20,
    ) -> list[Memory]:
        """Retrieve all active memories of a given type."""
        result = await self.db.execute(
            select(Memory)
            .where(Memory.memory_type == memory_type)
            .where(Memory.is_active.is_(True))
            .order_by(Memory.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def retrieve_all_active(self, limit: int = 50) -> list[Memory]:
        """Retrieve all active memories, ordered by most recently updated."""
        result = await self.db.execute(
            select(Memory)
            .where(Memory.is_active.is_(True))
            .order_by(Memory.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def retrieve_for_context(self) -> str:
        """
        Build a context string from all active memories.
        This is injected into the AI system prompt.
        """
        memories = await self.retrieve_all_active()

        if not memories:
            return ""

        sections: dict[str, list[str]] = {}
        for mem in memories:
            type_label = mem.memory_type.value.replace("_", " ").title()
            if type_label not in sections:
                sections[type_label] = []
            sections[type_label].append(f"- {mem.key}: {mem.content}")

        lines = ["## What I Know About the User"]
        for section, items in sections.items():
            lines.append(f"\n### {section}")
            lines.extend(items)

        # Mark access
        for mem in memories:
            mem.access_count = (mem.access_count or 0) + 1
            mem.last_accessed_at = datetime.now(timezone.utc)

        return "\n".join(lines)

    async def search_by_key(self, key_pattern: str) -> list[Memory]:
        """Search memories by key pattern (case-insensitive LIKE)."""
        result = await self.db.execute(
            select(Memory)
            .where(Memory.key.ilike(f"%{key_pattern}%"))
            .where(Memory.is_active.is_(True))
            .order_by(Memory.updated_at.desc())
        )
        return list(result.scalars().all())

    async def deactivate(self, memory_id: str) -> None:
        """Soft-delete a memory by marking it inactive."""
        await self.db.execute(
            update(Memory)
            .where(Memory.id == memory_id)
            .values(is_active=False, updated_at=datetime.now(timezone.utc))
        )
        logger.info("Deactivated memory: id=%s", memory_id)

    async def _get_by_key(self, key: str) -> Memory | None:
        """Get a single memory by its exact key."""
        result = await self.db.execute(
            select(Memory)
            .where(Memory.key == key)
            .where(Memory.is_active.is_(True))
        )
        return result.scalar_one_or_none()
