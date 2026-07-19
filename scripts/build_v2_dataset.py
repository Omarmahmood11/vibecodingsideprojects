"""Build the v2 enriched dataset (Phase v2 data prep).

Streams the full Kaggle "Zomato Bangalore Restaurants" CSV *straight out of its
zip* (never extracting the 548MB file to disk), then distills each restaurant
down to a small, grounded record:

    name, location, cuisine, rating, votes, cost, rest_type, dish_liked,
    review_snippets  <- a few short, cleaned, ambiance-relevant real reviews

The review snippets are what let the LLM make *grounded* claims about vibe
("reviewers mention it's quiet / great interiors") instead of inventing them.
Distillation is plain text heuristics (no LLM) so it runs once, offline, free.

Usage:
    python scripts/build_v2_dataset.py /path/to/archive.zip

Output: data/restaurants_v2.jsonl  (one JSON restaurant per line)
"""

import ast
import csv
import io
import json
import re
import sys
import zipfile
from pathlib import Path

try:
    from ftfy import fix_text  # fixes mojibake in the review text
except ImportError:  # pragma: no cover - ftfy is a project dep
    def fix_text(s: str) -> str:
        return s

csv.field_size_limit(sys.maxsize)  # reviews_list cells are huge

SNIPPETS_PER_PLACE = 3
SNIPPET_MAX_CHARS = 240
MIN_SNIPPET_CHARS = 40

# Words that signal a review is talking about atmosphere/experience (the stuff
# our structured fields can't capture). We prefer these reviews when distilling.
VIBE_WORDS = {
    "ambience", "ambiance", "cozy", "cosy", "quiet", "romantic", "lively",
    "crowd", "crowded", "interior", "interiors", "decor", "rooftop", "view",
    "music", "vibe", "seating", "spacious", "intimate", "family", "date",
    "peaceful", "calm", "noisy", "loud", "outdoor", "garden", "aesthetic",
    "lighting", "cocktails", "service", "staff", "buffet",
}
_word_re = re.compile(r"[a-z]+")


# Mojibake building-block chars that survive ftfy when the source was encoded
# inconsistently multiple times (e.g. "Donâ€Ã'™t" for "Don't"). None are legit
# in this English/Indian review text, so we drop them and tidy the leftovers.
_RESIDUE = {ord(c): None for c in "â€ÃÂƒ™‚"}


def _strip_residue(text: str) -> str:
    text = text.translate(_RESIDUE)
    text = re.sub(r"['’]{2,}", "'", text)  # collapse doubled apostrophes
    return text


def clean_field(value: object) -> str:
    """Repair encoding damage (mojibake) in a structured field. See EC-D10."""
    return _strip_residue(fix_text(str(value or ""))).strip()


def clean_review(text: str) -> str:
    text = _strip_residue(fix_text(text))
    text = text.replace("RATED\n", " ").replace("RATED", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def vibe_score(text: str) -> int:
    words = set(_word_re.findall(text.lower()))
    return len(words & VIBE_WORDS)


def parse_reviews(raw: str) -> list[str]:
    """reviews_list is a stringified list of ('Rated x', 'RATED\\n text') tuples."""
    if not raw or raw in ("[]", "nan"):
        return []
    try:
        parsed = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return []
    out = []
    for item in parsed:
        if isinstance(item, (list, tuple)) and len(item) == 2 and item[1]:
            cleaned = clean_review(str(item[1]))
            if len(cleaned) >= MIN_SNIPPET_CHARS:
                out.append(cleaned)
    return out


def pick_snippets(reviews: list[str]) -> list[str]:
    """Prefer ambiance-rich reviews; keep them short and de-duplicated."""
    seen: set[str] = set()
    unique = []
    for r in reviews:
        key = r[:80].lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    # rank by how much vibe signal they carry, then prefer concise ones
    unique.sort(key=lambda r: (vibe_score(r), -len(r)), reverse=True)
    return [r[:SNIPPET_MAX_CHARS].rstrip() + ("..." if len(r) > SNIPPET_MAX_CHARS else "")
            for r in unique[:SNIPPETS_PER_PLACE]]


def parse_rating(raw: str) -> float | None:
    if not raw:
        return None
    m = re.match(r"\s*([0-9](?:\.[0-9])?)\s*/\s*5", raw)
    return float(m.group(1)) if m else None


def parse_int(raw: str) -> int | None:
    if not raw:
        return None
    digits = re.sub(r"[^0-9]", "", raw)
    return int(digits) if digits else None


def main(zip_path: str) -> None:
    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "restaurants_v2.jsonl"

    # (name, location) -> aggregated record with incremental top-K snippets
    places: dict[tuple[str, str], dict] = {}
    rows = 0

    with zipfile.ZipFile(zip_path) as z:
        name_in_zip = next(n for n in z.namelist() if n.endswith(".csv"))
        with z.open(name_in_zip) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", errors="replace"))
            for row in reader:
                rows += 1
                name = clean_field(row.get("name"))
                location = clean_field(row.get("location"))
                if not name or not location:
                    continue
                key = (name.lower(), location.lower())

                votes = parse_int(row.get("votes")) or 0
                rec = places.get(key)
                if rec is None:
                    rec = places[key] = {
                        "name": name,
                        "location": location,
                        "cuisine": clean_field(row.get("cuisines")),
                        "rating": parse_rating(row.get("rate")),
                        "votes": votes,
                        "cost_for_two": parse_int(row.get("approx_cost(for two people)")),
                        "rest_type": clean_field(row.get("rest_type")),
                        "dish_liked": clean_field(row.get("dish_liked")),
                        "_reviews": [],
                    }
                # richer duplicate wins for the structured fields
                if votes >= rec["votes"]:
                    rec["votes"] = votes
                    rec["rating"] = parse_rating(row.get("rate")) or rec["rating"]
                    if row.get("dish_liked"):
                        rec["dish_liked"] = clean_field(row.get("dish_liked"))

                # accumulate reviews, keeping only a bounded, best pool per place
                rec["_reviews"].extend(parse_reviews(row.get("reviews_list") or ""))
                if len(rec["_reviews"]) > 40:  # bound memory
                    rec["_reviews"] = pick_snippets(rec["_reviews"])

    written = 0
    with out_path.open("w", encoding="utf-8") as f:
        for rec in places.values():
            rec["review_snippets"] = pick_snippets(rec.pop("_reviews"))
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1

    size_mb = out_path.stat().st_size / 1e6
    with_reviews = sum(1 for r in places.values() if r["review_snippets"])
    print(f"rows read:        {rows}")
    print(f"unique places:    {written}")
    print(f"with >=1 snippet: {with_reviews} ({100*with_reviews//max(written,1)}%)")
    print(f"output:           {out_path}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/build_v2_dataset.py <archive.zip>")
    main(sys.argv[1])
