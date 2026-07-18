"""Parse + ground the LLM response.

This is the safety layer. The LLM only supplies (id, rank, explanation); every
factual field is merged from the dataset here, and any id the model made up is
rejected. If the response is unusable, we fall back to rule-based ranking so the
user always gets an answer (edge cases EC-L04/L06/P01–P05).
"""

import json
import logging

from ..models.recommendation import Recommendation, RecommendationResponse
from ..models.restaurant import Restaurant, UserPreferences

logger = logging.getLogger(__name__)


def _format_cost(cost: int | None) -> str:
    return f"₹{cost} for two" if cost is not None else "Price not available"


def _strip_fences(text: str) -> str:
    """Remove ```json ... ``` fences if the model added them (EC-P01)."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: -3]
    return text.strip().removeprefix("json").strip()


def _to_recommendation(rank: int, r: Restaurant, explanation: str) -> Recommendation:
    return Recommendation(
        rank=rank,
        restaurant_id=r.id,
        name=r.name,
        cuisine=r.cuisine,
        rating=r.rating,
        estimated_cost=_format_cost(r.cost_for_two),
        location=r.location,
        explanation=explanation,
    )


def _fallback(
    candidates: list[Restaurant], prefs: UserPreferences, reason: str
) -> RecommendationResponse:
    """Rule-based ranking when the LLM output can't be used."""
    logger.warning("Using fallback ranking: %s", reason)
    top = candidates[: prefs.top_k]  # candidates arrive pre-sorted by rating
    recs = [
        _to_recommendation(
            i + 1,
            r,
            f"Rated {r.rating}/5, {r.cuisine}, {_format_cost(r.cost_for_two)}.",
        )
        for i, r in enumerate(top)
    ]
    return RecommendationResponse(
        summary=f"Top {len(recs)} restaurants in {prefs.location} by rating and budget.",
        recommendations=recs,
        metadata={"llm_fallback": True, "fallback_reason": reason},
    )


def parse_recommendations(
    raw_text: str,
    candidates: list[Restaurant],
    prefs: UserPreferences,
) -> RecommendationResponse:
    by_id = {r.id: r for r in candidates}

    try:
        data = json.loads(_strip_fences(raw_text))
    except (json.JSONDecodeError, ValueError):
        return _fallback(candidates, prefs, "invalid JSON")

    raw_recs = data.get("recommendations") if isinstance(data, dict) else None
    if not isinstance(raw_recs, list):
        return _fallback(candidates, prefs, "missing recommendations")

    recommendations: list[Recommendation] = []
    seen: set[str] = set()
    for item in raw_recs:
        if not isinstance(item, dict):
            continue
        rid = item.get("restaurant_id")
        if rid not in by_id or rid in seen:  # reject hallucinated / duplicate ids
            continue
        seen.add(rid)
        explanation = (item.get("explanation") or "").strip()
        restaurant = by_id[rid]
        if not explanation:  # EC-P03: template fallback for a missing explanation
            explanation = f"Rated {restaurant.rating}/5, {restaurant.cuisine}."
        rank = len(recommendations) + 1
        recommendations.append(_to_recommendation(rank, restaurant, explanation))
        if len(recommendations) >= prefs.top_k:  # EC-L09: truncate extras
            break

    if not recommendations:  # every id was invalid → full fallback
        return _fallback(candidates, prefs, "no valid restaurant ids")

    summary = (data.get("summary") or "").strip()
    if not summary:  # EC-P02
        summary = f"Here are {len(recommendations)} picks in {prefs.location} for you."

    return RecommendationResponse(
        summary=summary,
        recommendations=recommendations,
        metadata={"llm_fallback": False, "candidates_considered": len(candidates)},
    )
