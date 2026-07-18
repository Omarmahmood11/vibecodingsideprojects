import type { Recommendation } from '../api'

export function PlaceCard({ rec, delay }: { rec: Recommendation; delay: number }) {
  return (
    <article className={`card${rec.rank === 1 ? ' top' : ''}`} style={{ animationDelay: `${delay}ms` }}>
      <div className="rank num">{rec.rank}</div>
      <div>
        <h3>{rec.name}</h3>
        <div className="chips">
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
      </div>
    </article>
  )
}
