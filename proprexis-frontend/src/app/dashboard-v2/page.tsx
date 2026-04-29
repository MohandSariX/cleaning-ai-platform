'use client'
import { useEffect, useState } from 'react'
import { Mail, FileText, TrendingUp, Activity, Zap, Loader2 } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type DashboardStats = {
  today: {
    emails_sent: number
    devis_generated: number
    devis_total_ttc: number
    replies_received: number
  }
  pipeline: {
    new: number
    contacted: number
    replied: number
    quoted: number
    won: number
  }
  top_prospects: Array<{
    id: number
    company_name: string
    city: string
    lead_score: number
    score_label: string
    source: string
  }>
  recent_activities: Array<{
    id: number
    timestamp: string
    event_type: string
    message: string
    status: string
  }>
}

function StatCard({ icon: Icon, label, value, color }: {
  icon: React.ElementType
  label: string
  value: string | number
  color: string
}) {
  return (
    <div className="card" style={{ padding: '20px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          width: 48, height: 48, borderRadius: 12,
          background: `${color}15`, display: 'flex',
          alignItems: 'center', justifyContent: 'center'
        }}>
          <Icon size={22} color={color} strokeWidth={2} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
            {label}
          </div>
          <div style={{ fontFamily: 'Syne', fontSize: 28, fontWeight: 800, color: 'var(--text)' }}>
            {value}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function DashboardV2() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/api/dashboard/stats`)
      .then(res => res.json())
      .then(setStats)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={{ padding: '32px 36px', display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)' }}>
        <Loader2 size={18} className="animate-spin" /> Chargement...
      </div>
    )
  }

  if (!stats) return null

  return (
    <div style={{ padding: '32px 36px', maxWidth: 1400 }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: 'Syne', fontSize: 32, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' }}>
          Command Center
        </h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 6, fontSize: 14 }}>
          Ce que Claude a fait aujourd'hui
        </p>
      </div>

      {/* Stats aujourd'hui */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontFamily: 'Syne', fontSize: 16, fontWeight: 700, marginBottom: 16, color: 'var(--text)' }}>
          ⚡ Activité du jour
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          <StatCard
            icon={Mail}
            label="Emails envoyés"
            value={stats.today.emails_sent}
            color="#3b82f6"
          />
          <StatCard
            icon={FileText}
            label="Devis générés"
            value={stats.today.devis_generated}
            color="#22c55e"
          />
          <StatCard
            icon={TrendingUp}
            label="Montant TTC"
            value={`${stats.today.devis_total_ttc.toLocaleString('fr-FR')}€`}
            color="#f97316"
          />
          <StatCard
            icon={Zap}
            label="Réponses reçues"
            value={stats.today.replies_received}
            color="#a78bfa"
          />
        </div>
      </div>

      {/* Pipeline */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontFamily: 'Syne', fontSize: 16, fontWeight: 700, marginBottom: 16, color: 'var(--text)' }}>
          📊 Pipeline
        </h2>
        <div className="card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', gap: 20 }}>
            {[
              { label: 'Nouveaux', value: stats.pipeline.new, color: '#64748b' },
              { label: 'Contactés', value: stats.pipeline.contacted, color: '#3b82f6' },
              { label: 'Répondus', value: stats.pipeline.replied, color: '#8b5cf6' },
              { label: 'Devis envoyés', value: stats.pipeline.quoted, color: '#f97316' },
              { label: 'Gagnés', value: stats.pipeline.won, color: '#22c55e' },
            ].map((stage, i) => (
              <div key={i} style={{ flex: 1, textAlign: 'center' }}>
                <div style={{
                  fontSize: 32, fontWeight: 800, fontFamily: 'Syne',
                  color: stage.color, marginBottom: 8
                }}>
                  {stage.value}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {stage.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Top Prospects */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 15, fontWeight: 700, margin: '0 0 16px' }}>
            🔥 Top Prospects (score &gt;80)
          </h3>
          {stats.top_prospects.length === 0 ? (
            <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              Aucun prospect avec score &gt;80
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {stats.top_prospects.slice(0, 5).map((p, i) => (
                <div key={p.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '12px', borderRadius: 8, background: 'var(--surface)'
                }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>
                      {p.company_name || 'Sans nom'}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {p.city} • {p.source}
                    </div>
                  </div>
                  <div style={{
                    fontSize: 18, fontWeight: 800, fontFamily: 'Syne',
                    color: p.lead_score >= 90 ? '#22c55e' : p.lead_score >= 85 ? '#f97316' : '#eab308'
                  }}>
                    {p.lead_score}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Timeline activité */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 15, fontWeight: 700, margin: '0 0 16px' }}>
            <Activity size={16} style={{ display: 'inline', marginRight: 6 }} />
            Timeline activité
          </h3>
          <div style={{ maxHeight: 300, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {stats.recent_activities.slice(0, 10).map((activity) => {
              const time = new Date(activity.timestamp).toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit'
              })

              return (
                <div key={activity.id} style={{
                  padding: '10px 12px', borderRadius: 6,
                  background: 'var(--surface)', fontSize: 12
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{
                      fontSize: 10, fontWeight: 600, color: 'var(--text-muted)',
                      textTransform: 'uppercase', letterSpacing: '0.05em'
                    }}>
                      {time}
                    </span>
                    <span style={{
                      padding: '2px 6px', borderRadius: 4, fontSize: 9,
                      background: activity.status === 'success' ? '#22c55e20' :
                                 activity.status === 'error' ? '#ef444420' : '#3b82f620',
                      color: activity.status === 'success' ? '#22c55e' :
                             activity.status === 'error' ? '#ef4444' : '#3b82f6',
                      fontWeight: 600, textTransform: 'uppercase'
                    }}>
                      {activity.event_type}
                    </span>
                  </div>
                  <div style={{ color: 'var(--text)', fontSize: 12 }}>
                    {activity.message}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
