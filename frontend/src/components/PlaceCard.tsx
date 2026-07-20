import { motion, type Variants } from 'framer-motion'
import type { Recommendation } from '../api'

const item: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 28 },
  },
}

function matchTier(score: number): string {
  if (score >= 80) return 'high'
  if (score >= 60) return 'mid'
  return 'low'
}

export function PlaceCard({ rec }: { rec: Recommendation }) {
  const mapsUrl =
    'https://www.google.com/maps/search/?api=1&query=' +
    encodeURIComponent(`${rec.name}, ${rec.location}, Bengaluru`)

  return (
    <motion.article
      className={`card${rec.rank === 1 ? ' top' : ''}`}
      variants={item}
      whileHover={{ y: -4 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
    >
      <div className="rank num">{rec.rank}</div>
      <div>
        <div className="card-head">
          <h3>{rec.name}</h3>
          <a className="maps-link" href={mapsUrl} target="_blank" rel="noopener noreferrer">
            <span className="pin">📍</span> Maps
            <span className="ext">↗</span>
          </a>
        </div>
        <div className="chips">
          <span className={`metachip match ${matchTier(rec.match_score)}`}>
            <span className="num">{rec.match_score}%</span> match
          </span>
          {rec.rating != null && (
            <span className="metachip rating num">
              <span className="star">★</span> {rec.rating.toFixed(1)}
            </span>
          )}
          <span className="metachip num">{rec.estimated_cost}</span>
          <span className="metachip">{rec.location}</span>
          <span className="metachip cuisine">{rec.cuisine}</span>
        </div>
        <div className="note">
          <span className="why">Why this pick</span>
          <p>{rec.explanation}</p>
        </div>
        {rec.match_reasons.length > 0 && (
          <div className="match-reasons">
            Matches your ask: {rec.match_reasons.map((t) => `“${t}”`).join(' · ')}
          </div>
        )}
      </div>
    </motion.article>
  )
}
