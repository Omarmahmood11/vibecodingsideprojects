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


class RecommendationResponse(BaseModel):
    summary: str
    recommendations: list[Recommendation]
    metadata: dict = Field(default_factory=dict)
