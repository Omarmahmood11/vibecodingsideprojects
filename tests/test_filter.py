"""Tests for candidate filtering logic (Phase 2).

Covers each rule in isolation, combined filters, boundary values (EC-F03),
fallback relaxation (EC-F06/EC-U07), and the empty-result case (EC-U02/U14).
"""

from restaurant_rec.models.restaurant import Budget, Restaurant, UserPreferences
from restaurant_rec.services.filter import filter_candidates


def make(id, loc, cuisine="Italian", rating=4.0, cost=800, votes=10):
    return Restaurant(
        id=id, name=f"R{id}", location=loc, cuisine=cuisine,
        rating=rating, cost_for_two=cost, votes=votes,
    )


# Reusable dataset: mostly Indiranagar, mixed cuisines/cost/rating.
DATA = [
    make("1", "Indiranagar", "Italian", 4.5, 900),
    make("2", "Indiranagar", "North Indian, Chinese", 4.2, 400),
    make("3", "Indiranagar", "Italian", 3.0, 1600),
    make("4", "Indiranagar", "Thai", 4.8, 1200),
    make("5", "Koramangala", "Italian", 4.9, 700),
    make("6", "Indiranagar", "Italian", None, None),  # unrated + unknown cost
]


def run(prefs, data=DATA, min_c=1, max_c=50):
    return filter_candidates(prefs, data, min_candidates=min_c, max_candidates=max_c)


class TestLocation:
    def test_case_insensitive_and_only_that_area(self):
        res = run(UserPreferences(location="indiranagar"))
        assert {r.id for r in res.candidates} == {"1", "2", "3", "4", "6"}

    def test_no_match_returns_empty(self):
        res = run(UserPreferences(location="Whitefield"))
        assert res.candidates == []


class TestRating:
    def test_min_rating_excludes_below_and_unrated(self):
        res = run(UserPreferences(location="Indiranagar", min_rating=4.0))
        # 3 (3.0) and 6 (None) drop out
        assert {r.id for r in res.candidates} == {"1", "2", "4"}


class TestCuisine:
    def test_token_match(self):
        res = run(UserPreferences(location="Indiranagar", cuisine="Chinese"))
        assert {r.id for r in res.candidates} == {"2"}

    def test_any_disables_filter(self):
        res = run(UserPreferences(location="Indiranagar", cuisine="any"))
        assert len(res.candidates) == 5


class TestBudget:
    def test_low_boundary_inclusive_500(self):
        d = [make("a", "X", cost=500), make("b", "X", cost=501)]
        res = run(UserPreferences(location="X", budget=Budget.low), data=d)
        assert {r.id for r in res.candidates} == {"a"}

    def test_medium_range(self):
        res = run(UserPreferences(location="Indiranagar", budget=Budget.medium))
        # medium = 501..1500 -> ids 1(900),4(1200); excludes 2(400),3(1600),6(None)
        assert {r.id for r in res.candidates} == {"1", "4"}

    def test_null_cost_excluded(self):
        res = run(UserPreferences(location="Indiranagar", budget=Budget.high))
        assert "6" not in {r.id for r in res.candidates}


class TestFallback:
    def test_relaxes_cuisine_when_too_few(self):
        # Only 1 Thai in Indiranagar, but we demand 3 candidates.
        res = run(UserPreferences(location="Indiranagar", cuisine="Thai"), min_c=3)
        assert res.cuisine_relaxed is True
        assert len(res.candidates) >= 3

    def test_relaxes_budget_when_still_too_few(self):
        # Thai + low budget matches nothing; must relax both to hit min.
        res = run(
            UserPreferences(location="Indiranagar", cuisine="Thai", budget=Budget.low),
            min_c=3,
        )
        assert res.cuisine_relaxed is True
        assert res.budget_relaxed is True


class TestSortAndCap:
    def test_sorted_by_rating_desc_and_capped(self):
        res = run(UserPreferences(location="Indiranagar"), max_c=2)
        assert len(res.candidates) == 2
        assert res.candidates[0].id == "4"  # 4.8 highest among Indiranagar
        assert res.candidates[1].id == "1"  # 4.5 next
