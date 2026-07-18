export type Budget = 'low' | 'medium' | 'high'

export interface Preferences {
  location: string
  budget?: Budget | null
  cuisine?: string | null
  min_rating?: number
  additional_preferences?: string | null
  top_k?: number
}

export interface Recommendation {
  rank: number
  restaurant_id: string
  name: string
  cuisine: string
  rating: number | null
  estimated_cost: string
  location: string
  explanation: string
}

export interface RecommendationResponse {
  summary: string
  recommendations: Recommendation[]
  metadata: {
    llm_fallback?: boolean
    candidates_considered?: number
    model?: string
    latency_ms?: number
    cuisine_relaxed?: boolean
    budget_relaxed?: boolean
  }
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function fetchLocations(): Promise<string[]> {
  const res = await fetch('/metadata/locations')
  if (!res.ok) throw new ApiError(res.status, 'Could not load neighborhoods')
  return res.json()
}

export async function getRecommendations(prefs: Preferences): Promise<RecommendationResponse> {
  const res = await fetch('/recommendations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(prefs),
  })
  if (!res.ok) {
    let detail = 'Something went wrong. Please try again.'
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail)
  }
  return res.json()
}
