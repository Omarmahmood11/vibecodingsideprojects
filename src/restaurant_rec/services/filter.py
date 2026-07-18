"""Deterministic candidate filtering (Phase 2).

Narrows the full dataset to a small, relevant candidate set *before* the LLM
ever sees it — this controls cost, latency, and grounds results in real data.

Filter order: location -> min_rating -> cuisine -> budget.
If too few remain, relax cuisine first, then budget (never location/rating).
"""

from dataclasses import dataclass, field

from ..models.restaurant import Budget, Restaurant, UserPreferences

# Budget band -> (min_cost, max_cost) in INR, inclusive. See edge-case EC-F03.
BUDGET_RANGES: dict[Budget, tuple[int, int]] = {
    Budget.low: (0, 500),
    Budget.medium: (501, 1500),
    Budget.high: (1501, 10**9),
}

# Cuisine values that mean "no preference".
_ANY_CUISINE = {"", "any", "all", "*"}


@dataclass
class FilterResult:
    """Candidates plus flags describing any relaxation applied."""

    candidates: list[Restaurant] = field(default_factory=list)
    cuisine_relaxed: bool = False
    budget_relaxed: bool = False


def _match_location(restaurant: Restaurant, location: str) -> bool:
    return location.strip().lower() in restaurant.location.lower()


def _match_cuisine(restaurant: Restaurant, cuisine: str) -> bool:
    return cuisine.strip().lower() in restaurant.cuisine.lower()


def _match_budget(restaurant: Restaurant, budget: Budget) -> bool:
    if restaurant.cost_for_two is None:  # unknown cost — excluded from budget filter
        return False
    low, high = BUDGET_RANGES[budget]
    return low <= restaurant.cost_for_two <= high


def _apply(
    restaurants: list[Restaurant],
    prefs: UserPreferences,
    *,
    use_cuisine: bool,
    use_budget: bool,
) -> list[Restaurant]:
    """One filtering pass. Location and min_rating always apply."""
    out = []
    for r in restaurants:
        if not _match_location(r, prefs.location):
            continue
        if prefs.min_rating > 0 and (r.rating is None or r.rating < prefs.min_rating):
            continue
        if use_cuisine and prefs.cuisine and prefs.cuisine.lower() not in _ANY_CUISINE:
            if not _match_cuisine(r, prefs.cuisine):
                continue
        if use_budget and prefs.budget is not None:
            if not _match_budget(r, prefs.budget):
                continue
        out.append(r)
    return out


def _sort_and_cap(restaurants: list[Restaurant], max_candidates: int) -> list[Restaurant]:
    # Best first: rating desc (unrated last), then votes desc as tiebreak.
    ordered = sorted(
        restaurants,
        key=lambda r: (r.rating if r.rating is not None else -1.0, r.votes),
        reverse=True,
    )
    return ordered[:max_candidates]


def filter_candidates(
    prefs: UserPreferences,
    restaurants: list[Restaurant],
    *,
    min_candidates: int,
    max_candidates: int,
) -> FilterResult:
    """Return a capped candidate list, relaxing cuisine then budget if needed."""
    result = FilterResult()

    candidates = _apply(restaurants, prefs, use_cuisine=True, use_budget=True)

    # Fallback 1: relax cuisine.
    if len(candidates) < min_candidates:
        relaxed = _apply(restaurants, prefs, use_cuisine=False, use_budget=True)
        if len(relaxed) > len(candidates):
            candidates = relaxed
            result.cuisine_relaxed = True

    # Fallback 2: relax budget too.
    if len(candidates) < min_candidates:
        relaxed = _apply(restaurants, prefs, use_cuisine=False, use_budget=False)
        if len(relaxed) > len(candidates):
            candidates = relaxed
            result.cuisine_relaxed = True
            result.budget_relaxed = True

    result.candidates = _sort_and_cap(candidates, max_candidates)
    return result
