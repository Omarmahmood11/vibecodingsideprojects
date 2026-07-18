import { useEffect, useState } from 'react'
import {
  ApiError,
  fetchLocations,
  getRecommendations,
  type Budget,
  type RecommendationResponse,
} from './api'
import { NeighborhoodPicker } from './components/NeighborhoodPicker'
import { PlaceCard } from './components/PlaceCard'

const BUDGETS: { label: string; value: Budget | null }[] = [
  { label: 'Any', value: null },
  { label: '₹', value: 'low' },
  { label: '₹₹', value: 'medium' },
  { label: '₹₹₹', value: 'high' },
]

const RATINGS = [
  { label: 'Any', value: 0 },
  { label: '3.5+', value: 3.5 },
  { label: '4.0+', value: 4 },
  { label: '4.5+', value: 4.5 },
]

const EXAMPLES = [
  { text: 'casual catch-up over coffee and pizza, lively but not too loud', loc: 'Koramangala' },
  { text: 'impressive but not pricey first date, ideally quiet', loc: 'Indiranagar' },
  { text: 'big family dinner, great biryani, not fussy', loc: 'Whitefield' },
]

export default function App() {
  const [locations, setLocations] = useState<string[]>([])
  const [location, setLocation] = useState('')
  const [budget, setBudget] = useState<Budget | null>(null)
  const [minRating, setMinRating] = useState(0)
  const [intent, setIntent] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<{ status: number; message: string } | null>(null)
  const [result, setResult] = useState<RecommendationResponse | null>(null)

  useEffect(() => {
    fetchLocations()
      .then(setLocations)
      .catch(() => setLocations([]))
  }, [])

  async function run() {
    if (!location) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await getRecommendations({
        location,
        budget,
        min_rating: minRating,
        additional_preferences: intent.trim() || null,
        top_k: 3,
      })
      setResult(data)
    } catch (e) {
      const err = e as ApiError
      setError({ status: err.status ?? 0, message: err.message })
    } finally {
      setLoading(false)
    }
  }

  const relaxed = result?.metadata.cuisine_relaxed || result?.metadata.budget_relaxed

  return (
    <div className="page">
      <header className="masthead">
        <span className="dot">🍅</span>
        <span>Nombu</span>
        <span className="city">Bangalore</span>
      </header>

      <section className="hero">
        <h1>
          Tell me what you're <span className="accent">in the mood for.</span>
        </h1>
        <p>Skip the endless scroll. Describe your evening — get three places worth going to.</p>
      </section>

      <section className="composer">
        <label className="intent-label" htmlFor="intent">
          Your table for the evening
        </label>
        <textarea
          id="intent"
          className="intent"
          rows={2}
          placeholder="e.g. somewhere impressive but not too pricey for a first date, not too loud…"
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) run()
          }}
        />
        <div className="filters">
          <NeighborhoodPicker value={location} options={locations} onChange={setLocation} />

          <div className="segmented" role="group" aria-label="Budget">
            {BUDGETS.map((b) => (
              <button
                key={b.label}
                aria-pressed={budget === b.value}
                onClick={() => setBudget(b.value)}
              >
                {b.label}
              </button>
            ))}
          </div>

          <div className="segmented" role="group" aria-label="Minimum rating">
            {RATINGS.map((r) => (
              <button
                key={r.label}
                aria-pressed={minRating === r.value}
                onClick={() => setMinRating(r.value)}
              >
                {r.label}
              </button>
            ))}
          </div>

          <button className="go" onClick={run} disabled={!location || loading}>
            {loading ? 'Finding…' : 'Find me a place'}
          </button>
        </div>
      </section>

      {!result && !loading && !error && (
        <div className="examples">
          <span>Try:</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex.text}
              className="chip"
              onClick={() => {
                setIntent(ex.text)
                setLocation(ex.loc)
              }}
            >
              {ex.text}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div className="loading">
          <span>Tasting the options for you</span>
          <span className="dots">
            <i />
            <i />
            <i />
          </span>
        </div>
      )}

      {error && (
        <div className="notice error">
          <div className="big">
            {error.status === 404 ? 'No matches for that' : 'Something went wrong'}
          </div>
          <p>{error.message}</p>
        </div>
      )}

      {result && (
        <section className="results">
          <div className="lead">
            <span className="eyebrow">Your shortlist</span>
            <p>{result.summary}</p>
            {relaxed && (
              <span className="relaxed">
                Few exact matches — we widened the search a little to find these.
              </span>
            )}
          </div>

          <div className="card-list">
            {result.recommendations.map((rec, i) => (
              <PlaceCard key={rec.restaurant_id} rec={rec} delay={i * 90} />
            ))}
          </div>

          <div className="foot">
            Considered <span className="num">{result.metadata.candidates_considered}</span> spots
            {result.metadata.llm_fallback ? ' · ranked by rating' : ' · picked by AI'}
          </div>
        </section>
      )}
    </div>
  )
}
