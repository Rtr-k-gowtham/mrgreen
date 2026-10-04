"""
MR.GREEN — Short-Term Memory

Manages recent conversation context within a session.
This is ephemeral — it lives in memory and is backed by DB messages.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ShortTermEntry:
    """A single entry in short-term memory."""
    role: str
    content: str
    message_id: str | None = None


class ShortTermMemory:
    """
    Manages the recent conversation window.

    Keeps the last N messages in memory for context injection.
    Does NOT persist across server restarts — that's what the DB is for.
    """

    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages
        self._messages: list[ShortTermEntry] = []

    def add(self, role: str, content: str, message_id: str | None = None) -> None:
        """Add a message to short-term memory."""
        self._messages.append(ShortTermEntry(
            role=role,
            content=content,
            message_id=message_id,
        ))
        # Trim to limit
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages:]

    def get_recent(self, count: int | None = None) -> list[ShortTermEntry]:
        """Get the most recent messages."""
        if count is None:
            return list(self._messages)
        return list(self._messages[-count:])

    def get_context_messages(self) -> list[dict[str, str]]:
        """Get messages formatted for AI context injection."""
        return [
            {"role": entry.role, "content": entry.content}
            for entry in self._messages
        ]

    def clear(self) -> None:
        """Clear all short-term memory."""
        self._messages.clear()

    @property
    def count(self) -> int:
        return len(self._messages)
