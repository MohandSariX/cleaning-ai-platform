// ── Panneau Scheduler ─────────────────────────────────────────────────────────
// À intégrer dans le dashboard (page.tsx) — remplace ou complète ScrapePanel

'use client'
import { useEffect, useRef, useState } from 'react'
import { Clock, Play, ChevronDown, Loader2, Calendar, Zap, X } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const DAY_NAMES = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
const DEPT_COLORS: Record<string, string> = {
  '94': '#3b82f6', '93': '#8b5cf6', '92': '#06b6d4',
  '77': '#22c55e', '75': '#f97316', '91': '#eab308', '78': '#ec4899',
}
const DEPT_NAMES: Record<string, string> = {
  '94': 'Val-de-Marne', '93': 'Seine-Saint-Denis', '92': 'Hauts-de-Seine',
  '77': 'Seine-et-Marne', '75': 'Paris', '91': 'Essonne', '78': 'Yvelines',
}

type SchedulerStatus = {
  running: boolean
  current_dept: string | null
  current_query: string | null
  current_city: string | null
  log: string[]
  last_run: string | null
  next_run: string | null
  scheduler_running: boolean
  stats: { total_scraped_session: number; queries_done: number; queries_total: number }
  planning: Record<string, { dept: string; cities_count: number; queries_count: number }>
}

