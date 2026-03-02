'use client'
import { useEffect, useState } from 'react'
import { getAdminQueue, getAdminStats, submitDecision } from '@/lib/api'

interface ReviewItem {
  review_id: string
  return_id: string
  priority: string
  status: string
  escalation_reason: string
  risk_summary: Record<string, unknown>
  ai_recommendation: string
  created_at: string
}
interface Stats {
  total_returns: number
  instant_refunds: number
  escalated: number
  warehouse_routed: number
  p2p_matched: number
  pending_review: number
  automation_rate: number
}
const PRIORITY_BADGE: Record<string, string> = {
  urgent: 'badge-red',
  high:   'badge-red',
  normal: 'badge-yellow',
  low:    'badge-blue',
}

export default function AdminPage() {
  const [queue, setQueue] = useState<ReviewItem[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [selected, setSelected] = useState<ReviewItem | null>(null)
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [toast, setToast] = useState('')

  async function refresh() {
    const [q, s] = await Promise.all([getAdminQueue(), getAdminStats()])
    setQueue(q.queue || [])
    setStats(s)
  }

  useEffect(() => { refresh() }, [])

  async function decide(decision: string) {
    if (!selected) return
    setSubmitting(true)
    await submitDecision(selected.review_id, decision, notes || 'No notes provided.')
    setToast(`Decision "${decision}" submitted`)
    setSelected(null)
    setNotes('')
    await refresh()
    setSubmitting(false)
    setTimeout(() => setToast(''), 3000)
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Human Review Dashboard</h1>
        <p className="text-slate-500 text-sm mt-1">
          Cases where AI explicitly stopped and requested human judgment.
        </p>
      </div>

      {toast && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-2xl px-5 py-4 text-sm font-medium">
          ✓ {toast}
        </div>
      )}

      {/* Stats grid */}
      {stats && (
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {[
            { label: 'Total Returns',   value: stats.total_returns,         gradient: 'from-slate-600 to-slate-700',    bg: 'bg-slate-50' },
            { label: 'Instant Refunds', value: stats.instant_refunds,       gradient: 'from-emerald-500 to-teal-600',   bg: 'bg-emerald-50' },
            { label: 'P2P Matched',     value: stats.p2p_matched,           gradient: 'from-sky-500 to-blue-600',       bg: 'bg-sky-50' },
            { label: 'Escalated',       value: stats.escalated,             gradient: 'from-rose-500 to-pink-600',      bg: 'bg-rose-50' },
            { label: 'Pending Review',  value: stats.pending_review,        gradient: 'from-amber-500 to-orange-500',   bg: 'bg-amber-50' },
            { label: 'Automation Rate', value: `${stats.automation_rate}%`, gradient: 'from-indigo-500 to-violet-600',  bg: 'bg-indigo-50' },
          ].map(s => (
            <div key={s.label} className={`card text-center ${s.bg} border-slate-100`}>
              <p className={`text-2xl font-bold bg-gradient-to-r ${s.gradient} bg-clip-text text-transparent`}>{s.value}</p>
              <p className="text-slate-500 text-xs mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Queue */}
        <div className="space-y-3">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
            Review Queue ({queue.length})
          </h2>
          {queue.length === 0 && (
            <div className="card text-center py-10">
              <p className="text-4xl mb-3">✅</p>
              <p className="font-semibold text-slate-700">All clear!</p>
              <p className="text-sm text-slate-500 mt-1">Run Scenario B to populate the queue.</p>
            </div>
          )}
          {queue.map(item => (
            <button
              key={item.review_id}
              onClick={() => setSelected(item)}
              className={`w-full text-left card transition-all duration-200 hover:shadow-card-hover ${
                selected?.review_id === item.review_id
                  ? 'border-indigo-300 ring-2 ring-indigo-100'
                  : 'hover:border-slate-200'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="text-slate-900 font-semibold text-sm font-mono">{item.return_id.slice(0, 16)}…</p>
                  <p className="text-slate-400 text-xs mt-0.5">
                    {new Date(item.created_at).toLocaleTimeString()}
                  </p>
                </div>
                <span className={PRIORITY_BADGE[item.priority] ?? 'badge-blue'}>{item.priority}</span>
              </div>
              <p className="text-slate-600 text-sm leading-relaxed">{item.escalation_reason}</p>
            </button>
          ))}
        </div>

        {/* Decision panel */}
        {selected ? (
          <div className="card space-y-5">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Reviewer Decision Panel</h2>

            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 space-y-2">
              <p className="text-xs font-semibold text-slate-500 mb-2">Risk Summary</p>
              {Object.entries(selected.risk_summary || {}).map(([k, v]) => (
                <div key={k} className="flex justify-between text-sm">
                  <span className="text-slate-600 capitalize">{k.replace(/_/g, ' ')}</span>
                  <span className={`font-mono text-xs font-semibold ${
                    (k.includes('fraud') && Number(v) > 0.3) ||
                    (k.includes('loss') && Number(v) > 15)
                      ? 'text-rose-600' : 'text-slate-700'
                  }`}>
                    {typeof v === 'number' ? v.toFixed(2) : String(v)}
                  </span>
                </div>
              ))}
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-xs font-semibold text-amber-700 mb-1">AI Recommendation</p>
              <p className="text-slate-700 text-sm leading-relaxed">{selected.ai_recommendation}</p>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-500 mb-1">Why AI Stopped</p>
              <p className="text-slate-700 text-sm leading-relaxed">{selected.escalation_reason}</p>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-500 block mb-2">Reviewer Notes</label>
              <textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                rows={3}
                placeholder="Add your assessment..."
                className="input resize-none"
              />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <button onClick={() => decide('approve')} disabled={submitting} className="btn-success text-sm py-2.5">
                ✓ Approve
              </button>
              <button onClick={() => decide('deny')} disabled={submitting} className="btn-danger text-sm py-2.5">
                ✗ Deny
              </button>
              <button onClick={() => decide('request_inspection')} disabled={submitting} className="btn-secondary text-sm py-2.5">
                Inspect
              </button>
            </div>
          </div>
        ) : (
          <div className="card text-center py-16">
            <p className="text-4xl mb-3">👆</p>
            <p className="font-semibold text-slate-700">Select a review item</p>
            <p className="text-sm text-slate-400 mt-1">Click a queue item to make a decision</p>
          </div>
        )}
      </div>

      {/* Human boundary callout */}
      <div className="card bg-indigo-50 border-indigo-100">
        <div className="flex items-start gap-3">
          <span className="text-2xl mt-0.5">⚖️</span>
          <div>
            <h3 className="font-bold text-indigo-900 mb-1">The Human Boundary — By Design</h3>
            <p className="text-indigo-700 text-sm leading-relaxed">
              This queue exists because the AI explicitly stops at specific thresholds configured by the business —
              not because the AI failed. Items appear here when expected financial loss exceeds $15.00,
              item value exceeds $500, or fraud probability exceeds 75%. The AI surfaces all evidence
              and makes a recommendation. The human makes the final call.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
