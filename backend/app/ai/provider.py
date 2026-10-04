"""
MR.GREEN — AI Provider Abstraction

Defines the abstract interface that all AI providers must implement.
This allows switching between Ollama, cloud APIs, or future local models
without changing agent logic.

Architecture:
    AIProvider (abstract)
    ├── OllamaProvider
    ├── FutureCloudProvider
    └── FutureLocalProvider
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIMessage:
    """A single message in a conversation with the AI."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AIResponse:
    """Response from an AI provider."""
    content: str
    model: str
    provider: str
    token_count: int | None = None
    finish_reason: str | None = None
    duration_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    """Response from an embedding request."""
    embedding: list[float]
    model: str
    provider: str
    dimensions: int = 0


class AIProvider(ABC):
    """
    Abstract base class for all AI providers.

    Every AI provider must implement:
    - generate(): Send messages and get a text response
    - embed(): Generate vector embeddings for text
    - health_check(): Verify the provider is available
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        """
        Generate a response from the AI model.

        Args:
            messages: Conversation history as a list of AIMessage objects.
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
            max_tokens: Maximum tokens in response (None = model default).
            system_prompt: Optional system prompt prepended to messages.
            **kwargs: Provider-specific parameters.

        Returns:
            AIResponse with the generated text and metadata.
        """
        ...

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResponse:
        """
        Generate a vector embedding for the given text.

        Args:
            text: The text to embed.

        Returns:
            EmbeddingResponse with the embedding vector.
        """
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Check if the AI provider is available and responding.

        Returns:
            Dictionary with health status information.
        """
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """
        List available models from this provider.

        Returns:
            List of model name strings.
        """
        ...
