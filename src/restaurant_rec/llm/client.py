"""LLM adapter: a provider-agnostic protocol + a Gemini implementation.

Keeping the interface tiny (`complete`) means the rest of the app never imports
a vendor SDK — swapping providers is a one-file change (Architecture principle).
"""

import asyncio
import logging
from typing import Protocol

from ..config import get_settings

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    async def complete(self, system: str, user: str) -> str:
        """Return the model's raw text response (expected to be JSON)."""
        ...


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
            response_mime_type="application/json",
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
            except (TimeoutError, errors.ServerError) as exc:
                last_exc = exc
            except errors.ClientError as exc:
                # 429 is transient (rate limit); other 4xx are not worth retrying.
                if exc.code != 429:
                    raise
                last_exc = exc

            if attempt < self._settings.llm_max_retries:
                backoff = 2**attempt
                logger.warning(
                    "LLM call failed (attempt %d), retrying in %ds", attempt + 1, backoff
                )
                await asyncio.sleep(backoff)

        raise RuntimeError("LLM call failed after retries") from last_exc
