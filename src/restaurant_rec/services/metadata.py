"""Locations and cuisines metadata service.

Serves the distinct values (built as indexes at load time) that populate the
UI dropdowns — so users pick a real neighborhood instead of typing a miss.
"""

from ..data.cache import RestaurantStore


def get_locations(store: RestaurantStore) -> list[str]:
    return store.locations()


def get_cuisines(store: RestaurantStore) -> list[str]:
    return store.cuisines()
