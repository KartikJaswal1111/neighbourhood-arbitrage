const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function getScenarios() {
  const r = await fetch(`${BASE}/api/v1/demo/scenarios`)
  return r.json()
}

export async function initiateReturn(payload: {
  customer_id: string
  order_id: string
  reason_text: string
  media_urls: string[]
  returner_lat: number
  returner_lng: number
}) {
  const r = await fetch(`${BASE}/api/v1/returns/initiate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getReturn(returnId: string) {
  const r = await fetch(`${BASE}/api/v1/returns/${returnId}`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function simulateLockerDropoff(returnId: string) {
  const r = await fetch(`${BASE}/api/v1/returns/${returnId}/simulate-locker-dropoff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ locker_ai_score: 83, weight_match: true, camera_match: true })
  })
  return r.json()
}

export async function getAdminQueue() {
  const r = await fetch(`${BASE}/api/v1/admin/queue`)
  return r.json()
}

export async function getAdminStats() {
  const r = await fetch(`${BASE}/api/v1/admin/stats`)
  return r.json()
}

export async function submitDecision(reviewId: string, decision: string, notes: string) {
  const r = await fetch(`${BASE}/api/v1/admin/queue/${reviewId}/decide`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer_id: 'demo-reviewer', decision, notes })
  })
  return r.json()
}
