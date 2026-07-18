"""Tests for LLM response parsing + grounding (Phase 3).

Covers grounding (reject hallucinated ids), dedup, truncation, template
fallbacks, and rule-based fallback (EC-L04/L06/L07/L09, EC-P01/P02/P03/P05/P06).
"""

import json

from restaurant_rec.llm.parser import parse_recommendations
from restaurant_rec.models.restaurant import Restaurant, UserPreferences


def make(id, rating=4.0, cost=800):
    return Restaurant(
        id=id, name=f"R{id}", location="Indiranagar", cuisine="Italian",
        rating=rating, cost_for_two=cost, votes=10,
    )


CANDS = [make("1", 4.5), make("2", 4.2), make("3", 3.0, cost=None)]
PREFS = UserPreferences(location="Indiranagar", top_k=2)


def wrap(recs, summary="Nice picks."):
    return json.dumps({"summary": summary, "recommendations": recs})


class TestHappyPath:
    def test_facts_merged_from_dataset_not_llm(self):
        # LLM lies about the name; parser must use the dataset's real name.
        raw = wrap([{"rank": 1, "restaurant_id": "1", "name": "FAKE", "explanation": "great"}])
        res = parse_recommendations(raw, CANDS, PREFS)
        assert res.recommendations[0].name == "R1"  # not "FAKE"
        assert res.recommendations[0].estimated_cost == "₹800 for two"
        assert res.metadata["llm_fallback"] is False

    def test_markdown_fenced_json(self):
        raw = "```json\n" + wrap([{"rank": 1, "restaurant_id": "2", "explanation": "x"}]) + "\n```"
        res = parse_recommendations(raw, CANDS, PREFS)
        assert res.recommendations[0].restaurant_id == "2"


class TestGrounding:
    def test_hallucinated_id_rejected(self):
        raw = wrap([
            {"rank": 1, "restaurant_id": "fake-999", "explanation": "made up"},
            {"rank": 2, "restaurant_id": "1", "explanation": "real"},
        ])
        res = parse_recommendations(raw, CANDS, PREFS)
        assert [r.restaurant_id for r in res.recommendations] == ["1"]

    def test_all_ids_invalid_triggers_fallback(self):
        raw = wrap([{"rank": 1, "restaurant_id": "nope", "explanation": "x"}])
        res = parse_recommendations(raw, CANDS, PREFS)
        assert res.metadata["llm_fallback"] is True

    def test_duplicate_ids_deduped(self):
        raw = wrap([
            {"rank": 1, "restaurant_id": "1", "explanation": "a"},
            {"rank": 2, "restaurant_id": "1", "explanation": "b"},
        ])
        res = parse_recommendations(raw, CANDS, PREFS)
        assert len(res.recommendations) == 1


class TestLimitsAndTemplates:
    def test_truncates_to_top_k(self):
        raw = wrap([
            {"rank": 1, "restaurant_id": "1", "explanation": "a"},
            {"rank": 2, "restaurant_id": "2", "explanation": "b"},
            {"rank": 3, "restaurant_id": "3", "explanation": "c"},
        ])
        res = parse_recommendations(raw, CANDS, PREFS)  # top_k=2
        assert len(res.recommendations) == 2
        assert [r.rank for r in res.recommendations] == [1, 2]

    def test_missing_explanation_gets_template(self):
        raw = wrap([{"rank": 1, "restaurant_id": "1", "explanation": ""}])
        res = parse_recommendations(raw, CANDS, PREFS)
        assert res.recommendations[0].explanation  # non-empty

    def test_missing_summary_gets_template(self):
        raw = json.dumps(
            {"recommendations": [{"rank": 1, "restaurant_id": "1", "explanation": "x"}]}
        )
        res = parse_recommendations(raw, CANDS, PREFS)
        assert res.summary

    def test_null_cost_display(self):
        raw = wrap([{"rank": 1, "restaurant_id": "3", "explanation": "x"}])
        res = parse_recommendations(raw, CANDS, PREFS)
        assert res.recommendations[0].estimated_cost == "Price not available"


class TestFallback:
    def test_invalid_json_falls_back(self):
        res = parse_recommendations("not json at all", CANDS, PREFS)
        assert res.metadata["llm_fallback"] is True
        assert len(res.recommendations) == 2  # top_k from pre-sorted candidates
