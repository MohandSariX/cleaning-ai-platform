'use client'
import { useEffect, useState } from 'react'
import { Mail, Send, RefreshCw, Loader2, Clock, CheckCircle, AlertCircle, Zap } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type OutreachStats = {
  envoyes_aujourd_hui: number
  quota_journalier: number
  total_envoyes: number
  total_relances: number
  en_attente: number
  prochaine_envoi: string
}

export function OutreachPanel() {
  const [stats, setStats] = useState<OutreachStats | null>(null)
  const [sending, setSending] = useState(false)
  const [relancing, setRelancing] = useState(false)
  const [open, setOpen] = useState(false)
  const [lastAction, setLastAction] = useState<string | null>(null)

  const fetchStats = async () => {
    const res = await fetch(`${API}/api/outreach/stats`)
    setStats(await res.json())
  }

  useEffect(() => { fetchStats() }, [])

  const sendTest = async () => {
    setSending(true)
    const res = await fetch(`${API}/api/outreach/send-test`, { method: 'POST' })
    const data = await res.json()
    setLastAction(data.status === 'sent' ? `✅ Email envoyé à ${data.prospect}` : data.message)
    await fetchStats()
    setSending(false)
  }

  const runRelances = async () => {
    setRelancing(true)
    await fetch(`${API}/api/outreach/run-relances`, { method: 'POST' })
    setLastAction('✅ Relances lancées')
    await fetchStats()
    setRelancing(false)
  }

  if (!stats) return null

  const pct = Math.round((stats.envoyes_aujourd_hui / stats.quota_journalier) * 100)
  const actif = stats.prochaine_envoi !== 'Hors fenêtre (9h-18h)'

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      {/* Header cliquable */}
      <div
        onClick={() => setOpen(o => !o)}
        style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: actif ? '#3b82f618' : 'var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Mail size={14} color={actif ? '#3b82f6' : 'var(--text-muted)'} />
          </div>
          <div>
            <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: 13 }}>
              Prospection automatique
              <span style={{ marginLeft: 8, fontSize: 11, padding: '2px 7px', borderRadius: 10, background: actif ? '#3b82f618' : 'var(--border)', color: actif ? '#3b82f6' : 'var(--text-muted)', fontWeight: 600 }}>
                {actif ? '● Actif' : '○ Hors fenêtre'}
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>
              {stats.envoyes_aujourd_hui}/{stats.quota_journalier} emails aujourd'hui · {stats.en_attente} en attente
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* Mini progress bar */}
          <div style={{ width: 80, height: 4, borderRadius: 2, background: 'var(--border)', overflow: 'hidden' }}>
            <div style={{ width: `${pct}%`, height: '100%', background: '#3b82f6', borderRadius: 2, transition: 'width 0.5s' }} />
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', transform: open ? 'rotate(180deg)' : 'none', transition: '0.2s' }}>▾</span>
        </div>
      </div>

      {/* Contenu expandable */}
      {open && (
        <div style={{ padding: '0 20px 20px', borderTop: '1px solid var(--border)' }}>
          {/* KPIs */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, paddingTop: 16, marginBottom: 16 }}>
            {[
              { label: "Aujourd'hui", value: `${stats.envoyes_aujourd_hui}/${stats.quota_journalier}`, color: '#3b82f6', icon: Send },
              { label: 'Total envoyés', value: stats.total_envoyes, color: '#22c55e', icon: CheckCircle },
              { label: 'Relances', value: stats.total_relances, color: '#f97316', icon: RefreshCw },
              { label: 'En attente', value: stats.en_attente, color: '#a855f7', icon: Clock },
            ].map(({ label, value, color, icon: Icon }) => (
              <div key={label} style={{ padding: '12px 14px', borderRadius: 8, background: `${color}08`, border: `1px solid ${color}20` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <Icon size={12} color={color} />
                  <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
                </div>
                <div style={{ fontFamily: 'Syne', fontSize: 22, fontWeight: 700, color }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Barre de quota */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
              <span>Quota journalier</span>
              <span>{pct}%</span>
            </div>
            <div style={{ height: 6, borderRadius: 3, background: 'var(--border)', overflow: 'hidden' }}>
              <div style={{ width: `${pct}%`, height: '100%', background: pct > 80 ? '#f97316' : '#3b82f6', borderRadius: 3, transition: 'width 0.5s' }} />
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Prochain envoi : {stats.prochaine_envoi}</div>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={sendTest} disabled={sending} style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px',
              borderRadius: 7, border: 'none', background: '#3b82f6', color: 'white',
              fontSize: 12, fontWeight: 600, cursor: 'pointer', opacity: sending ? 0.7 : 1
            }}>
              {sending ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
              Envoyer maintenant (test)
            </button>
            <button onClick={runRelances} disabled={relancing} style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px',
              borderRadius: 7, border: '1px solid var(--border)', background: 'transparent',
              color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer'
            }}>
              {relancing ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
              Lancer relances J+3
            </button>
            <button onClick={fetchStats} style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '7px 10px',
              borderRadius: 7, border: '1px solid var(--border)', background: 'transparent',
              color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer'
            }}>
              <RefreshCw size={12} />
            </button>
          </div>

          {lastAction && (
            <div style={{ marginTop: 10, fontSize: 12, color: '#22c55e', padding: '6px 10px', background: '#22c55e10', borderRadius: 6 }}>
              {lastAction}
            </div>
          )}
        </div>
      )}
    </div>
  )
}