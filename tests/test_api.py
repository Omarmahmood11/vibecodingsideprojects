"""API integration tests (Phase 4).

Uses a tiny in-memory store and a mocked LLM (via dependency overrides) so tests
are fast and offline — no dataset download, no real Gemini calls.
"""

import json

import pytest
from fastapi.testclient import TestClient

from restaurant_rec.api.dependencies import get_llm_client, get_store
from restaurant_rec.data.cache import RestaurantStore
from restaurant_rec.main import app
from restaurant_rec.models.restaurant import Restaurant


def make(id, name, rating=4.5, cost=800):
    return Restaurant(
        id=id, name=name, location="Indiranagar", cuisine="Italian",
        rating=rating, cost_for_two=cost, votes=10,
    )


FAKE_RECORDS = [
    make("1", "Toit", 4.7, 1200),
    make("2", "Bologna", 4.5, 1000),
    make("3", "Chianti", 4.6, 1500),
]


class FakeLLM:
    """Returns canned JSON; records the last prompt for assertions."""

    def __init__(self, payload: str):
        self._payload = payload
        self.last_user_prompt: str | None = None

    async def complete(self, system: str, user: str) -> str:
        self.last_user_prompt = user
        return self._payload


def build_store(records=FAKE_RECORDS) -> RestaurantStore:
    s = RestaurantStore()
    s.load_records(records)
    return s


def make_client(store=None, llm=None) -> TestClient:
    store = store or build_store()
    llm = llm or FakeLLM(json.dumps({
        "summary": "Great picks.",
        "recommendations": [
            {"rank": 1, "restaurant_id": "1", "explanation": "lively and great beer"},
            {"rank": 2, "restaurant_id": "2", "explanation": "quiet and romantic"},
        ],
    }))
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_llm_client] = lambda: llm
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_health_returns_ok():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}


def test_metadata_locations():
    client = make_client()
    resp = client.get("/metadata/locations")
    assert resp.status_code == 200
    assert "Indiranagar" in resp.json()


def test_recommendations_happy_path():
    client = make_client()
    resp = client.post("/recommendations", json={
        "location": "Indiranagar", "budget": "medium", "min_rating": 4.0, "top_k": 2,
        "additional_preferences": "quiet first date spot",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["recommendations"]) == 2
    assert body["recommendations"][0]["name"] == "Toit"  # fact merged from store
    assert body["metadata"]["llm_fallback"] is False
    assert body["metadata"]["model"]  # metadata populated


def test_recommendations_404_when_no_match():
    client = make_client()
    resp = client.post("/recommendations", json={"location": "Whitefield"})
    assert resp.status_code == 404


def test_recommendations_422_invalid_rating():
    client = make_client()
    resp = client.post("/recommendations", json={"location": "Indiranagar", "min_rating": 9})
    assert resp.status_code == 422


def test_recommendations_degrades_when_llm_errors():
    class BrokenLLM:
        async def complete(self, system, user):
            raise RuntimeError("gemini down")

    client = make_client(llm=BrokenLLM())
    resp = client.post("/recommendations", json={"location": "Indiranagar", "top_k": 2})
    assert resp.status_code == 200  # graceful degrade, not 500
    assert resp.json()["metadata"]["llm_fallback"] is True


def test_503_when_store_not_ready():
    empty = RestaurantStore()  # never loaded -> is_ready() False
    client = make_client(store=empty)
    resp = client.post("/recommendations", json={"location": "Indiranagar"})
    assert resp.status_code == 503
