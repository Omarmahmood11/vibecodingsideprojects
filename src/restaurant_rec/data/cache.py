"""In-memory restaurant store with lookup indexes.

Loaded once at startup and held in memory for the process lifetime. Building
indexes up front keeps filtering and metadata endpoints fast (no full scans).
"""

import logging

from ..models.restaurant import Restaurant
from .loader import load_restaurants

logger = logging.getLogger(__name__)

# Delimiters used to split multi-value cuisine strings ("North Indian, Chinese").
_CUISINE_SEPARATORS = [",", "/", "&"]


def _split_cuisines(cuisine: str) -> list[str]:
    tokens = [cuisine]
    for sep in _CUISINE_SEPARATORS:
        tokens = [part for token in tokens for part in token.split(sep)]
    return [t.strip() for t in tokens if t.strip()]


class RestaurantStore:
    """Holds normalized restaurants and derived indexes."""

    def __init__(self) -> None:
        self._records: list[Restaurant] = []
        self._by_id: dict[str, Restaurant] = {}
        self._by_location: dict[str, list[Restaurant]] = {}
        self._locations: list[str] = []
        self._cuisines: list[str] = []
        self._ready = False

    def load(self) -> None:
        """Populate the store and build indexes. Safe to call once at startup."""
        records = load_restaurants()
        self._records = records
        self._by_id = {r.id: r for r in records}

        by_location: dict[str, list[Restaurant]] = {}
        cuisines: set[str] = set()
        for r in records:
            by_location.setdefault(r.location.lower(), []).append(r)
            cuisines.update(c.lower() for c in _split_cuisines(r.cuisine))

        self._by_location = by_location
        self._locations = sorted({r.location for r in records})
        self._cuisines = sorted({c for c in cuisines})
        self._ready = True

        if records:
            sample = records[0]
            logger.info(
                "Store ready: %d restaurants, %d locations, %d cuisines. "
                "Sample: %s (%s, rating=%s)",
                len(records),
                len(self._locations),
                len(self._cuisines),
                sample.name,
                sample.location,
                sample.rating,
            )

    # --- read API -------------------------------------------------------
    def is_ready(self) -> bool:
        return self._ready

    def count(self) -> int:
        return len(self._records)

    def get_all(self) -> list[Restaurant]:
        return self._records

    def get_by_id(self, restaurant_id: str) -> Restaurant | None:
        return self._by_id.get(restaurant_id)

    def locations(self) -> list[str]:
        return self._locations

    def cuisines(self) -> list[str]:
        return self._cuisines


# Process-wide singleton. Loaded at app startup (see main.py lifespan).
store = RestaurantStore()
