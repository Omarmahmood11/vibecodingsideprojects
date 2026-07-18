from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from restaurant_rec.api.dependencies import get_llm_client, get_store
from restaurant_rec.data.cache import RestaurantStore
from restaurant_rec.llm.client import LLMClient
from restaurant_rec.models.recommendation import RecommendationResponse
from restaurant_rec.models.restaurant import UserPreferences
from restaurant_rec.services import metadata
from restaurant_rec.services.orchestrator import (
    DatasetNotReadyError,
    NoCandidatesError,
    recommend,
)

router = APIRouter()

StoreDep = Annotated[RestaurantStore, Depends(get_store)]
LLMDep = Annotated[LLMClient, Depends(get_llm_client)]


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metadata/locations")
async def locations(store: StoreDep) -> list[str]:
    if not store.is_ready():
        raise HTTPException(status_code=503, detail="Restaurant data is unavailable.")
    return metadata.get_locations(store)


@router.get("/metadata/cuisines")
async def cuisines(store: StoreDep) -> list[str]:
    if not store.is_ready():
        raise HTTPException(status_code=503, detail="Restaurant data is unavailable.")
    return metadata.get_cuisines(store)


@router.post("/recommendations")
async def recommendations(
    prefs: UserPreferences,
    store: StoreDep,
    llm_client: LLMDep,
) -> RecommendationResponse:
    try:
        return await recommend(prefs, store, llm_client)
    except DatasetNotReadyError:
        raise HTTPException(
            status_code=503, detail="Restaurant data is loading. Try again shortly."
        )
    except NoCandidatesError:
        raise HTTPException(
            status_code=404,
            detail="No restaurants found for these preferences. Try relaxing your filters.",
        )
