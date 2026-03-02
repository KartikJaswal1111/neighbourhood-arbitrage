'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getScenarios, initiateReturn } from '@/lib/api'
import type { Scenario } from '@/lib/types'

const BADGE: Record<string, string> = {
  green:  'badge-green',
  red:    'badge-red',
  yellow: 'badge-yellow',
}
const CARD_GRADIENTS = [
  'from-indigo-500 to-violet-600',
  'from-rose-500 to-pink-600',
  'from-amber-500 to-orange-500',
]
const CARD_ICONS = ['👟', '📷', '🧥']

export default function HomePage() {
  const router = useRouter()
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getScenarios()
      .then(d => setScenarios(d.scenarios))
      .catch(() => setError('Backend not reachable. Start the FastAPI server on port 8000.'))
  }, [])

  async function launch(s: Scenario) {
    setLoading(s.id)
    setError('')
    try {
      const result = await initiateReturn({
        customer_id:  s.customer_id,
        order_id:     s.order_id,
        reason_text:  s.reason_text,
        media_urls:   s.media_urls,
        returner_lat: s.returner_lat,
        returner_lng: s.returner_lng,
      })
      router.push(`/result/${result.return_id}`)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to initiate return')
      setLoading(null)
    }
  }

  return (
    <div className="space-y-16">

      {/* ── Hero ── */}
      <section className="relative rounded-3xl overflow-hidden px-10 py-16 text-white bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-700">
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-white/[0.04] blur-3xl" />
          <div className="absolute -bottom-32 -left-32 w-96 h-96 rounded-full bg-white/[0.04] blur-3xl" />
        </div>
        <div className="relative z-10 mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 ring-1 ring-white/20 text-xs font-semibold text-white/90 mb-6">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Based on the Real Scenario of Nike shoes I have returned
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight mb-4">
            Neighbourhood<br />Arbitrage Engine
          </h1>
          <p className="text-indigo-100 text-lg leading-relaxed mb-10 max-w-2xl mx-auto">
            AI-native reverse logistics. Returns rerouted P2P through smart neighbourhood
            lockers — cutting cost and CO₂ by up to 80% with instant refunds.
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            {[
              { icon: '💸', value: '80%',    label: 'Cost Saved' },
              { icon: '🌱', value: '4x less', label: 'CO₂ Footprint' },
              { icon: '⚡', value: '<30s',    label: 'Refund Time' },
              { icon: '🤖', value: '>85%',   label: 'AI Automation' },
            ].map(m => (
              <div key={m.label} className="flex items-center gap-3 bg-white/10 backdrop-blur-sm ring-1 ring-white/20 rounded-2xl px-4 py-3">
                <span className="text-2xl">{m.icon}</span>
                <div>
                  <p className="text-xl font-bold leading-none">{m.value}</p>
                  <p className="text-xs text-indigo-200 mt-0.5">{m.label}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── The Problem ── */}
      <section>
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-900">The $B+ Problem</h2>
          <p className="text-slate-500 text-sm mt-1">Traditional returns are— slow and expensive</p>
        </div>
        <div className="card mb-5 bg-rose-50 border-rose-100">
          <p className="text-xs font-semibold text-rose-600 uppercase tracking-wider mb-3">
            That is what happened when I have returned my Nike shoes:
          </p>
          <div className="flex flex-wrap gap-1.5 items-center">
            {[
              'Return Requested', 'Postal Label', 'Walk to Post Office',
              'Carrier Pickup', 'Warehouse (Day 10)', 'Inspection (Day 12)',
              'Restock Decision (Day 14)', '💸 Refund (Day 15)',
            ].map((step, i, arr) => (
              <span key={i} className="flex items-center gap-1.5">
                <span className="bg-white border border-rose-200 text-slate-700 text-xs px-2.5 py-1 rounded-lg shadow-sm font-medium">
                  {step}
                </span>
                {i < arr.length - 1 && <span className="text-rose-300">→</span>}
              </span>
            ))}
          </div>
          <p className="text-rose-600 text-xs mt-3 font-medium">
            15 days · two shipping legs · $15-25 processing cost · zero customer delight
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: '📦', title: '$B+ returned annually', desc: 'Only 20% gets resold. The rest is liquidated or landfilled.', border: 'border-rose-200 bg-rose-50' },
            { icon: '🚛', title: '15-day return cycle',     desc: 'Customer → carrier → warehouse → inspection → refund. Every step adds cost.', border: 'border-amber-200 bg-amber-50' },
            { icon: '🌍', title: 'B+ kg CO₂/year',          desc: 'Return shipping generates enormous carbon from empty truck miles.', border: 'border-orange-200 bg-orange-50' },
          ].map(p => (
            <div key={p.title} className={`card border ${p.border}`}>
              <div className="text-3xl mb-3">{p.icon}</div>
              <h3 className="font-bold text-slate-900 mb-1">{p.title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Live Demo ── */}
      <section>
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-900">Live Demo — 3 AI Scenarios</h2>
          <p className="text-slate-500 text-sm mt-1">Each runs the full agent pipeline end-to-end. Pick one to watch it work.</p>
        </div>
        {error && (
          <div className="mb-5 bg-rose-50 border border-rose-200 text-rose-700 rounded-2xl px-5 py-4 text-sm font-medium">
            {error}
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {scenarios.map((s, i) => (
            <div key={s.id} className="bg-white rounded-2xl shadow-card border border-slate-100 flex flex-col overflow-hidden hover:shadow-card-hover transition-all duration-300">
              <div className={`h-1.5 w-full bg-gradient-to-r ${CARD_GRADIENTS[i] ?? 'from-indigo-500 to-violet-600'}`} />
              <div className="p-6 flex flex-col flex-1">
                <div className="flex items-start justify-between mb-4">
                  <span className="text-4xl">{CARD_ICONS[i]}</span>
                  <span className={BADGE[s.badge_color] ?? 'badge-blue'}>{s.badge}</span>
                </div>
                <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">{s.title}</p>
                <h3 className="text-slate-900 font-bold text-lg leading-snug mb-3">{s.subtitle}</h3>
                <p className="text-slate-500 text-sm leading-relaxed flex-1 mb-4">{s.description}</p>
                <div className="bg-slate-50 rounded-xl px-3 py-2.5 mb-5 text-xs border border-slate-100">
                  <span className="font-semibold text-slate-700">Expected: </span>
                  <span className="text-slate-500">{s.expected_outcome}</span>
                </div>
                <button className="btn-primary w-full" onClick={() => launch(s)} disabled={!!loading}>
                  {loading === s.id ? (
                    <>
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Analyzing...
                    </>
                  ) : 'Run Scenario →'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Architecture ── */}
      <section>
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-900">System Architecture</h2>
          <p className="text-slate-500 text-sm mt-1">Four AI systems working in concert — humans only step in when the AI flags it</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { icon: '👁️', title: 'AI Vision',    desc: 'Claude Vision inspects condition, detects damage, checks authenticity from photos',  gradient: 'from-sky-400 to-blue-500',      bg: 'bg-sky-50' },
            { icon: '🛡️', title: 'Fraud Engine', desc: 'Behavioral signals + LLM reasoning assess fraud probability per return',               gradient: 'from-rose-400 to-pink-500',     bg: 'bg-rose-50' },
            { icon: '📍', title: 'Geo Matcher',  desc: 'Haversine geo search finds P2P buyers within configurable radius',                     gradient: 'from-emerald-400 to-teal-500',  bg: 'bg-emerald-50' },
            { icon: '🔒', title: 'Smart Locker', desc: 'IoT lockers verify drop-off via weight + camera + AI score before firing refund',       gradient: 'from-violet-400 to-purple-500', bg: 'bg-violet-50' },
          ].map(a => (
            <div key={a.title} className={`card text-center ${a.bg} border-slate-100 hover:shadow-card-hover transition-all duration-300`}>
              <div className={`w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br ${a.gradient} flex items-center justify-center text-2xl mb-4 shadow-md`}>
                {a.icon}
              </div>
              <h3 className="font-bold text-slate-900 mb-2">{a.title}</h3>
              <p className="text-xs text-slate-500 leading-relaxed">{a.desc}</p>
            </div>
          ))}
        </div>
      </section>

    </div>
  )
}
