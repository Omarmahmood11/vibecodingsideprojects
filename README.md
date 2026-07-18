# Restaurant Recommendation API

AI-powered restaurant recommendation system inspired by Zomato. Combines structured Zomato dataset filtering with LLM-based ranking and explanations.

## Prerequisites

- Python 3.11+
- OpenAI API key (required from Phase 3 onward)

## Setup

1. **Clone and enter the project:**

   ```bash
   cd vibecodingsideprojects
   ```

2. **Create a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -e ".[dev]"
   ```

   Or using `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio ruff
   ```

4. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your values (at minimum `OPENAI_API_KEY` for later phases).

## Run the API

```bash
uvicorn restaurant_rec.main:app --reload
```

The server starts at `http://127.0.0.1:8000`.

- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Run Tests

```bash
pytest
```

## Project Structure

```
src/restaurant_rec/
├── main.py              # FastAPI entrypoint
├── config.py            # Settings (pydantic-settings)
├── models/              # Domain DTOs
├── data/                # Dataset loader and cache
├── services/            # Filter, orchestrator, metadata
├── llm/                 # LLM client, prompts, parser
└── api/                 # Routes and dependencies
```

## Documentation

See the [`docs/`](./docs/) folder:

- [`context.md`](./docs/context.md) — Project requirements
- [`Architecture.md`](./docs/Architecture.md) — Technical architecture
- [`ImplementationPlan.md`](./docs/ImplementationPlan.md) — Phase-wise build plan
- [`edge-case.md`](./docs/edge-case.md) — Edge case handling guide

## Current Phase

**Phase 0 — Project Foundation** ✓

- FastAPI app with `GET /health`
- Project scaffold and configuration
- Dev tooling (pytest, ruff)
