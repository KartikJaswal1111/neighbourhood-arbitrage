'use client'

interface Props {
  decision: string | null
  reasoning: string | null
  expectedLoss: number | null
  amount: number | null
  transactionId: string | null
  fraudProb: number | null
  routingDecision: string | null
}

export default function RefundDecision({
  decision, reasoning, expectedLoss, amount, transactionId, fraudProb, routingDecision
}: Props) {
  if (!decision) return null
  const isApproved   = decision === 'auto_approved'
  const isEscalated  = decision === 'escalate'
  const isWarehouse  = routingDecision === 'warehouse' || routingDecision === 'no_match_routed'
  const isInstant    = isApproved && !isWarehouse

  return (
    <div className={`rounded-2xl border-2 p-6 space-y-5 ${
      isInstant   ? 'border-emerald-200 bg-emerald-50' :
      isEscalated ? 'border-rose-200 bg-rose-50' :
      isWarehouse ? 'border-amber-200 bg-amber-50' :
                    'border-amber-200 bg-amber-50'
    }`}>
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shadow-sm ${
          isInstant ? 'bg-emerald-100' : isEscalated ? 'bg-rose-100' : 'bg-amber-100'
        }`}>
          {isInstant ? '✅' : isEscalated ? '🚨' : isWarehouse ? '🏭' : '⏸️'}
        </div>
        <div>
          <h3 className={`text-xl font-extrabold ${
            isInstant ? 'text-emerald-700' : isEscalated ? 'text-rose-700' : 'text-amber-700'
          }`}>
            {isInstant   ? 'INSTANT REFUND APPROVED' :
             isEscalated ? 'ESCALATED TO HUMAN REVIEW' :
             isWarehouse ? 'REFUND ON DELIVERY' :
                           'MANUAL PROCESSING'}
          </h3>
          {isInstant && amount && (
            <p className="text-emerald-600 font-semibold text-sm">${amount.toFixed(2)} CAD credited instantly</p>
          )}
          {isWarehouse && (
            <p className="text-amber-600 font-semibold text-sm">Issued after warehouse confirms receipt</p>
          )}
        </div>
      </div>

      {/* Decision calculation */}
      <div className="bg-white/80 rounded-xl p-4 border border-white font-mono text-sm space-y-2">
        <p className="text-xs font-sans font-semibold text-slate-500 mb-3">Decision Calculation</p>
        {fraudProb !== null && (
          <div className="flex justify-between">
            <span className="text-slate-500">Fraud probability</span>
            <span className={`font-semibold ${fraudProb > 0.3 ? 'text-rose-600' : 'text-emerald-600'}`}>
              {(fraudProb * 100).toFixed(1)}%
            </span>
          </div>
        )}
        {expectedLoss !== null && (
          <div className="flex justify-between">
            <span className="text-slate-500">Expected loss</span>
            <span className={`font-semibold ${expectedLoss > 15 ? 'text-rose-600' : 'text-emerald-600'}`}>
              ${expectedLoss.toFixed(2)}
            </span>
          </div>
        )}
        <div className="flex justify-between text-slate-400">
          <span>Auto-approve threshold</span>
          <span>$15.00</span>
        </div>
        <div className={`border-t pt-2 flex justify-between font-bold ${
          isInstant ? 'border-emerald-200' : isWarehouse ? 'border-amber-200' : 'border-rose-200'
        }`}>
          <span className="text-slate-600 font-sans text-xs">Decision</span>
          <span className={isInstant ? 'text-emerald-600' : isWarehouse ? 'text-amber-600' : 'text-rose-600'}>
            {isInstant ? '✓ AUTO APPROVED' : isWarehouse ? '🏭 REFUND ON DELIVERY' : '✗ ESCALATE'}
          </span>
        </div>
      </div>

      {reasoning && (
        <p className="text-slate-600 text-sm leading-relaxed">{reasoning}</p>
      )}

      {transactionId && (
        <div className="flex items-center gap-2 text-xs text-emerald-700 bg-emerald-100 rounded-lg px-3 py-2">
          <span className="font-semibold">Transaction:</span>
          <code className="font-mono">{transactionId}</code>
        </div>
      )}
    </div>
  )
}
