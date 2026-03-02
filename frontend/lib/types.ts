export interface Scenario {
  id: string
  title: string
  subtitle: string
  description: string
  badge: string
  badge_color: 'green' | 'red' | 'yellow'
  customer_id: string
  order_id: string
  reason_text: string
  media_urls: string[]
  returner_lat: number
  returner_lng: number
  expected_outcome: string
}

export interface TraceStep {
  tool: string
  input: Record<string, unknown>
  output: Record<string, unknown>
  duration_ms: number
  status: 'completed' | 'error'
}

export interface ReturnResult {
  return_id: string
  status: string
  customer_id: string
  product_id: string
  reason: string
  condition: {
    score: number | null
    grade: string | null
    issues: Array<{ location: string; severity: string; type: string; description: string }>
    authenticity: Record<string, string>
  }
  fraud: {
    probability: number | null
    signals: Array<{ signal: string; value: unknown; weight: string }>
    reasoning: string | null
  }
  refund: {
    decision: string | null
    reasoning: string | null
    expected_loss: number | null
    amount: number | null
    transaction_id: string | null
  }
  matching: {
    p2p_match_order_id: string | null
    match_distance_km: number | null
  }
  routing: {
    decision: string | null
    instructions: Record<string, unknown>
  }
  locker: {
    allocation_id: string
    locker_id: string
    locker_unit: string
    dropoff_qr_hash: string
    pickup_qr_hash: string | null
    allocation_status: string
  } | null
  escalation: {
    review_id: string
    priority: string
    escalation_reason: string
    risk_summary: Record<string, unknown>
    ai_recommendation: string
    queue_status: string
  } | null
  agent_trace: TraceStep[]
}
