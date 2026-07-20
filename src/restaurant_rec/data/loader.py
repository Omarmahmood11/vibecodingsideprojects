"""Load and normalize the Zomato dataset from Hugging Face.

The raw dataset (ManikaSaini/zomato-restaurant-recommendation) has messy,
string-typed fields. This module is the *only* place that knows about those
raw quirks; everything downstream works with clean `Restaurant` objects.
"""

import json
import logging
import time
from pathlib import Path

import ftfy

from ..config import get_settings
from ..models.restaurant import Restaurant

logger = logging.getLogger(__name__)

# v2 enriched dataset: pre-cleaned, deduped, with grounded review snippets.
# Built once via scripts/build_v2_dataset.py. Preferred when present.
_cwd_data = Path.cwd() / "data" / "restaurants_v2.jsonl"
_file_data = Path(__file__).resolve().parents[3] / "data" / "restaurants_v2.jsonl"
V2_DATA_FILE = _cwd_data if _cwd_data.exists() else _file_data


def _clean(text: object) -> str:
    """Strip and repair common text-encoding damage (EC-D10). ~0.6% of names."""
    return ftfy.fix_text(str(text or "")).strip()

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
    """Load restaurants, preferring the v2 enriched local file over Hugging Face.

    v2 (data/restaurants_v2.jsonl) is already cleaned, deduped, and carries real
    review snippets for grounded explanations. If it's missing, fall back to
    loading + normalizing the raw Hugging Face dataset (v1 behavior).
    """
    if V2_DATA_FILE.exists():
        return _load_from_v2_file()
    logger.info("v2 data file not found; falling back to Hugging Face loader")
    return _load_from_huggingface()


def _load_from_v2_file() -> list[Restaurant]:
    """Load the pre-built enriched JSONL (fast, offline, grounded)."""
    started = time.perf_counter()
    logger.info("Loading v2 enriched dataset from %s ...", V2_DATA_FILE)

    restaurants: list[Restaurant] = []
    with V2_DATA_FILE.open(encoding="utf-8") as f:
        for index, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            name = (rec.get("name") or "").strip()
            location = (rec.get("location") or "").strip()
            if not name or not location:
                continue
            restaurants.append(
                Restaurant(
                    id=f"r{index}",
                    name=name,
                    location=location,
                    cuisine=(rec.get("cuisine") or "").strip(),
                    rating=rec.get("rating"),
                    cost_for_two=rec.get("cost_for_two"),
                    rest_type=(rec.get("rest_type") or None),
                    votes=int(rec.get("votes") or 0),
                    dish_liked=(rec.get("dish_liked") or "").strip(),
                    review_snippets=rec.get("review_snippets") or [],
                )
            )

    with_reviews = sum(1 for r in restaurants if r.review_snippets)
    logger.info(
        "Loaded %d restaurants (%d with review snippets) from v2 file in %.1fs",
        len(restaurants),
        with_reviews,
        time.perf_counter() - started,
    )
    return restaurants


def _load_from_huggingface() -> list[Restaurant]:
    """Load + normalize the raw Hugging Face dataset (v1 fallback path)."""
    from datasets import load_dataset

    settings = get_settings()
    started = time.perf_counter()
    logger.info("Loading dataset %s ...", settings.hf_dataset_name)

    ds = load_dataset(settings.hf_dataset_name, split="train")

    restaurants: list[Restaurant] = []
    skipped = 0
    for index, row in enumerate(ds):
        name = _clean(row.get(COL_NAME))
        location = _clean(row.get(COL_LOCATION))
        if not name or not location:
            skipped += 1
            continue

        restaurants.append(
            Restaurant(
                id=f"r{index}",
                name=name,
                location=location,
                city=_clean(row.get(COL_CITY)) or None,
                cuisine=_clean(row.get(COL_CUISINES)),
                rating=parse_rating(row.get(COL_RATE)),
                cost_for_two=parse_cost(row.get(COL_COST)),
                rest_type=_clean(row.get(COL_REST_TYPE)) or None,
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
