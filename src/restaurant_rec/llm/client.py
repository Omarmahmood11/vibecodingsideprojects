"""LLM adapter: a provider-agnostic protocol + a Gemini implementation.

Keeping the interface tiny (`complete`) means the rest of the app never imports
a vendor SDK — swapping providers is a one-file change (Architecture principle).

Reliability (Phase 6 hardening):
- Enforce a response schema + JSON mime so the reply is always the exact shape.
- Disable "thinking" for this ranking task so the whole output-token budget goes
  to the JSON answer (also faster), and cap output tokens to avoid truncation.
- Fail fast on 429 (free-tier quota / rate limit): retrying just burns more of the
  daily quota and rarely helps in-window, so we surface a typed error and let the
  caller degrade to rule-based ranking with an honest reason.
"""

import asyncio
import logging
from typing import Protocol

from pydantic import BaseModel

from ..config import get_settings

logger = logging.getLogger(__name__)


class LLMRateLimitError(Exception):
    """Provider rejected the call for quota / rate limits (HTTP 429)."""


class LLMUnavailableError(Exception):
    """LLM call failed after retries (timeout / server error)."""


class LLMClient(Protocol):
    async def complete(self, system: str, user: str) -> str:
        """Return the model's raw text response (expected to be JSON)."""
        ...


# Structured-output schema: forces Gemini to emit exactly this shape. Mirrors the
# JSON the prompt asks for and the parser reads (rank is accepted but re-derived).
class _RecItem(BaseModel):
    rank: int
    restaurant_id: str
    explanation: str


class _LLMOutput(BaseModel):
    summary: str
    recommendations: list[_RecItem]


class GeminiClient:
    """Google Gemini adapter using structured (JSON) output."""

    def __init__(self) -> None:
        from google import genai

        settings = get_settings()
        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.llm_model

    async def complete(self, system: str, user: str) -> str:
        from google.genai import errors, types

        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=self._settings.llm_temperature,
            max_output_tokens=self._settings.llm_max_output_tokens,
            response_mime_type="application/json",
            response_schema=_LLMOutput,
            # Ranking/formatting doesn't need chain-of-thought; disabling it sends
            # the whole token budget to the JSON answer and cuts latency.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )

        last_exc: Exception | None = None
        for attempt in range(self._settings.llm_max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self._client.aio.models.generate_content(
                        model=self._model, contents=user, config=config
                    ),
                    timeout=self._settings.llm_timeout_seconds,
                )
                return response.text or ""
            except errors.ClientError as exc:
                # 429 = quota/rate limit. Fail fast: retrying burns more quota.
                if exc.code == 429:
                    raise LLMRateLimitError(str(exc)) from exc
                raise  # other 4xx (bad key/config) — not retryable, surface it
            except (TimeoutError, errors.ServerError) as exc:
                last_exc = exc  # transient — worth a retry

            if attempt < self._settings.llm_max_retries:
                backoff = 2**attempt
                logger.warning(
                    "LLM call failed (attempt %d), retrying in %ds", attempt + 1, backoff
                )
                await asyncio.sleep(backoff)

        raise LLMUnavailableError("LLM call failed after retries") from last_exc
