"""Recommendation pipeline coordinator (Phase 4).

Runs: validate -> filter -> prompt -> LLM -> parse -> respond, tracking metadata.
Raises typed errors the API layer maps to HTTP codes. If the LLM call itself
throws, we degrade to rule-based ranking rather than failing the request.
"""

import logging
import time

from ..config import get_settings
from ..data.cache import RestaurantStore
from ..llm.client import LLMClient
from ..llm.parser import parse_recommendations
from ..llm.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from ..models.recommendation import RecommendationResponse
from ..models.restaurant import UserPreferences
from .filter import filter_candidates

logger = logging.getLogger(__name__)


class DatasetNotReadyError(Exception):
    """Dataset has not finished loading (-> 503)."""


class NoCandidatesError(Exception):
    """No restaurants matched, even after fallback (-> 404)."""


async def recommend(
    prefs: UserPreferences,
    store: RestaurantStore,
    llm_client: LLMClient,
) -> RecommendationResponse:
    if not store.is_ready():
        raise DatasetNotReadyError

    settings = get_settings()
    started = time.perf_counter()

    filtered = filter_candidates(
        prefs,
        store.get_all(),
        min_candidates=settings.min_candidates,
        max_candidates=settings.max_candidates,
    )
    if not filtered.candidates:
        raise NoCandidatesError

    user_prompt = build_user_prompt(prefs, filtered.candidates)
    try:
        raw = await llm_client.complete(SYSTEM_PROMPT, user_prompt)
    except Exception:  # network/auth/etc — degrade instead of 500ing the user
        logger.exception("LLM call failed; degrading to rule-based ranking")
        raw = ""  # parser treats empty as invalid -> rule-based fallback

    response = parse_recommendations(raw, filtered.candidates, prefs)

    response.metadata.update(
        candidates_considered=len(filtered.candidates),
        model=settings.llm_model,
        latency_ms=int((time.perf_counter() - started) * 1000),
        cuisine_relaxed=filtered.cuisine_relaxed,
        budget_relaxed=filtered.budget_relaxed,
    )
    return response
