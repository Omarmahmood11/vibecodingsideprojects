"""Prompt construction for ranking + explanation.

Design choice (edge-case DB-03): the LLM's real job is to honor the user's
free-text intent — the fuzzy stuff dropdowns can't capture. The prompt makes
that intent the primary ranking signal and demands the explanation reference it.
"""

import json

from ..models.restaurant import Restaurant, UserPreferences

SYSTEM_PROMPT = """You are a restaurant recommendation assistant for a Zomato-inspired app.

You receive a user's preferences and a list of REAL restaurants from a database.
Each restaurant may include `popular_dishes` and `reviews` (short real excerpts
from actual customer reviews).

Rules you must follow:
- ONLY recommend restaurants from the provided candidate list. Never invent one.
- Refer to each restaurant by its exact `id` from the list.
- Do not alter factual fields (name, rating, cost) — just rank and explain.
- The user's free-text request is the MOST important signal. Weigh it above the
  structured filters.
- GROUNDING (important): any claim about atmosphere, vibe, noise, crowd, decor,
  service, or who a place suits (dates, families, groups) MUST be based on that
  restaurant's `reviews` or `popular_dishes`. Paraphrase what reviewers actually
  said. If a restaurant has NO reviews, do not invent ambiance; explain the fit
  using only cuisine, rating, price, and dishes.
- Write plainly. Do NOT use em dashes or en dashes (— or –); use commas or short
  sentences instead.
- Return ONLY valid JSON matching the requested schema. No prose outside the JSON.
"""


def serialize_candidates(candidates: list[Restaurant]) -> str:
    """Compact JSON of just the fields the model needs to reason (no `raw`).

    Includes `popular_dishes` and real `reviews` (v2) so the model can ground
    vibe/ambiance claims instead of inventing them.
    """
    rows = []
    for r in candidates:
        row = {
            "id": r.id,
            "name": r.name,
            "cuisine": r.cuisine,
            "rating": r.rating,
            "cost_for_two": r.cost_for_two,
            "location": r.location,
            "type": r.rest_type,
        }
        if r.dish_liked:
            row["popular_dishes"] = r.dish_liked
        if r.review_snippets:
            row["reviews"] = r.review_snippets
        rows.append(row)
    return json.dumps(rows, ensure_ascii=False)


def build_user_prompt(prefs: UserPreferences, candidates: list[Restaurant]) -> str:
    intent = prefs.additional_preferences or "(none given)"
    return f"""User's request (most important — honor this):
"{intent}"

Structured preferences:
- Neighborhood: {prefs.location}
- Budget: {prefs.budget or "any"}
- Cuisine: {prefs.cuisine or "any"}
- Minimum rating: {prefs.min_rating}

Candidate restaurants (JSON):
{serialize_candidates(candidates)}

Pick the top {prefs.top_k} that best fit the user's request and rank them.
Return JSON:
{{
  "summary": "one short paragraph addressing the user's request",
  "recommendations": [
    {{"rank": 1, "restaurant_id": "<id>", "explanation": "why this fits, grounded in the reviews/dishes"}}
  ]
}}"""
