"""
MR.GREEN — Google Gemini AI Provider

Implements the AIProvider interface for Google's Gemini models via the
Generative Language REST API.
Includes resilient fallback on 503/429 spikes across flash models.
"""

import json
import logging
import os
import time
from typing import Any, AsyncIterator

import httpx

from app.ai.provider import AIMessage, AIProvider, AIResponse, EmbeddingResponse
from app.config import get_settings

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_FALLBACK_MODELS = ["gemini-flash-latest", "gemini-3.5-flash", "gemini-3.8-flash"]


class GeminiProvider(AIProvider):
    """
    AI provider for Google Gemini models.

    Connects to Google's Generative Language API using httpx.
    Automatically handles model fallback if Google returns 503 high demand or 429 quota.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        embedding_model: str | None = None,
        timeout: int | None = None,
    ):
        settings = get_settings()
        self.api_key = (
            api_key
            or getattr(settings, "gemini_api_key", "")
            or os.environ.get("GEMINI_API_KEY", "")
        )
        self.model = model or getattr(settings, "gemini_model", "gemini-flash-latest")
        if self.model.startswith("models/"):
            self.model = self.model.split("models/", 1)[1]

        self.embedding_model = embedding_model or getattr(
            settings, "gemini_embedding_model", "gemini-embedding-001"
        )
        if self.embedding_model.startswith("models/"):
            self.embedding_model = self.embedding_model.split("models/", 1)[1]

        self.timeout = timeout or getattr(settings, "gemini_timeout", 60)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the pooled persistent HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=GEMINI_API_BASE,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=120.0),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _build_contents_and_system(
        self,
        messages: list[AIMessage],
        system_prompt: str | None = None,
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Convert AIMessages into Gemini system_instruction and contents format."""
        system_parts: list[str] = []
        if system_prompt:
            system_parts.append(system_prompt)

        raw_turns: list[dict[str, str]] = []
        for msg in messages:
            if msg.role == "system":
                system_parts.append(msg.content)
            elif msg.role in ("user", "tool"):
                raw_turns.append({"role": "user", "text": msg.content})
            elif msg.role == "assistant":
                raw_turns.append({"role": "model", "text": msg.content})
            else:
                raw_turns.append({"role": "user", "text": msg.content})

        # Consolidate consecutive turns of the same role
        contents: list[dict[str, Any]] = []
        for turn in raw_turns:
            role = turn["role"]
            text = turn["text"]
            if not text:
                continue
            if contents and contents[-1]["role"] == role:
                contents[-1]["parts"].append({"text": text})
            else:
                contents.append({"role": role, "parts": [{"text": text}]})

        system_instruction = None
        if system_parts:
            combined_sys = "\n\n".join(part for part in system_parts if part.strip())
            if combined_sys:
                system_instruction = {
                    "parts": [{"text": combined_sys}]
                }

        return system_instruction, contents

    async def generate(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Generate a response using Gemini's generateContent endpoint with automatic fallback."""
        client = await self._get_client()
        primary_model = kwargs.get("model", self.model)
        if primary_model.startswith("models/"):
            primary_model = primary_model.split("models/", 1)[1]

        candidate_models = [primary_model] + [m for m in DEFAULT_FALLBACK_MODELS if m != primary_model]

        system_instruction, contents = self._build_contents_and_system(
            messages=messages,
            system_prompt=system_prompt,
        )

        generation_config: dict[str, Any] = {
            "temperature": temperature,
        }
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        if system_instruction:
            payload["system_instruction"] = system_instruction

        last_error: Exception | None = None

        for model in candidate_models:
            start_time = time.monotonic()
            endpoint = f"/models/{model}:generateContent"
            params = {"key": self.api_key}

            try:
                response = await client.post(endpoint, params=params, json=payload)
                if response.status_code in (503, 429) and model != candidate_models[-1]:
                    logger.warning(
                        "Gemini model %s returned status %d. Falling back to next model.",
                        model,
                        response.status_code,
                    )
                    continue

                response.raise_for_status()
                data = response.json()
                duration_ms = int((time.monotonic() - start_time) * 1000)

                candidates = data.get("candidates", [])
                content = ""
                finish_reason = None
                if candidates:
                    first_candidate = candidates[0]
                    finish_reason = first_candidate.get("finishReason")
                    parts = first_candidate.get("content", {}).get("parts", [])
                    text_parts = [p.get("text", "") for p in parts if "text" in p]
                    content = "".join(text_parts)

                usage = data.get("usageMetadata", {})
                total_tokens = usage.get("totalTokenCount")

                return AIResponse(
                    content=content,
                    model=model,
                    provider="gemini",
                    token_count=total_tokens,
                    finish_reason=finish_reason,
                    duration_ms=duration_ms,
                    metadata=usage,
                )

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code in (503, 429) and model != candidate_models[-1]:
                    logger.warning("Gemini model %s failed (%s). Retrying next.", model, e)
                    continue
                logger.error("Gemini HTTP error on %s: %s — %s", model, e.response.status_code, e.response.text)
                raise
            except httpx.RequestError as e:
                last_error = e
                logger.error("Gemini connection error on %s: %s", model, str(e))
                if model != candidate_models[-1]:
                    continue
                raise

        if last_error:
            raise last_error
        raise RuntimeError("No candidate models succeeded")

    async def generate_stream(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream token deltas from Gemini via Server-Sent Events (SSE)."""
        client = await self._get_client()
        model = kwargs.get("model", self.model)
        if model.startswith("models/"):
            model = model.split("models/", 1)[1]

        system_instruction, contents = self._build_contents_and_system(
            messages=messages,
            system_prompt=system_prompt,
        )

        generation_config: dict[str, Any] = {
            "temperature": temperature,
        }
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        if system_instruction:
            payload["system_instruction"] = system_instruction

        endpoint = f"/models/{model}:streamGenerateContent"
        params = {"key": self.api_key, "alt": "sse"}

        start_time = time.monotonic()
        first_token = True
        token_count = 0

        try:
            async with client.stream("POST", endpoint, params=params, json=payload) as response:
                if response.status_code != 200:
                    raise httpx.HTTPStatusError(
                        f"Stream returned status {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        json_str = line[6:].strip()
                        if not json_str:
                            continue
                        try:
                            chunk = json.loads(json_str)
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    delta = p.get("text", "")
                                    if delta:
                                        if first_token:
                                            ttft = time.monotonic() - start_time
                                            logger.info(
                                                "[GEMINI_FIRST_TOKEN] model=%s ttft=%.2fs",
                                                model, ttft,
                                            )
                                            first_token = False
                                        token_count += 1
                                        yield delta
                        except json.JSONDecodeError:
                            continue

            total_duration = time.monotonic() - start_time
            logger.info("[GEMINI_STREAM_COMPLETED] model=%s duration=%.2fs", model, total_duration)

        except Exception as e:
            logger.warning("Gemini stream error (%s), falling back to non-streaming generate", str(e))
            resp = await self.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                **kwargs,
            )
            if resp.content:
                yield resp.content

    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embeddings using Gemini's embedContent endpoint."""
        client = await self._get_client()
        model_name = self.embedding_model
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        payload = {
            "model": model_name,
            "content": {
                "parts": [{"text": text}]
            }
        }
        endpoint = f"/{model_name}:embedContent"
        params = {"key": self.api_key}

        try:
            response = await client.post(endpoint, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Gemini embed HTTP error: %s — %s", e.response.status_code, e.response.text)
            raise
        except httpx.RequestError as e:
            logger.error("Gemini embed connection error: %s", str(e))
            raise

        embedding = data.get("embedding", {}).get("values", [])

        return EmbeddingResponse(
            embedding=embedding,
            model=model_name,
            provider="gemini",
            dimensions=len(embedding),
        )

    async def health_check(self) -> dict[str, Any]:
        """Verify API key and connectivity with Gemini API."""
        client = await self._get_client()

        try:
            response = await client.get("/models", params={"key": self.api_key})
            response.raise_for_status()
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            target_model = f"models/{self.model}" if not self.model.startswith("models/") else self.model
            model_available = any(target_model in m for m in models)

            return {
                "status": "healthy" if model_available else "degraded",
                "provider": "gemini",
                "model": self.model,
                "model_available": model_available,
                "available_models_count": len(models),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "gemini",
                "model": self.model,
                "error": f"{type(e).__name__}: {str(e)}",
            }

    async def list_models(self) -> list[str]:
        """List all models available with this Gemini API key."""
        client = await self._get_client()
        try:
            response = await client.get("/models", params={"key": self.api_key})
            response.raise_for_status()
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            logger.error("Failed to list Gemini models: %s", str(e))
            return []
