"""
MR.GREEN — Embedding Generation

Generates vector embeddings via the AI provider for semantic memory search.
Keeps the embedding logic decoupled from the specific AI provider.
"""

import logging
from typing import Any

from app.ai.provider import AIProvider

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Generates text embeddings using the configured AI provider.

    Used by the memory system for semantic search/retrieval.
    """

    def __init__(self, ai_provider: AIProvider):
        self.provider = ai_provider

    async def generate(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        try:
            response = await self.provider.embed(text)
            logger.debug(
                "Generated embedding: dimensions=%d, model=%s",
                response.dimensions,
                response.model,
            )
            return response.embedding
        except Exception as e:
            logger.error("Failed to generate embedding: %s", str(e))
            raise

    async def get_dimensions(self) -> int:
        """
        Get the embedding dimension count by generating a test embedding.

        Returns:
            Number of dimensions in the embedding vector.
        """
        response = await self.provider.embed("test")
        return response.dimensions
