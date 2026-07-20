import { useEffect, useState } from 'react'
import { AnimatePresence, motion, type Variants } from 'framer-motion'
import {
  ApiError,
  fetchLocations,
  getRecommendations,
  type Budget,
  type RecommendationResponse,
} from './api'
import { NeighborhoodPicker } from './components/NeighborhoodPicker'
import { PlaceCard } from './components/PlaceCard'

const BUDGETS: { label: string; sub?: string; value: Budget | null }[] = [
  { label: 'Any', value: null },
  { label: '₹', sub: '<500', value: 'low' },
  { label: '₹₹', sub: '500 to 1500', value: 'medium' },
  { label: '₹₹₹', sub: '1500+', value: 'high' },
]

const RATINGS = [
  { label: 'Any', value: 0 },
  { label: '3.5★', value: 3.5 },
  { label: '4★', value: 4 },
  { label: '4.5★', value: 4.5 },
]

const EXAMPLES = [
  { text: 'casual catch-up over coffee and pizza, lively but not too loud', loc: 'Koramangala' },
  { text: 'impressive but not pricey first date, somewhere quiet', loc: 'Indiranagar' },
  { text: 'big family dinner, great biryani, nothing fussy', loc: 'Whitefield' },
]

// staggered reveal for the shortlist
const listContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09, delayChildren: 0.04 } },
}

// Collapse sub-divided areas (e.g. "Koramangala 5th Block") to their base name
// ("Koramangala") for a cleaner, consistent dropdown. The backend filter matches
// by substring, so selecting the base still covers every block behind the scenes.
function collapseLocations(locs: string[]): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  for (const l of locs) {
    const base = l.replace(/\s+\d+(st|nd|rd|th)?\s+(Block|Phase|Stage|Sector)\b.*$/i, '').trim()
    if (!seen.has(base)) {
      seen.add(base)
      out.push(base)
    }
  }
  return out
}

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
      .then((locs) => setLocations(collapseLocations(locs)))
      .catch(() => setLocations([]))
  }, [])

  async function run() {
    if (!location || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await getRecommendations({
        location,
        budget,
        min_rating: minRating,
        additional_preferences: intent.trim() || null,
        top_k: 5,
      })
      setResult(data)
    } catch (e) {
      const err = e as ApiError
      setError({ status: err.status ?? 0, message: err.message })
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setResult(null)
    setError(null)
  }

  const relaxed = result?.metadata.cuisine_relaxed || result?.metadata.budget_relaxed

  return (
    <>
      <div className="aurora">
        <span className="blob b1" />
        <span className="blob b2" />
        <span className="blob b3" />
        <span className="blob b4" />
      </div>

      <div className="page">
        <header className="topbar">
          <div className="brand">
            <span className="mark">🍅</span>
            <span>sakkath tindi</span>
          </div>
        </header>

        <motion.section
          className="hero"
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          <span className="eyebrow">📍 Bengaluru</span>
          <h1>
            What are you <span className="accent">in the mood for?</span>
          </h1>
          <p>
            Skip the endless scroll. Describe your evening and get three spots worth going to.
          </p>
        </motion.section>

        <motion.section
          className="console"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className="console-top">
            <div className="intent-wrap">
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
            </div>
            <motion.button
              className="go"
              onClick={run}
              disabled={!location || loading}
              whileTap={{ scale: 0.97 }}
            >
              {loading ? 'Finding…' : 'Find spots'}
              {!loading && <span className="arrow">→</span>}
            </motion.button>
          </div>

          <div className="rail">
            <div className="group">
              <span className="glabel">Area</span>
              <NeighborhoodPicker value={location} options={locations} onChange={setLocation} />
            </div>

            <div className="group">
              <span className="glabel">Budget for two</span>
              <div className="segmented" role="group" aria-label="Budget">
                {BUDGETS.map((b) => (
                  <button
                    key={b.label}
                    aria-pressed={budget === b.value}
                    onClick={() => setBudget(b.value)}
                  >
                    {b.label}
                    {b.sub && <small>{b.sub}</small>}
                  </button>
                ))}
              </div>
            </div>

            <div className="group">
              <span className="glabel">Min rating</span>
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
            </div>
          </div>
        </motion.section>

        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loading"
              className="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <span>Tasting the options for you</span>
              <span className="dots">
                <i />
                <i />
                <i />
              </span>
            </motion.div>
          ) : error ? (
            <motion.div
              key="error"
              className="notice error"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div className="big">
                {error.status === 404 ? 'No matches for that' : 'Something went wrong'}
              </div>
              <p>{error.message}</p>
            </motion.div>
          ) : result ? (
            <motion.section
              key="results"
              className="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="results-head">
                <span className="eyebrow">Your shortlist</span>
                <button className="again" onClick={reset}>
                  ↻ Start over
                </button>
              </div>
              <p className="summary">{result.summary}</p>
              {relaxed && (
                <span className="relaxed">
                  Few exact matches, so we widened the search a little to find these.
                </span>
              )}

              <motion.div
                className="card-list"
                variants={listContainer}
                initial="hidden"
                animate="show"
              >
                {result.recommendations.map((rec) => (
                  <PlaceCard key={rec.restaurant_id} rec={rec} />
                ))}
              </motion.div>

              <div className="foot">
                Considered <span className="num">{result.metadata.candidates_considered}</span> spots
                {result.metadata.llm_fallback ? ' · ranked by rating' : ' · picked by AI'}
              </div>
            </motion.section>
          ) : (
            <motion.div
              key="examples"
              className="examples"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <span className="lbl">Not sure? Try one of these</span>
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
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  )
}
