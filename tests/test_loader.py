"""Unit tests for dataset normalization (Phase 1).

Covers the messy real-world values we saw in the raw Zomato data:
EC-D06 (bad ratings) and EC-D07 (comma/symbol costs).
"""

from restaurant_rec.data.loader import parse_cost, parse_rating


class TestParseRating:
    def test_fraction_form(self):
        assert parse_rating("4.1/5") == 4.1

    def test_plain_number(self):
        assert parse_rating("3.5") == 3.5

    def test_new_and_dash_and_blank_are_none(self):
        assert parse_rating("NEW") is None
        assert parse_rating("-") is None
        assert parse_rating("") is None
        assert parse_rating(None) is None

    def test_out_of_range_is_none(self):
        assert parse_rating("6.0/5") is None
        assert parse_rating("-1") is None

    def test_junk_is_none_not_zero(self):
        assert parse_rating("great") is None


class TestParseCost:
    def test_plain(self):
        assert parse_cost("800") == 800

    def test_comma_separated(self):
        assert parse_cost("1,200") == 1200

    def test_currency_symbol(self):
        assert parse_cost("₹1,500") == 1500

    def test_blank_and_none(self):
        assert parse_cost("") is None
        assert parse_cost(None) is None

    def test_junk(self):
        assert parse_cost("cheap") is None
