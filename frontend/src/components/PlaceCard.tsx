import type { Recommendation } from '../api'

export function PlaceCard({ rec, delay }: { rec: Recommendation; delay: number }) {
  return (
    <article className="card" style={{ animationDelay: `${delay}ms` }}>
      <div className="rank num">{rec.rank}</div>
      <div>
        <h3>{rec.name}</h3>
        <div className="meta">
          {rec.rating != null && (
            <span className="num">
              <span className="star">★</span> {rec.rating.toFixed(1)}
            </span>
          )}
          <span className="sep">·</span>
          <span className="num">{rec.estimated_cost}</span>
          <span className="sep">·</span>
          <span>{rec.location}</span>
          <span className="sep">·</span>
          <span className="cuisine">{rec.cuisine}</span>
        </div>
        <div className="note">
          <span className="why">Why this pick</span>
          <p>{rec.explanation}</p>
        </div>
      </div>
    </article>
  )
}
