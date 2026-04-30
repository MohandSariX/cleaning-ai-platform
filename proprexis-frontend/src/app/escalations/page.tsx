'use client'
import { useEffect, useState } from 'react'
import {
  AlertTriangle, CheckCircle, XCircle, Loader2, RefreshCw,
  TrendingUp, Clock, Filter, ChevronRight
} from 'lucide-react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Escalation = {
  id: number
  decision_type: string
  priority: string
  title: string
  description: string | null
  context_data: string | null
  status: string
  prospect_id: number | null
  prospect_name: string | null
  devis_id: number | null
  chantier_id: number | null
  amount_ht: number | null
  amount_ttc: number | null
  ia_recommendation: string | null
  ia_confidence: number | null
  ia_reasoning: string | null
  approved_by: string | null
  decision_note: string | null
  decided_at: string | null
  auto_resolve_at: string | null
  default_action: string | null
  created_at: string
}

type Stats = {
  total: number
  pending: number
  approved: number
  rejected: number
  auto_resolved: number
  by_type: Record<string, number>
  by_priority: Record<string, number>
}

const PRIORITY_CONFIG: Record<string, { label: string; color: string }> = {
  low:      { label: 'Faible',   color: '#64748b' },
  medium:   { label: 'Moyen',    color: '#f97316' },
  high:     { label: 'Haute',    color: '#ef4444' },
  critical: { label: 'Critique', color: '#dc2626' },
}

const TYPE_LABELS: Record<string, string> = {
  devis_high_value:    'Devis montant élevé',
  discount_request:    'Demande remise',
  planning_conflict:   'Conflit planning',
  chantier_urgent:     'Chantier urgent',
}

