"""
MR.GREEN — Ollama AI Provider

Implements the AIProvider interface for local Ollama models.
Communicates with Ollama's REST API via httpx.
"""

import logging
import time
from typing import Any

import httpx

from app.ai.provider import AIMessage, AIProvider, AIResponse, EmbeddingResponse
from app.config import get_settings

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """
    AI provider for locally-running Ollama models.

    Connects to the Ollama HTTP API at the configured base URL.
    Never exposes the local Ollama instance to the public internet.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        embedding_model: str | None = None,
        timeout: int | None = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.embedding_model = embedding_model or settings.ollama_embedding_model
        self.timeout = timeout or settings.ollama_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Generate a response using Ollama's /api/chat endpoint."""
        client = await self._get_client()

        # Build message list for Ollama
        ollama_messages: list[dict[str, str]] = []

        if system_prompt:
            ollama_messages.append({
                "role": "system",
                "content": system_prompt,
            })

        for msg in messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        payload: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        logger.info(
            "Ollama generate request: model=%s, messages=%d",
            payload["model"],
            len(ollama_messages),
        )

        start_time = time.monotonic()

        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Ollama HTTP error: %s — %s", e.response.status_code, e.response.text)
            raise
        except httpx.RequestError as e:
            logger.error("Ollama connection error: %s", str(e))
            raise

        duration_ms = int((time.monotonic() - start_time) * 1000)

        # Parse response
        message_data = data.get("message", {})
        content = message_data.get("content", "")

        # Token counts from Ollama
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens

        logger.info(
            "Ollama response: tokens=%d, duration=%dms",
            total_tokens,
            duration_ms,
        )

        return AIResponse(
            content=content,
            model=data.get("model", self.model),
            provider="ollama",
            token_count=total_tokens if total_tokens > 0 else None,
            finish_reason=data.get("done_reason"),
            duration_ms=duration_ms,
            metadata={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_duration_ns": data.get("total_duration"),
            },
        )

    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embeddings using Ollama's /api/embed endpoint."""
        client = await self._get_client()

        payload = {
            "model": self.embedding_model,
            "input": text,
        }

        try:
            response = await client.post("/api/embed", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Ollama embed HTTP error: %s — %s", e.response.status_code, e.response.text)
            raise
        except httpx.RequestError as e:
            logger.error("Ollama embed connection error: %s", str(e))
            raise

        # Ollama returns embeddings as a list of vectors
        embeddings = data.get("embeddings", [[]])
        embedding = embeddings[0] if embeddings else []

        return EmbeddingResponse(
            embedding=embedding,
            model=data.get("model", self.embedding_model),
            provider="ollama",
            dimensions=len(embedding),
        )

    async def health_check(self) -> dict[str, Any]:
        """Check if Ollama is running and the model is available."""
        client = await self._get_client()

        try:
            # Check Ollama is running
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()

            models = [m["name"] for m in data.get("models", [])]
            model_available = any(
                self.model in m for m in models
            )

            return {
                "status": "healthy" if model_available else "degraded",
                "provider": "ollama",
                "base_url": self.base_url,
                "model": self.model,
                "model_available": model_available,
                "available_models": models,
            }
        except Exception as e:
            err_msg = str(e) or repr(e)
            return {
                "status": "unhealthy",
                "provider": "ollama",
                "base_url": self.base_url,
                "model": self.model,
                "error": f"{type(e).__name__}: {err_msg}" if str(e) else repr(e),
            }

    async def list_models(self) -> list[str]:
        """List all models available in Ollama."""
        client = await self._get_client()

        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error("Failed to list Ollama models: %s", str(e))
            return []
