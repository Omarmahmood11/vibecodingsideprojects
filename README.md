# 🍅 Sakkath Tindi — AI-Powered Bengaluru Restaurant Finder

An AI-powered restaurant recommendation app for Bengaluru. Describe the vibe you're looking for — *"quiet first date spot with great pasta"* — and the app finds the perfect restaurants using real Zomato data and Google Gemini AI.

🔗 **Live App:** [sakkath-tindi.vercel.app](https://sakkath-tindi.vercel.app)

## How It Works

1. **Pick a neighborhood** — Choose from 90+ Bengaluru areas
2. **Set your budget** — Low (₹<500), Medium (₹500–1500), or High (₹1500+)
3. **Describe what you want** — Free-text like *"big family dinner, great biryani, nothing fussy"*
4. **Get AI-ranked results** — Gemini reads real customer reviews and picks the best matches

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + TypeScript + Vite + Framer Motion |
| Backend | Python + FastAPI |
| AI | Google Gemini Flash (free tier) |
| Data | 12,000+ Bengaluru restaurants from Zomato dataset |
| Hosting | Vercel (frontend) + Render (backend) |

## Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API key ([get one free here](https://aistudio.google.com/apikey))

## Setup

1. **Clone and enter the project:**

   ```bash
   git clone https://github.com/Omarmahmood11/vibecodingsideprojects.git
   cd vibecodingsideprojects
   ```

2. **Backend setup:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your Gemini API key:
   ```
   GEMINI_API_KEY=your_key_here
   ```

4. **Frontend setup:**

   ```bash
   cd frontend
   npm install
   ```

## Run Locally

**Start the backend:**
```bash
uvicorn restaurant_rec.main:app --reload
```
The API starts at `http://127.0.0.1:8000` with docs at `/docs`.

**Start the frontend (in a separate terminal):**
```bash
cd frontend
npm run dev
```
The app opens at `http://localhost:5173`.

## Run Tests

```bash
pytest
```

## Project Structure

```
├── src/restaurant_rec/
│   ├── main.py              # FastAPI entrypoint + CORS
│   ├── config.py            # Settings (pydantic-settings)
│   ├── models/              # Domain DTOs
│   ├── data/                # Dataset loader and in-memory cache
│   ├── services/            # Filter, orchestrator, scoring, metadata
│   ├── llm/                 # Gemini client, prompt builder, JSON parser
│   └── api/                 # Routes and dependencies
├── frontend/
│   └── src/                 # React + TypeScript UI
├── data/
│   └── restaurants_v2.jsonl # Pre-enriched dataset with review snippets
└── docs/                    # Architecture docs and case studies
```

## Key Features

- **AI-Grounded Explanations** — Recommendations cite real customer reviews, not hallucinated text
- **Graceful Degradation** — Falls back to rule-based ranking if the AI is rate-limited
- **Smart Filtering** — Automatically relaxes cuisine/budget filters if too few matches are found
- **Rate-Limit Safe** — Button disables during searches to prevent API spam

## Documentation

See the [`docs/`](./docs/) folder:

- [`context.md`](./docs/context.md) — Project requirements
- [`Architecture.md`](./docs/Architecture.md) — Technical architecture
- [`ImplementationPlan.md`](./docs/ImplementationPlan.md) — Phase-wise build plan
