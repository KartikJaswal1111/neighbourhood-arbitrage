'use client'
import { useEffect, useState, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getReturn } from '@/lib/api'
import type { ReturnResult } from '@/lib/types'
import AgentTrace from '@/components/AgentTrace'
import ConditionReport from '@/components/ConditionReport'
import RefundDecision from '@/components/RefundDecision'
import LockerFlow from '@/components/LockerFlow'

const STATUS_LABEL: Record<string, { label: string; badge: string; icon: string }> = {
  analyzing:             { label: 'AI Analysis Running',      badge: 'badge-indigo', icon: '⚡' },
  awaiting_locker_dropoff: { label: 'Awaiting Locker Drop-off', badge: 'badge-yellow', icon: '🔒' },
  refund_issued:         { label: 'Refund Issued',             badge: 'badge-green',  icon: '✅' },
  escalated:             { label: 'Human Review',              badge: 'badge-red',    icon: '🚨' },
  warehouse_routed:      { label: 'Warehouse Route',           badge: 'badge-yellow', icon: '🏭' },
  no_match_routed:       { label: 'No Match — Routed',         badge: 'badge-blue',   icon: '📦' },
  error:                 { label: 'Error',                     badge: 'badge-red',    icon: '⚠️' },
}

export default function ResultPage() {
  const { returnId } = useParams<{ returnId: string }>()
  const router = useRouter()
  const [data, setData] = useState<ReturnResult | null>(null)
  const [error, setError] = useState('')

  const poll = useCallback(async () => {
    try {
      const result = await getReturn(returnId)
      setData(result)
      return result.status
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch return')
      return 'error'
    }
  }, [returnId])

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>
    const start = async () => {
      const status = await poll()
      if (status === 'analyzing') {
        interval = setInterval(async () => {
          const s = await poll()
          if (s !== 'analyzing') clearInterval(interval)
        }, 2500)
      }
    }
    start()
    return () => clearInterval(interval)
  }, [poll])

  const status = data?.status || 'analyzing'
  const meta = STATUS_LABEL[status] || STATUS_LABEL.analyzing

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => router.push('/')}
            className="text-slate-500 hover:text-indigo-600 text-sm mb-2 flex items-center gap-1 transition-colors font-medium"
          >
            ← Back to scenarios
          </button>
          <h1 className="text-2xl font-bold text-slate-900">Return Analysis</h1>
          <p className="text-slate-400 text-sm font-mono mt-0.5">{returnId}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-2xl">{meta.icon}</span>
          <div>
            <span className={meta.badge}>{meta.label}</span>
            {status === 'analyzing' && (
              <p className="text-xs text-slate-400 mt-1">AI agent working… ~30s</p>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-2xl px-5 py-4 text-sm font-medium">{error}</div>
      )}

      {/* Analyzing state — loading skeleton */}
      {status === 'analyzing' && !data?.agent_trace?.length && (
        <div className="card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-6 h-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
            <span className="text-indigo-600 font-semibold">Agent analyzing return…</span>
          </div>
          {['Vision inspection', 'Trust profile', 'Fraud signals', 'Nearby buyers', 'Hub search', 'Risk calculation'].map(step => (
            <div key={step} className="flex items-center gap-3 py-2.5 border-b border-slate-100 last:border-0">
              <div className="w-3.5 h-3.5 rounded-full bg-slate-200 animate-pulse" />
              <span className="text-slate-400 text-sm">{step}…</span>
            </div>
          ))}
        </div>
      )}

      {data && data.status !== 'analyzing' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left column */}
          <div className="space-y-6">
            <RefundDecision
              decision={data.refund.decision}
              reasoning={data.refund.reasoning}
              expectedLoss={data.refund.expected_loss}
              amount={data.refund.amount}
              transactionId={data.refund.transaction_id}
              fraudProb={data.fraud.probability}
            />
            <LockerFlow
              returnId={returnId}
              locker={data.locker}
              routing={data.routing}
              onDropoffConfirmed={() => poll()}
            />

            {/* Escalation details */}
            {data.escalation && (
              <div className="card border-rose-200 bg-rose-50 space-y-4">
                <h3 className="text-sm font-bold text-rose-700 uppercase tracking-wide">Human Review Required</h3>
                <div className="flex items-center gap-2">
                  <span className="badge-red">{data.escalation.priority} priority</span>
                  <span className="text-xs text-slate-500">{data.escalation.queue_status}</span>
                </div>
                <p className="text-slate-700 text-sm leading-relaxed">{data.escalation.escalation_reason}</p>
                <div className="bg-white rounded-xl p-4 border border-rose-100 space-y-2">
                  <p className="text-xs font-semibold text-slate-500">Risk Summary</p>
                  {Object.entries(data.escalation.risk_summary || {}).slice(0, 5).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-sm">
                      <span className="text-slate-600 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="text-slate-800 font-mono text-xs font-semibold">
                        {typeof v === 'number' ? v.toFixed(2) : String(v)}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                  <p className="text-xs font-semibold text-amber-700 mb-1">AI Recommendation</p>
                  <p className="text-slate-700 text-sm leading-relaxed">{data.escalation.ai_recommendation}</p>
                </div>
              </div>
            )}

            <ConditionReport
              score={data.condition.score}
              grade={data.condition.grade}
              issues={data.condition.issues}
              authenticity={data.condition.authenticity}
            />

            {/* Fraud signals */}
            {data.fraud.probability !== null && (
              <div className="card space-y-4">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Fraud Assessment</h3>
                <div className="flex items-center gap-4">
                  <div className={`text-4xl font-extrabold ${
                    (data.fraud.probability || 0) > 0.4 ? 'text-rose-600' :
                    (data.fraud.probability || 0) > 0.15 ? 'text-amber-600' : 'text-emerald-600'
                  }`}>
                    {((data.fraud.probability || 0) * 100).toFixed(1)}%
                  </div>
                  <div>
                    <p className="text-slate-900 font-semibold">Fraud Probability</p>
                    <p className="text-slate-500 text-sm leading-relaxed">{data.fraud.reasoning}</p>
                  </div>
                </div>
                {data.fraud.signals.length > 0 && (
                  <div className="space-y-1.5">
                    {data.fraud.signals.map((s, i) => (
                      <div key={i} className="flex items-center justify-between text-sm bg-slate-50 rounded-xl px-3 py-2 border border-slate-100">
                        <span className="text-slate-600 capitalize">{s.signal.replace(/_/g, ' ')}</span>
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                          s.weight === 'critical' || s.weight === 'high_risk'
                            ? 'bg-rose-100 text-rose-700'
                            : s.weight === 'medium_risk'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-emerald-100 text-emerald-700'
                        }`}>{s.weight.replace('_', ' ')}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right column — Agent trace */}
          <div className="card">
            <AgentTrace trace={data.agent_trace} />
          </div>
        </div>
      )}

      {/* Partial trace while analyzing */}
      {status === 'analyzing' && data?.agent_trace && data.agent_trace.length > 0 && (
        <div className="card">
          <AgentTrace trace={data.agent_trace} />
        </div>
      )}
    </div>
  )
}
