"""Transparent, computed match score (not LLM-guessed).

Blends how well-rated a place is with how much the user's free-text request is
actually echoed in that restaurant's real reviews (plus its dishes/cuisine).
Every input is real data and the formula is inspectable, so "88% match" means
something concrete, unlike a number a model would invent.

    score = 0.6 * (rating / 5) + 0.4 * (fraction of the user's PREFERENCE terms the data backs up)

Filler and meal/time words ("big", "dinner", "great") are ignored so they don't
unfairly drag the score. Only real preferences (vibe + food terms) are counted.
"""

import re

from ..models.restaurant import Restaurant, UserPreferences

# Words that carry no preference signal, so they don't count toward a match.
# This includes filler ("big", "great") and meal/time words ("dinner", "night")
# that a review would rarely echo, so they shouldn't drag the score down.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "for", "to", "of", "in", "on", "with",
    "without", "some", "somewhere", "place", "places", "spot", "really", "not",
    "too", "very", "nice", "good", "great", "best", "want", "looking", "would",
    "like", "me", "my", "we", "us", "is", "are", "be", "at", "that", "this",
    "have", "get", "go", "out", "up", "near", "around", "something", "anything",
    "bit", "big", "small", "dinner", "lunch", "breakfast", "brunch", "meal",
    "food", "eat", "evening", "night", "morning", "day", "fussy", "fancy",
    "simple", "plain", "thing", "catch", "one", "nothing", "everything",
}

# Small synonym groups so we match meaning, not just exact spelling.
_SYNONYMS = {
    "quiet": {"quiet", "calm", "peaceful", "serene", "relaxed", "silent"},
    "romantic": {"romantic", "intimate", "date", "couple", "candlelight"},
    "lively": {"lively", "vibrant", "buzzing", "energetic", "happening", "crowd", "fun"},
    "family": {"family", "families", "kids", "children", "child"},
    "cheap": {"cheap", "affordable", "budget", "value", "pocket"},
    "cozy": {"cozy", "cosy", "warm", "comfortable", "comfy", "snug"},
    "outdoor": {"outdoor", "rooftop", "terrace", "alfresco", "garden", "open"},
    "view": {"view", "rooftop", "scenic", "skyline"},
    "coffee": {"coffee", "cafe", "espresso", "latte", "brew"},
    "authentic": {"authentic", "traditional", "original"},
    "friends": {"friends", "group", "groups", "gang", "hangout", "buddies"},
    "spacious": {"spacious", "roomy", "large", "ample", "airy"},
}


def _expand(word: str) -> set[str]:
    return _SYNONYMS.get(word, {word})


def _keywords(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 2 and w not in _STOPWORDS]


def compute_match(r: Restaurant, prefs: UserPreferences) -> tuple[int, list[str]]:
    """Return (score 0-100, matched terms). Deterministic and inspectable."""
    rating_c = (r.rating / 5.0) if r.rating is not None else 0.7

    haystack = " ".join(
        [" ".join(r.review_snippets), r.dish_liked, r.cuisine, r.rest_type or ""]
    ).lower()

    terms = list(dict.fromkeys(_keywords(prefs.additional_preferences or "")))  # de-duped
    matched: list[str] = [t for t in terms if any(syn in haystack for syn in _expand(t))]

    if terms:
        intent_c = len(matched) / len(terms)
        score = 0.6 * rating_c + 0.4 * intent_c  # rating is a real quality floor
    else:
        score = rating_c  # no free-text request: fit is just how well-rated it is

    return round(score * 100), matched
