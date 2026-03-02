import type { Metadata } from 'next'
import './globals.css'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Neighbourhood Arbitrage Engine',
  description: 'AI-native reverse logistics — P2P rerouting via Smart Locker network',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-100">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-brand">
                <span className="text-white font-bold text-xs">NA</span>
              </div>
              <div className="leading-tight">
                <p className="font-bold text-slate-900 text-sm">Neighbourhood Arbitrage</p>
                <p className="text-xs text-slate-400">AI Returns Engine</p>
              </div>
            </Link>
            <div className="flex items-center gap-2">
              <span className="hidden sm:inline-flex badge-indigo mr-1">MVP Demo</span>
              <Link href="/" className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 transition-all">
                Demo
              </Link>
              <Link href="/admin" className="btn-primary py-2 px-4 text-xs">
                Review Queue →
              </Link>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">
          {children}
        </main>
      </body>
    </html>
  )
}
