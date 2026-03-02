'use client'
import type { TraceStep } from '@/lib/types'

const TOOL_META: Record<string, { label: string; icon: string; color: string }> = {
  analyze_item_condition:       { label: 'Vision — Item Condition',         icon: '🔍', color: 'sky' },
  get_customer_trust_score:     { label: 'Trust Profile Retrieved',         icon: '👤', color: 'violet' },
  calculate_fraud_risk:         { label: 'Fraud Risk Calculated',           icon: '⚠️', color: 'orange' },
  search_nearby_buyers:         { label: 'Nearby Buyers Searched',          icon: '📍', color: 'teal' },
  find_nearest_hub:             { label: 'Smart Locker Hub Located',        icon: '🔒', color: 'cyan' },
  calculate_refund_risk:        { label: 'Refund Risk Assessed',            icon: '💰', color: 'amber' },
  allocate_locker:              { label: 'Locker Allocated — QR Generated', icon: '📦', color: 'emerald' },
  issue_instant_refund:         { label: 'INSTANT REFUND ISSUED',           icon: '✅', color: 'emerald' },
  generate_routing_instruction: { label: 'Routing Instruction Generated',   icon: '🗺️', color: 'indigo' },
  escalate_to_human:            { label: 'ESCALATED TO HUMAN',              icon: '🚨', color: 'rose' },
}

const CHIP: Record<string, string> = {
  sky:     'bg-sky-50 text-sky-700 border-sky-200',
  violet:  'bg-violet-50 text-violet-700 border-violet-200',
  orange:  'bg-orange-50 text-orange-700 border-orange-200',
  teal:    'bg-teal-50 text-teal-700 border-teal-200',
  cyan:    'bg-cyan-50 text-cyan-700 border-cyan-200',
  amber:   'bg-amber-50 text-amber-700 border-amber-200',
  emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  indigo:  'bg-indigo-50 text-indigo-700 border-indigo-200',
  rose:    'bg-rose-50 text-rose-700 border-rose-200',
}

const DOT: Record<string, string> = {
  sky:     'bg-sky-400',
  violet:  'bg-violet-400',
  orange:  'bg-orange-400',
  teal:    'bg-teal-400',
  cyan:    'bg-cyan-400',
  amber:   'bg-amber-400',
  emerald: 'bg-emerald-400',
  indigo:  'bg-indigo-400',
  rose:    'bg-rose-500',
}

function KeyValue({ k, v }: { k: string; v: unknown }) {
  if (v === null || v === undefined) return null
  if (typeof v === 'object' && !Array.isArray(v)) {
    return (
      <div className="ml-2">
        <span className="text-slate-400 text-xs">{k}:</span>
        {Object.entries(v as Record<string, unknown>).slice(0, 4).map(([k2, v2]) => (
          <KeyValue key={k2} k={k2} v={v2} />
        ))}
      </div>
    )
  }
  if (Array.isArray(v)) {
    return (
      <div className="ml-2">
        <span className="text-slate-400 text-xs">{k}: </span>
        <span className="text-slate-500 text-xs">[{v.length} items]</span>
      </div>
    )
  }
  const display = String(v)
  return (
    <div className="flex gap-2 ml-2">
      <span className="text-slate-400 text-xs shrink-0">{k}:</span>
      <span className="text-slate-600 text-xs truncate max-w-[200px] font-medium" title={display}>
        {typeof v === 'number' ? (Number.isInteger(v) ? v : v.toFixed(3)) : display}
      </span>
    </div>
  )
}

export default function AgentTrace({ trace }: { trace: TraceStep[] }) {
  if (!trace || trace.length === 0) return null

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
          Agent Decision Trail
        </h3>
        <span className="badge-indigo">{trace.length} tool calls</span>
      </div>

      <div className="relative">
        {/* Vertical timeline line */}
        <div className="absolute left-3.5 top-4 bottom-4 w-px bg-slate-200" />
        <div className="space-y-3">
          {trace.map((step, i) => {
            const meta = TOOL_META[step.tool] || { label: step.tool, icon: '⚙️', color: 'indigo' }
            const chipClass = CHIP[meta.color] || CHIP.indigo
            const dotClass  = DOT[meta.color]  || DOT.indigo

            return (
              <div key={i} className="relative pl-9 animate-slide-in">
                {/* Timeline dot */}
                <div className={`absolute left-2 top-3.5 w-3 h-3 rounded-full border-2 border-white shadow-sm ${dotClass}`} />

                <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-3.5">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-base leading-none">{meta.icon}</span>
                      <span className="text-sm font-semibold text-slate-800">{meta.label}</span>
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-mono border ${chipClass}`}>
                        {step.tool}()
                      </span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {step.status === 'error'
                        ? <span className="badge-red">error</span>
                        : <span className="badge-green">✓</span>
                      }
                      <span className="text-xs text-slate-400">{step.duration_ms}ms</span>
                    </div>
                  </div>
                  {/* Output values */}
                  <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 bg-slate-50 rounded-lg p-2">
                    {Object.entries(step.output)
                      .filter(([k]) => !['signals', 'issues', 'all_candidates', 'recovery_options', 'all_hubs'].includes(k))
                      .slice(0, 8)
                      .map(([k, v]) => <KeyValue key={k} k={k} v={v} />)}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
