"""Domain models for restaurants and user preferences.

`Restaurant` is our *clean* internal shape. The raw Zomato dataset is messy
(string ratings like "4.1/5", costs like "1,200", odd column names), so the
data layer normalizes every record into this model before anything else sees it.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class Budget(StrEnum):
    """Budget bands mapped to cost-for-two ranges in the filter."""

    low = "low"
    medium = "medium"
    high = "high"


class Restaurant(BaseModel):
    """A single normalized restaurant record."""

    id: str = Field(description="Stable identifier (dataset index based)")
    name: str
    location: str = Field(description="Neighborhood/area, e.g. 'Banashankari'")
    city: str | None = Field(default=None, description="Listed city grouping")
    cuisine: str = Field(default="", description="Raw comma-separated cuisines")
    rating: float | None = Field(default=None, description="0-5, or None if unrated")
    cost_for_two: int | None = Field(default=None, description="INR, or None if unknown")
    rest_type: str | None = Field(default=None, description="e.g. 'Casual Dining'")
    votes: int = Field(default=0)
    raw: dict = Field(default_factory=dict, description="Original record, for debugging")


class UserPreferences(BaseModel):
    """What the user asks for. `location` is a neighborhood (see edge-case DB-01)."""

    location: str = Field(min_length=1, description="Neighborhood, e.g. 'Indiranagar'")
    budget: Budget | None = None
    cuisine: str | None = None
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    additional_preferences: str | None = Field(default=None, max_length=500)
    top_k: int = Field(default=5, ge=1, le=10)
