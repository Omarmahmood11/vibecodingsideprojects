# Sakkath Tindi — Case Study

**An AI restaurant recommender for Bengaluru, and what building it taught me about when an LLM actually earns its place.**

*"Sakkath tindi" is Bengaluru slang for "awesome food."*

---

## The brief

The assignment: build an AI-powered restaurant recommender inspired by Zomato. Take a user's preferences (location, budget, cuisine, rating, plus free-text like "family-friendly"), filter a real Zomato dataset, then use an LLM to **rank the results, explain why each one fits, and summarize the set.**

It pointed at a specific Hugging Face dataset and expected a working end-to-end app.

## What I built (v1)

A complete full-stack app, faithful to the brief:

- **Data layer:** load and normalize ~51k messy Zomato rows into ~12k clean restaurants (string ratings like "4.1/5", costs like "1,200", encoding damage, duplicate listings).
- **Filtering:** deterministic pre-filter by neighborhood, budget, rating, cuisine, with graceful relaxation when too few match.
- **LLM step:** Gemini ranks the candidates and writes a "why this pick" explanation for each, with the user's free-text intent as the primary signal.
- **API:** FastAPI, one clean `/recommendations` endpoint, typed errors mapped to HTTP codes.
- **Frontend:** a React interface where you describe your evening in plain language and get three grounded picks.

It worked. It met every line of the brief.

## The question that actually mattered

Instead of shipping v1 and calling it done, I asked the question that separates executing a spec from evaluating one:

> Does the LLM actually do something the data and a simple sort couldn't? And are its explanations even *true*?

## The eval that changed the project

I audited v1's own output. The finding was structural and damning:

- The dataset has fields for name, cuisine, rating, cost, location, and type. **It has nothing about atmosphere, noise, decor, or crowd.**
- So when a user searched "quiet romantic first date" and v1 answered *"quiet and visually stunning, a perfect backdrop for a first date,"* the model was **inventing** those claims from the restaurant's name and cuisine.
- Across the sample, factual claims (rating, price, cuisine) were grounded. **Nearly 100% of experiential claims (quiet, cozy, romantic, lively) were ungrounded.**
- And those were exactly the claims users lean on. The AI was most confident precisely where it had no evidence.

The deeper insight: the flaw was baked into the brief. It asked the model to justify "fit" and handle vibe-y preferences, but paired that with a dataset that could not support such claims. "Generate an explanation" and "generate a *true* explanation" are different bars, and the data only supported the first.

## v2: grounding it in real reviews

The fix was not a fancier model. It was better data.

The dataset I was given turned out to be a stripped-down copy of a fuller Kaggle dataset: the *same* Bengaluru restaurants, but with a `reviews_list` column of real customer reviews. Reviews are exactly where people describe atmosphere.

What I did:

1. **Streamed** the 548 MB source straight out of its zip and distilled each restaurant down to a few ambiance-relevant review snippets, offline, with plain text heuristics (no LLM, so it runs once and free). Output: a 7.8 MB file, deduped to the same 12,094 restaurants, 80% with real review snippets. The 548 MB file never touched disk.
2. **Fed those snippets to the model** at query time and required every vibe claim to be grounded in them, with instructions to *not* invent atmosphere when a place has no reviews.

The result, same query, before and after:

- **v1 (invented):** *"quiet and visually stunning, a perfect backdrop for a first date."*
- **v2 (grounded):** *"A reviewer specifically notes that even though it is on a main road, it keeps the noise of the busy street away, offering a quiet, cozy cafe environment filled with green plants."*

The claims now trace back to real reviews instead of being confabulated. That is the whole point of the app finally being true.

## Engineering decisions worth noting

- **Graceful degradation:** if the LLM is unavailable, the app never breaks. It falls back to rating-ranked results with plain descriptions, so a user always gets real recommendations.
- **Honest observability:** the app kept logging "invalid JSON" failures. On inspection they were not malformed JSON at all, they were rate-limit rejections mislabeled. I fixed the labeling to report the real cause, and stopped the code from retrying (and burning quota) on those.
- **Latency:** disabling the model's "thinking" mode for this ranking task cut a call from ~8s to ~2s.
- **Cost discipline:** the distillation is offline and LLM-free, because doing it per restaurant would have been 12k model calls against a 20/day free-tier limit.

## Honest limitations

- **Free-tier quota:** ~20 AI searches per day, with a per-minute cap. Fine for personal use, not for a public demo without paid inference.
- **Stale data:** the reviews are from 2019.
- **Distillation is heuristic:** snippet selection is keyword-based, not perfect.
- **Grounding cost:** v2 latency rose to ~16s because the prompt now carries review snippets for every candidate. Tunable.
- **Not yet fully measured:** I have strong qualitative before/after evidence. A larger quantitative v1-vs-v2 grounding eval is the next step, currently constrained by the free-tier quota.

## What I would do next

- Run a quantitative eval (grounded-vs-invented claim rate, v1 vs v2, across ~20 queries).
- Use reviews for *filtering*, not just explaining ("only show places reviewers call quiet").
- Trim latency by sending snippets only for a shortlist.
- Fresher data, and paid inference for a reliable public demo.

## The takeaway

The most valuable thing I learned is not that I can wire an LLM into an app. It is knowing when the LLM is garnish and when it is genuine:

- An LLM earns its place when it does something code cannot **and** its output is grounded in data that makes it true.
- The value is capped by the data you feed it. LLM plus thin data is plausible filler. LLM plus real reviews is something a filter and a sort could never produce.
- Meeting a spec and meeting the need are different. The interesting work was noticing the gap, measuring it, and closing it.
