'use client'
import { useEffect, useState } from 'react'
import {
  TrendingUp, TrendingDown, Zap, RefreshCw, Loader2,
  Target, Award, AlertCircle, CheckCircle, Brain
} from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Suggestion = {
  type: string
  priority: string
  message: string
  action: string
  params?: any
}

type EmailPerformance = {
  total_sent: number
  replied: number
  reply_rate: number
  best_day: string
  recommendations: any[]
}

type LostAnalysis = {
  total: number
  avg_score: number
  by_score_range: { high: number; medium: number; low: number }
  top_lost_industries: Array<{ industry: string; count: number }>
  recommendations: any[]
}

type Strategy = {
  priority_industry: string | null
  priority_city: string | null
  ab_test_active: string | null
  top_converting_industry: string | null
  top_converting_city: string | null
}

export default function OptimizationsPage() {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [emailPerf, setEmailPerf] = useState<EmailPerformance | null>(null)
  const [lostAnalysis, setLostAnalysis] = useState<LostAnalysis | null>(null)
  const [strategy, setStrategy] = useState<Strategy | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [sugRes, emailRes, lostRes, stratRes] = await Promise.all([
        fetch(`${API}/api/optimizations/suggestions`),
        fetch(`${API}/api/optimizations/email-performance`),
        fetch(`${API}/api/optimizations/lost-prospects`),
        fetch(`${API}/api/optimizations/strategy`),
      ])
      setSuggestions(await sugRes.json())
      setEmailPerf(await emailRes.json())
      setLostAnalysis(await lostRes.json())
      setStrategy(await stratRes.json())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const runCycle = async () => {
    setRunning(true)
    try {
      await fetch(`${API}/api/optimizations/run-cycle`, { method: 'POST' })
      await load()
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '32px 36px', display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)' }}>
        <Loader2 size={18} className="animate-spin" /> Chargement...
      </div>
    )
  }

  const PRIORITY_COLORS = {
    high: '#ef4444',
    medium: '#f97316',
    low: '#64748b',
  }

  return (
    <div style={{ padding: '32px 36px', maxWidth: 1400 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Optimisations IA</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 6, fontSize: 13 }}>
            Claude apprend et s'améliore automatiquement
          </p>
        </div>
        <button
          onClick={runCycle}
          disabled={running}
          style={{
            display: 'flex', alignItems: 'center', gap: 6, padding: '9px 18px',
            borderRadius: 8, border: 'none', background: '#f5a623', color: 'white',
            fontSize: 13, fontWeight: 600, cursor: 'pointer', opacity: running ? 0.7 : 1,
          }}
        >
          {running ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          Lancer cycle d'optimisation
        </button>
      </div>

      {/* Stratégie actuelle */}
      {strategy && (
        <div className="card" style={{ padding: '24px', marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Target size={18} color="#f5a623" />
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Stratégie actuelle</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
            {strategy.top_converting_industry && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Top industrie convertie
                </div>
                <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)' }}>
                  {strategy.top_converting_industry}
                </div>
              </div>
            )}
            {strategy.top_converting_city && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Top ville convertie
                </div>
                <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)' }}>
                  {strategy.top_converting_city}
                </div>
              </div>
            )}
            {strategy.ab_test_active && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  A/B test en cours
                </div>
                <div style={{ fontSize: 16, fontWeight: 600, color: '#3b82f6' }}>
                  {strategy.ab_test_active}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Email Performance */}
        {emailPerf && (
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <TrendingUp size={18} color="#3b82f6" />
              <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Performance emails</h2>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Envoyés (7j)</div>
                <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'DM Sans', color: 'var(--text)' }}>
                  {emailPerf.total_sent}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Réponses</div>
                <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'DM Sans', color: 'var(--text)' }}>
                  {emailPerf.replied}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Taux réponse</div>
                <div style={{
                  fontSize: 24, fontWeight: 700, fontFamily: 'DM Sans',
                  color: emailPerf.reply_rate >= 3 ? '#22c55e' : emailPerf.reply_rate >= 2 ? '#f97316' : '#ef4444',
                }}>
                  {emailPerf.reply_rate.toFixed(1)}%
                </div>
              </div>
            </div>
            {emailPerf.best_day !== 'N/A' && (
              <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '10px 12px', background: 'var(--surface)', borderRadius: 6 }}>
                Meilleur jour : <strong style={{ color: 'var(--text)' }}>{emailPerf.best_day}</strong>
              </div>
            )}
          </div>
        )}

        {/* Lost Prospects */}
        {lostAnalysis && (
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <TrendingDown size={18} color="#ef4444" />
              <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Prospects perdus (30j)</h2>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16, marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Total perdus</div>
                <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'DM Sans', color: '#ef4444' }}>
                  {lostAnalysis.total}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Score moyen</div>
                <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'DM Sans', color: 'var(--text)' }}>
                  {lostAnalysis.avg_score.toFixed(0)}
                </div>
              </div>
            </div>
            {lostAnalysis.top_lost_industries.length > 0 && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, fontWeight: 600 }}>
                  Industries problématiques :
                </div>
                {lostAnalysis.top_lost_industries.slice(0, 3).map((item, i) => (
                  <div key={i} style={{ fontSize: 12, color: 'var(--text)', marginBottom: 4 }}>
                    • {item.industry} : {item.count} perdus
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Suggestions */}
      <div className="card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
          <Brain size={18} color="#f5a623" />
          <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Suggestions d'optimisation</h2>
          <span style={{
            padding: '2px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600,
            background: '#f5a62318', color: '#f5a623',
          }}>
            {suggestions.length} actives
          </span>
        </div>

        {suggestions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 0' }}>
            <CheckCircle size={48} color="#22c55e" style={{ marginBottom: 12 }} />
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>
              Aucune optimisation nécessaire
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              Tout fonctionne bien !
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {suggestions.map((sug, i) => {
              const priorityColor = PRIORITY_COLORS[sug.priority as keyof typeof PRIORITY_COLORS] || '#64748b'
              return (
                <div
                  key={i}
                  style={{
                    padding: '16px 20px', borderRadius: 8,
                    background: 'var(--surface)', border: `1px solid ${priorityColor}40`,
                    display: 'flex', alignItems: 'flex-start', gap: 12,
                  }}
                >
                  <div style={{
                    width: 6, height: 6, borderRadius: '50%', background: priorityColor,
                    marginTop: 6, flexShrink: 0,
                  }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{
                        fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
                        color: priorityColor, letterSpacing: '0.05em',
                      }}>
                        {sug.priority}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {sug.type}
                      </span>
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text)' }}>
                      {sug.message}
                    </div>
                  </div>
                  {sug.priority === 'high' && (
                    <AlertCircle size={18} color={priorityColor} style={{ flexShrink: 0 }} />
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
