"""FastAPI dependency providers.

Centralizing these lets tests override the store and LLM client cleanly
(via app.dependency_overrides) without touching real data or the network.
"""

from functools import lru_cache

from restaurant_rec.config import Settings, get_settings
from restaurant_rec.data.cache import RestaurantStore, store
from restaurant_rec.llm.client import GeminiClient, LLMClient


def get_app_settings() -> Settings:
    return get_settings()


def get_store() -> RestaurantStore:
    return store


@lru_cache
def get_llm_client() -> LLMClient:
    return GeminiClient()