export function SchedulerPanel() {
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState<SchedulerStatus | null>(null)
  const [showLog, setShowLog] = useState(false)
  const logRef = useRef<HTMLDivElement>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API}/api/scheduler/status`)
      const data = await res.json()
      setStatus(data)
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
    } catch {}
  }

  useEffect(() => {
    fetchStatus()
    pollRef.current = setInterval(fetchStatus, 3000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  const runNow = async () => {
    await fetch(`${API}/api/scheduler/run-now`, { method: 'POST' })
    fetchStatus()
  }

  const clearLog = async () => {
    await fetch(`${API}/api/scheduler/clear-log`, { method: 'POST' })
    fetchStatus()
  }

  const todayDept = status?.planning?.[String(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1)]?.dept
  const progress = status?.stats.queries_total
    ? Math.round((status.stats.queries_done / status.stats.queries_total) * 100)
    : 0

  return (
    <div className="card" style={{ marginBottom: 16, overflow: 'hidden' }}>
      {/* Header */}
      <button onClick={() => setOpen(o => !o)} style={{
        width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '18px 24px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: '#22c55e18', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Zap size={15} color="#22c55e" />
          </div>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: 14 }}>Agent de prospection automatique</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 1 }}>
              {status?.running
                ? `⚡ En cours — ${status.current_dept ? `Dept ${status.current_dept}` : ''} ${status.current_city ? `/ ${status.current_city}` : ''}`
                : status?.next_run
                  ? `Prochain lancement : ${new Date(status.next_run).toLocaleString('fr-FR', { weekday: 'long', hour: '2-digit', minute: '2-digit' })}`
                  : 'Scraping automatique chaque soir à 23h00'
              }
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {status?.running && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Loader2 size={13} className="animate-spin" color="#22c55e" />
              <span style={{ fontSize: 12, color: '#22c55e', fontWeight: 600 }}>{progress}%</span>
            </div>
          )}
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: status?.scheduler_running ? '#22c55e' : '#64748b',
            boxShadow: status?.scheduler_running ? '0 0 6px #22c55e' : 'none',
          }} />
          <ChevronDown size={16} color="var(--text-muted)" style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
        </div>
      </button>

      {open && (
        <div style={{ padding: '0 24px 24px', borderTop: '1px solid var(--border)' }}>

          {/* Barre de progression si running */}
          {status?.running && (
            <div style={{ marginTop: 16, marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>
                <span>{status.current_query && `📂 ${status.current_query}`}</span>
                <span>{status.stats.queries_done} / {status.stats.queries_total} combinaisons</span>
              </div>
              <div style={{ height: 6, borderRadius: 3, background: 'var(--border)', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${progress}%`, background: '#22c55e', borderRadius: 3, transition: 'width 0.5s' }} />
              </div>
            </div>
          )}

          {/* Planning semaine */}
          <div style={{ marginTop: 20 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Calendar size={12} /> Planning hebdomadaire — 23h00 chaque soir
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 8 }}>
              {status && Object.entries(status.planning).map(([dayIdx, info]) => {
                const dayNum = parseInt(dayIdx)
                const isToday = (new Date().getDay() === 0 ? 6 : new Date().getDay() - 1) === dayNum
                const isActive = status.running && status.current_dept === info.dept
                const color = DEPT_COLORS[info.dept] || '#64748b'
                return (
                  <div key={dayIdx} style={{
                    padding: '10px 8px', borderRadius: 8, textAlign: 'center',
                    border: `1px solid ${isToday ? color : 'var(--border)'}`,
                    background: isActive ? `${color}18` : isToday ? `${color}0a` : 'var(--surface)',
                    position: 'relative',
                  }}>
                    {isActive && (
                      <div style={{ position: 'absolute', top: 4, right: 4, width: 6, height: 6, borderRadius: '50%', background: color, boxShadow: `0 0 6px ${color}` }} />
                    )}
                    <div style={{ fontSize: 11, fontWeight: 700, color: isToday ? color : 'var(--text-muted)', marginBottom: 4 }}>
                      {DAY_NAMES[dayNum].slice(0, 3).toUpperCase()}
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 800, fontFamily: 'Syne', color }}>
                      {info.dept}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>
                      {DEPT_NAMES[info.dept]}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 4 }}>
                      {info.cities_count} villes
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Détail du jour courant */}
          {todayDept && (
            <div style={{ marginTop: 16, padding: '12px 16px', borderRadius: 8, background: `${DEPT_COLORS[todayDept]}0d`, border: `1px solid ${DEPT_COLORS[todayDept]}30` }}>
              <div style={{ fontSize: 12, color: DEPT_COLORS[todayDept], fontWeight: 600, marginBottom: 4 }}>
                Ce soir à 23h — Département {todayDept} ({DEPT_NAMES[todayDept]})
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {status?.planning[String(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1)]?.cities_count} villes ×{' '}
                {status?.planning[String(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1)]?.queries_count} types d'entreprises
              </div>
            </div>
          )}

          {/* Actions */}
          <div style={{ marginTop: 20, display: 'flex', gap: 10, alignItems: 'center' }}>
            <button onClick={runNow} disabled={status?.running} style={{
              display: 'flex', alignItems: 'center', gap: 7, padding: '9px 18px',
              borderRadius: 8, border: 'none',
              background: status?.running ? 'var(--border)' : '#22c55e',
              color: 'white', fontSize: 12, fontWeight: 600,
              cursor: status?.running ? 'not-allowed' : 'pointer',
            }}>
              {status?.running ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} fill="white" />}
              {status?.running ? 'En cours...' : 'Lancer maintenant'}
            </button>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {status?.last_run && `Dernière exécution : ${new Date(status.last_run).toLocaleString('fr-FR')}`}
            </div>
          </div>

          {/* Logs */}
          {status && status.log.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <button onClick={() => setShowLog(v => !v)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Clock size={12} /> {showLog ? 'Masquer' : 'Voir'} les logs ({status.log.length} lignes)
                </button>
                <button onClick={clearLog} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 11, color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: 3 }}>
                  <X size={11} /> Effacer
                </button>
              </div>
              {showLog && (
                <div ref={logRef} style={{
                  background: '#0a0f1a', borderRadius: 8, padding: '12px 16px',
                  fontFamily: 'monospace', fontSize: 11, color: '#94a3b8',
                  maxHeight: 200, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2,
                }}>
                  {status.log.map((line, i) => (
                    <div key={i} style={{
                      color: line.includes('✅') || line.includes('🎉') ? '#22c55e'
                        : line.includes('❌') ? '#ef4444'
                        : line.includes('⚙️') || line.includes('⚡') ? '#f97316'
                        : line.includes('🚀') ? '#3b82f6'
                        : '#94a3b8'
                    }}>
                      {line}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}