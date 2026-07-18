"""Load and normalize the Zomato dataset from Hugging Face.

The raw dataset (ManikaSaini/zomato-restaurant-recommendation) has messy,
string-typed fields. This module is the *only* place that knows about those
raw quirks; everything downstream works with clean `Restaurant` objects.
"""

import logging
import time

from ..config import get_settings
from ..models.restaurant import Restaurant

logger = logging.getLogger(__name__)

# Raw dataset column names (note the spaces/parentheses — we isolate them here).
COL_NAME = "name"
COL_LOCATION = "location"
COL_CITY = "listed_in(city)"
COL_CUISINES = "cuisines"
COL_RATE = "rate"
COL_COST = "approx_cost(for two people)"
COL_REST_TYPE = "rest_type"
COL_VOTES = "votes"


def parse_rating(raw: object) -> float | None:
    """Normalize a raw rating into a 0-5 float, or None.

    Handles: "4.1/5" -> 4.1, "NEW"/"-"/""/None -> None, out-of-range -> None.
    Never coerces junk to 0.0 (a real 0 and "no rating" are different things).
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if text == "" or text.upper() in {"NEW", "-", "NAN"}:
        return None
    if "/" in text:
        text = text.split("/", 1)[0].strip()
    try:
        value = float(text)
    except ValueError:
        return None
    return value if 0.0 <= value <= 5.0 else None


def parse_cost(raw: object) -> int | None:
    """Normalize a raw cost-for-two into an INR int, or None.

    Handles: "800" -> 800, "1,200" -> 1200, "₹1,200" -> 1200, junk/None -> None.
    """
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "").replace("₹", "").strip()
    if text == "":
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def load_restaurants() -> list[Restaurant]:
    """Load the dataset and return normalized, valid `Restaurant` records.

    Records missing a usable name are skipped (they can't be recommended).
    Missing rating/cost are kept as None — those get excluded per-filter later,
    not dropped outright.
    """
    from datasets import load_dataset

    settings = get_settings()
    started = time.perf_counter()
    logger.info("Loading dataset %s ...", settings.hf_dataset_name)

    ds = load_dataset(settings.hf_dataset_name, split="train")

    restaurants: list[Restaurant] = []
    skipped = 0
    for index, row in enumerate(ds):
        name = (row.get(COL_NAME) or "").strip()
        location = (row.get(COL_LOCATION) or "").strip()
        if not name or not location:
            skipped += 1
            continue

        restaurants.append(
            Restaurant(
                id=f"r{index}",
                name=name,
                location=location,
                city=(row.get(COL_CITY) or "").strip() or None,
                cuisine=(row.get(COL_CUISINES) or "").strip(),
                rating=parse_rating(row.get(COL_RATE)),
                cost_for_two=parse_cost(row.get(COL_COST)),
                rest_type=(row.get(COL_REST_TYPE) or "").strip() or None,
                votes=int(row.get(COL_VOTES) or 0),
                raw=dict(row),
            )
        )

    # Deduplicate: the raw dataset repeats each restaurant once per listing
    # category (EC-D08), producing exact dupes. Keep one record per
    # (name, location), preferring the most-voted (most complete) listing.
    unique: dict[tuple[str, str], Restaurant] = {}
    for r in restaurants:
        key = (r.name.lower(), r.location.lower())
        existing = unique.get(key)
        if existing is None or r.votes > existing.votes:
            unique[key] = r
    deduped = list(unique.values())

    elapsed = time.perf_counter() - started
    logger.info(
        "Loaded %d restaurants (%d duplicates merged, %d skipped) in %.1fs",
        len(deduped),
        len(restaurants) - len(deduped),
        skipped,
        elapsed,
    )
    return deduped
