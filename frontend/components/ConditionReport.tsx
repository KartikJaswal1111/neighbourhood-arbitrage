'use client'

interface Issue {
  location: string
  severity: string
  type: string
  description: string
}
interface Props {
  score: number | null
  grade: string | null
  issues: Issue[]
  authenticity: Record<string, string>
}
const SEV_COLOR: Record<string, string> = {
  none:     'bg-emerald-100 text-emerald-700',
  minor:    'bg-amber-100 text-amber-700',
  moderate: 'bg-orange-100 text-orange-700',
  severe:   'bg-rose-100 text-rose-700',
}

function ScoreRing({ score }: { score: number }) {
  const color = score >= 75 ? '#10b981' : score >= 60 ? '#f59e0b' : score >= 45 ? '#f97316' : '#ef4444'
  const r = 36
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  return (
    <div className="relative w-24 h-24 flex items-center justify-center">
      <svg className="absolute inset-0 -rotate-90" width="96" height="96" viewBox="0 0 96 96">
        <circle cx="48" cy="48" r={r} fill="none" stroke="#e2e8f0" strokeWidth="8" />
        <circle
          cx="48" cy="48" r={r} fill="none"
          stroke={color} strokeWidth="8"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div className="text-center">
        <div className="text-2xl font-bold text-slate-800">{score}</div>
        <div className="text-xs text-slate-400">/100</div>
      </div>
    </div>
  )
}

export default function ConditionReport({ score, grade, issues, authenticity }: Props) {
  if (score === null) return null
  const authEntries = Object.entries(authenticity).filter(([k]) => k !== 'overall')

  return (
    <div className="card space-y-5">
      <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">AI Condition Assessment</h3>
      <div className="flex items-center gap-6">
        <ScoreRing score={score} />
        <div className="space-y-1.5">
          <div className="text-3xl font-extrabold text-slate-900">Grade {grade}</div>
          <p className="text-slate-500 text-sm">
            {score >= 80 ? 'Excellent — P2P eligible' :
             score >= 65 ? 'Good — P2P eligible' :
             score >= 45 ? 'Fair — warehouse route' : 'Poor — inspection required'}
          </p>
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${
              authenticity.overall === 'authentic' ? 'bg-emerald-400' :
              authenticity.overall === 'suspicious' ? 'bg-amber-400' : 'bg-rose-400'
            }`} />
            <span className="text-sm font-medium text-slate-600 capitalize">
              {authenticity.overall || 'Not checked'}
            </span>
          </div>
        </div>
      </div>

      {issues.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-slate-500 mb-2">Detected Issues</p>
          <div className="space-y-2">
            {issues.map((issue, i) => (
              <div key={i} className="flex items-start gap-3 text-sm bg-slate-50 rounded-xl p-3 border border-slate-100">
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full shrink-0 capitalize ${SEV_COLOR[issue.severity] || 'bg-slate-100 text-slate-600'}`}>
                  {issue.severity}
                </span>
                <span className="text-slate-700">{issue.description}</span>
                <span className="text-slate-400 text-xs ml-auto shrink-0">{issue.location}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {authEntries.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-slate-500 mb-2">Authenticity Checks</p>
          <div className="flex flex-wrap gap-2">
            {authEntries.map(([key, val]) => (
              <div key={key} className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium border ${
                val === 'pass' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                val === 'fail' ? 'bg-rose-50 text-rose-700 border-rose-200' :
                                 'bg-amber-50 text-amber-700 border-amber-200'
              }`}>
                <span>{val === 'pass' ? '✓' : val === 'fail' ? '✗' : '?'}</span>
                <span className="capitalize">{key.replace('_check', '')}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
