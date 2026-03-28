'use client'
import { useEffect, useState } from 'react'
import { Mail, CheckCircle, AlertTriangle, XCircle, RefreshCw, Loader2 } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type TokenHealth = {
  status: 'valid' | 'expired_refreshable' | 'invalid' | 'missing' | 'error'
  expires_in_hours?: number
  message?: string
}

export function GmailStatusPanel() {
  const [health, setHealth] = useState<TokenHealth | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchHealth = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/watchdog/token-health`)
      setHealth(await res.json())
    } catch {}
    setLoading(false)
  }

  useEffect(() => { fetchHealth() }, [])

  if (!health) return null

  const config = {
    valid: { color: '#22c55e', icon: CheckCircle, label: 'Connecté', bg: '#22c55e10' },
    expired_refreshable: { color: '#f97316', icon: AlertTriangle, label: 'Refresh en cours', bg: '#f9741610' },
    invalid: { color: '#ef4444', icon: XCircle, label: 'Token invalide', bg: '#ef444410' },
    missing: { color: '#ef4444', icon: XCircle, label: 'Token manquant', bg: '#ef444410' },
    error: { color: '#ef4444', icon: XCircle, label: 'Erreur', bg: '#ef444410' },
  }[health.status] || { color: '#64748b', icon: Mail, label: 'Inconnu', bg: 'var(--border)' }

  const Icon = config.icon

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '8px 14px', borderRadius: 8,
      background: config.bg, border: `1px solid ${config.color}30`,
      marginBottom: 16
    }}>
      <Icon size={13} color={config.color} />
      <div style={{ flex: 1 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: config.color }}>Gmail {config.label}</span>
        {health.expires_in_hours !== undefined && health.expires_in_hours !== null && (
          <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 8 }}>
            expire dans {health.expires_in_hours}h
          </span>
        )}
        {health.message && (
          <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 8 }}>{health.message}</span>
        )}
      </div>
      <button onClick={fetchHealth} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
        {loading ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
      </button>
      {health.status !== 'valid' && (
        <a href="http://localhost:8000/docs" target="_blank" style={{ fontSize: 11, color: config.color, textDecoration: 'underline' }}>
          Réparer
        </a>
      )}
    </div>
  )
}