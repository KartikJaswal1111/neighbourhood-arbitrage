'use client'
import { useState } from 'react'
import { simulateLockerDropoff } from '@/lib/api'

interface LockerInfo {
  locker_unit: string
  dropoff_qr_hash: string
  pickup_qr_hash: string | null
  allocation_status: string
}
interface Props {
  returnId: string
  locker: LockerInfo | null
  routing: { decision: string | null; instructions: Record<string, unknown> }
  onDropoffConfirmed: () => void
}

function QRCode({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="w-24 h-24 bg-white rounded-xl border border-slate-200 p-2 shadow-sm grid grid-cols-5 grid-rows-5 gap-0.5">
        {Array.from({ length: 25 }).map((_, i) => (
          <div
            key={i}
            className={`rounded-sm ${
              [0,1,2,3,4,5,9,10,14,15,19,20,21,22,23,24,6,12,18,7,11,13,17].includes(i)
                ? 'bg-slate-900' : 'bg-white'
            }`}
          />
        ))}
      </div>
      <span className="text-xs text-slate-500 font-medium">{label}</span>
    </div>
  )
}

export default function LockerFlow({ returnId, locker, routing, onDropoffConfirmed }: Props) {
  const [simulating, setSimulating] = useState(false)
  const [confirmed, setConfirmed] = useState(false)
  const [confirmResult, setConfirmResult] = useState<Record<string, unknown> | null>(null)

  if (!locker && routing.decision !== 'community_hub_p2p') {
    if (routing.decision === 'warehouse') {
      return (
        <div className="card border-amber-200 bg-amber-50">
          <h3 className="text-xs font-bold text-amber-700 uppercase tracking-widest mb-3">Routing</h3>
          <div className="flex items-center gap-3">
            <span className="text-3xl">🏭</span>
            <div>
              <p className="font-bold text-slate-900">Warehouse Return</p>
              <p className="text-slate-600 text-sm mt-0.5">
                No nearby buyer found. Standard return label issued. Refund on confirmed delivery.
              </p>
            </div>
          </div>
        </div>
      )
    }
    return null
  }

  const inst = routing.instructions as Record<string, unknown>

  async function handleSimulate() {
    setSimulating(true)
    try {
      const result = await simulateLockerDropoff(returnId)
      setConfirmResult(result)
      if (result.confirmed) {
        setConfirmed(true)
        setTimeout(onDropoffConfirmed, 1500)
      }
    } finally {
      setSimulating(false)
    }
  }

  return (
    <div className="card border-emerald-200 bg-emerald-50 space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold text-emerald-700 uppercase tracking-widest">Smart Locker — P2P</h3>
        <span className="badge-green">AI Approved</span>
      </div>

      {/* Flow steps */}
      <div className="grid grid-cols-3 gap-3 text-center text-xs">
        {[
          { icon: '📱', label: 'QR Code Received', status: 'done' },
          { icon: '🔒', label: 'Drop at Locker',   status: confirmed ? 'done' : 'pending' },
          { icon: '💸', label: 'Refund + Buyer QR', status: confirmed ? 'done' : 'locked' },
        ].map((step, i) => (
          <div key={i} className={`rounded-xl p-3 border font-medium ${
            step.status === 'done'    ? 'border-emerald-300 bg-emerald-100 text-emerald-700' :
            step.status === 'pending' ? 'border-amber-300 bg-amber-50 text-amber-700 animate-pulse-slow' :
                                        'border-slate-200 bg-white text-slate-400'
          }`}>
            <div className="text-2xl mb-1">{step.icon}</div>
            <p>{step.label}</p>
          </div>
        ))}
      </div>

      {/* Locker details */}
      {locker && (
        <div className="bg-white rounded-xl p-4 border border-emerald-100 space-y-3">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-bold text-slate-900">{(inst?.title as string) || 'Drop at Smart Locker'}</p>
              <p className="text-slate-600 text-sm mt-1 font-mono">{locker.locker_unit}</p>
              <p className="text-slate-500 text-xs mt-0.5">
                {(inst?.carrier as string) || 'Smart Locker Network'}
                {inst?.co2_saved_kg ? ` · ${inst.co2_saved_kg}kg CO₂ saved` : ''}
              </p>
            </div>
            <QRCode label="Drop-off QR" />
          </div>
          <p className="text-slate-600 text-sm border-t border-emerald-100 pt-3">
            {(inst?.description as string) || 'Scan QR at the locker, place item inside, close door.'}
          </p>
        </div>
      )}

      {/* Demo simulate button */}
      {!confirmed && (
        <div className="border border-dashed border-emerald-300 rounded-xl p-4 space-y-3 bg-white/60">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Demo — Simulate IoT Locker Event</p>
          <p className="text-xs text-slate-500 leading-relaxed">
            In production this fires automatically when the customer closes the locker door.
            Weight and camera sensors confirm the item.
          </p>
          <button className="btn-success w-full" onClick={handleSimulate} disabled={simulating}>
            {simulating ? (
              <>
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Locker verifying...
              </>
            ) : '🔒 Simulate Customer Drops Item at Locker'}
          </button>
        </div>
      )}

      {/* Confirmation result */}
      {confirmResult && (
        <div className={`rounded-xl p-4 border space-y-3 ${
          confirmResult.confirmed ? 'border-emerald-300 bg-emerald-100' : 'border-rose-300 bg-rose-50'
        }`}>
          <p className="font-bold text-slate-900">
            {confirmResult.confirmed ? '✅ Locker Confirmed — Refund Fired' : '⚠️ Verification Failed'}
          </p>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {[
              { label: 'Weight',    value: confirmResult.weight_verified ? '✓ Match' : '✗ Mismatch' },
              { label: 'Camera',    value: confirmResult.camera_verified ? '✓ SKU confirmed' : '✗ Mismatch' },
              { label: 'Locker AI', value: `${confirmResult.locker_ai_score}/100` },
            ].map(item => (
              <div key={item.label} className="bg-white rounded-lg p-2 text-center border border-emerald-100">
                <p className="text-slate-500">{item.label}</p>
                <p className="text-slate-800 font-semibold mt-0.5">{String(item.value)}</p>
              </div>
            ))}
          </div>
          {confirmResult.confirmed && (
            <div className="flex items-center gap-3 pt-1">
              <QRCode label="Buyer Pickup QR" />
              <p className="text-emerald-700 text-sm font-medium">Buyer notified — 24hr pickup window active</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