function EscalationCard({ escalation, onDecide }: { escalation: Escalation; onDecide: (id: number, decision: string) => void }) {
  const [deciding, setDeciding] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
  const [note, setNote] = useState('')

  const priority = PRIORITY_CONFIG[escalation.priority] || PRIORITY_CONFIG.medium
  const typeLabel = TYPE_LABELS[escalation.decision_type] || escalation.decision_type

  const handleDecide = async (decision: string) => {
    setDeciding(true)
    try {
      await fetch(`${API}/api/escalations/${escalation.id}/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, approved_by: 'Mohand', note }),
      })
      onDecide(escalation.id, decision)
    } catch (e) {
      alert('Erreur lors de la décision')
    }
    setDeciding(false)
  }

  const contextData = escalation.context_data ? JSON.parse(escalation.context_data) : {}

  return (
    <div className="card" style={{ padding: '20px 24px', marginBottom: 16 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span style={{
              padding: '3px 10px', borderRadius: 12, fontSize: 10, fontWeight: 600,
              background: `${priority.color}18`, color: priority.color, textTransform: 'uppercase',
              border: `1px solid ${priority.color}40`,
            }}>
              {priority.label}
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              {typeLabel}
            </span>
          </div>
          <h3 style={{ fontSize: 16, fontWeight: 600, margin: 0, color: 'var(--text)' }}>
            {escalation.title}
          </h3>
          {escalation.description && (
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 6, marginBottom: 0 }}>
              {escalation.description}
            </p>
          )}
        </div>
        {escalation.amount_ttc && (
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'DM Sans', color: 'var(--text)', letterSpacing: '-0.5px' }}>
              {escalation.amount_ttc.toLocaleString('fr-FR')} €
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>TTC</div>
          </div>
        )}
      </div>

      {/* IA Recommendation */}
      {escalation.ia_recommendation && (
        <div style={{
          padding: '12px 16px', borderRadius: 8,
          background: escalation.ia_recommendation === 'approve' ? '#22c55e08' : '#ef444408',
          border: `1px solid ${escalation.ia_recommendation === 'approve' ? '#22c55e30' : '#ef444430'}`,
          marginBottom: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <TrendingUp size={14} color={escalation.ia_recommendation === 'approve' ? '#22c55e' : '#ef4444'} />
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>
              Recommandation IA : {escalation.ia_recommendation === 'approve' ? 'Approuver' : 'Refuser'}
            </span>
            {escalation.ia_confidence && (
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                ({escalation.ia_confidence}% confiance)
              </span>
            )}
          </div>
          {escalation.ia_reasoning && (
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {escalation.ia_reasoning}
            </div>
          )}
        </div>
      )}

      {/* Context Info */}
      {(escalation.prospect_name || Object.keys(contextData).length > 0) && (
        <div style={{ marginBottom: 12 }}>
          <button
            onClick={() => setShowDetails(!showDetails)}
            style={{
              fontSize: 12, color: 'var(--text-muted)', background: 'none',
              border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4,
            }}
          >
            {showDetails ? '▾' : '▸'} Détails
          </button>
          {showDetails && (
            <div style={{ marginTop: 8, fontSize: 12, color: 'var(--text-muted)', paddingLeft: 16 }}>
              {escalation.prospect_name && (
                <div>Prospect : <strong style={{ color: 'var(--text)' }}>{escalation.prospect_name}</strong></div>
              )}
              {contextData.devis_numero && (
                <div>Devis : {contextData.devis_numero}</div>
              )}
              {contextData.client_name && (
                <div>Client : {contextData.client_name}</div>
              )}
              {contextData.service_type && (
                <div>Service : {contextData.service_type}</div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Auto-resolve info */}
      {escalation.auto_resolve_at && (
        <div style={{
          fontSize: 11, color: 'var(--text-muted)', padding: '8px 12px',
          background: 'var(--surface)', borderRadius: 6, marginBottom: 12,
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <Clock size={12} />
          Auto-résolution dans {Math.round((new Date(escalation.auto_resolve_at).getTime() - Date.now()) / (1000 * 60 * 60))}h
          → action par défaut : <strong>{escalation.default_action === 'approve' ? 'Approuver' : 'Refuser'}</strong>
        </div>
      )}

      {/* Note field */}
      <div style={{ marginBottom: 12 }}>
        <textarea
          value={note}
          onChange={e => setNote(e.target.value)}
          placeholder="Note de décision (optionnel)"
          style={{
            width: '100%', padding: '8px 12px', borderRadius: 6,
            border: '1px solid var(--border)', background: 'var(--surface)',
            color: 'var(--text)', fontSize: 13, fontFamily: 'inherit',
            minHeight: 60, resize: 'vertical', boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 10 }}>
        <button
          onClick={() => handleDecide('approve')}
          disabled={deciding}
          style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            padding: '10px 18px', borderRadius: 8, border: 'none',
            background: '#22c55e', color: 'white', fontSize: 13, fontWeight: 600,
            cursor: 'pointer', opacity: deciding ? 0.7 : 1,
          }}
        >
          {deciding ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
          Approuver
        </button>
        <button
          onClick={() => handleDecide('reject')}
          disabled={deciding}
          style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            padding: '10px 18px', borderRadius: 8, border: '1px solid var(--border)',
            background: 'transparent', color: 'var(--text)', fontSize: 13, fontWeight: 600,
            cursor: 'pointer', opacity: deciding ? 0.7 : 1,
          }}
        >
          {deciding ? <Loader2 size={14} className="animate-spin" /> : <XCircle size={14} />}
          Refuser
        </button>
      </div>
    </div>
  )
}

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<Escalation[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('pending')

  const load = async () => {
    setLoading(true)
    try {
      const [escRes, statsRes] = await Promise.all([
        fetch(`${API}/api/escalations?status=${filter}`),
        fetch(`${API}/api/escalations/stats`),
      ])
      setEscalations(await escRes.json())
      setStats(await statsRes.json())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [filter])

  const handleDecide = (id: number, decision: string) => {
    // Retirer l'escalation de la liste
    setEscalations(prev => prev.filter(e => e.id !== id))
    // Recharger les stats
    fetch(`${API}/api/escalations/stats`).then(r => r.json()).then(setStats)
  }

  if (loading) {
    return (
      <div style={{ padding: '32px 36px', display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)' }}>
        <Loader2 size={18} className="animate-spin" /> Chargement...
      </div>
    )
  }

  return (
    <div style={{ padding: '32px 36px', maxWidth: 1200 }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Escalations</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 6, fontSize: 13 }}>
          Décisions nécessitant validation humaine
        </p>
      </div>

      {/* Stats */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
          {[
            { label: 'En attente', value: stats.pending, color: '#f97316', active: filter === 'pending' },
            { label: 'Approuvées', value: stats.approved, color: '#22c55e', active: filter === 'approved' },
            { label: 'Refusées', value: stats.rejected, color: '#ef4444', active: filter === 'rejected' },
            { label: 'Auto-résolues', value: stats.auto_resolved, color: '#64748b', active: filter === 'auto_resolved' },
          ].map((stat) => (
            <button
              key={stat.label}
              onClick={() => setFilter(stat.label === 'En attente' ? 'pending' : stat.label === 'Approuvées' ? 'approved' : stat.label === 'Refusées' ? 'rejected' : 'auto_resolved')}
              className="card"
              style={{
                padding: '20px', textAlign: 'center', cursor: 'pointer',
                border: stat.active ? `2px solid ${stat.color}` : '1px solid var(--border)',
                background: stat.active ? `${stat.color}08` : 'var(--card)',
              }}
            >
              <div style={{ fontSize: 28, fontWeight: 700, fontFamily: 'DM Sans', color: stat.color, letterSpacing: '-0.5px' }}>
                {stat.value}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {stat.label}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <Filter size={16} color="var(--text-muted)" />
        <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Affichage :</span>
        <select
          value={filter}
          onChange={e => setFilter(e.target.value)}
          style={{
            padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)',
            background: 'var(--surface)', color: 'var(--text)', fontSize: 13, cursor: 'pointer',
          }}
        >
          <option value="pending">En attente</option>
          <option value="approved">Approuvées</option>
          <option value="rejected">Refusées</option>
          <option value="auto_resolved">Auto-résolues</option>
        </select>
        <button
          onClick={load}
          style={{
            marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6,
            padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)',
            background: 'transparent', color: 'var(--text-muted)', fontSize: 13, cursor: 'pointer',
          }}
        >
          <RefreshCw size={14} /> Actualiser
        </button>
      </div>

      {/* Liste escalations */}
      {escalations.length === 0 ? (
        <div className="card" style={{ padding: '48px 32px', textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✓</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>
            Aucune escalation {filter === 'pending' ? 'en attente' : filter}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            Toutes les décisions sont prises !
          </div>
        </div>
      ) : (
        <div>
          {escalations.map(esc => (
            filter === 'pending' ? (
              <EscalationCard key={esc.id} escalation={esc} onDecide={handleDecide} />
            ) : (
              <div key={esc.id} className="card" style={{ padding: '16px 20px', marginBottom: 12, opacity: 0.7 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>{esc.title}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                      {esc.decided_at && `Décidé le ${new Date(esc.decided_at).toLocaleDateString('fr-FR')}`}
                      {esc.approved_by && ` par ${esc.approved_by}`}
                    </div>
                  </div>
                  <span style={{
                    padding: '4px 12px', borderRadius: 12, fontSize: 11, fontWeight: 600,
                    background: esc.status === 'approved' ? '#22c55e18' : '#ef444418',
                    color: esc.status === 'approved' ? '#22c55e' : '#ef4444',
                  }}>
                    {esc.status === 'approved' ? '✓ Approuvé' : '✕ Refusé'}
                  </span>
                </div>
              </div>
            )
          ))}
        </div>
      )}
    </div>
  )
}
