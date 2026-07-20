"""Response models for recommendations.

Factual fields (name, rating, cost) are always filled server-side from the
dataset — never from the LLM — so the model can't alter facts (grounding).
"""

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    rank: int
    restaurant_id: str
    name: str
    cuisine: str
    rating: float | None = None
    estimated_cost: str = Field(description="Human-readable, e.g. '₹800 for two'")
    location: str
    explanation: str
    match_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Transparent 0-100 fit score: rating + how much the user's "
        "request is echoed in the restaurant's real reviews. Computed, not LLM-guessed.",
    )
    match_reasons: list[str] = Field(
        default_factory=list,
        description="Which of the user's terms the reviews actually support.",
    )


class RecommendationResponse(BaseModel):
    summary: str
    recommendations: list[Recommendation]
    metadata: dict = Field(default_factory=dict)
