'use client'
import { useEffect, useState } from 'react'
import { Calendar, MapPin, Clock, Loader2, CheckCircle, Circle, XCircle } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Chantier = {
  id: number
  titre: string
  type: string
  adresse: string
  ville: string
  date_debut: string
  heure_debut: string
  duree_heures: number
  statut: string
  client_nom: string
}

function StatusBadge({ status }: { status: string }) {
  const config = {
    planifie: { label: 'Planifié', color: '#3b82f6', icon: Circle },
    en_cours: { label: 'En cours', color: '#f97316', icon: Circle },
    termine: { label: 'Terminé', color: '#22c55e', icon: CheckCircle },
    annule: { label: 'Annulé', color: '#ef4444', icon: XCircle },
  }[status] || { label: status, color: '#64748b', icon: Circle }

  const Icon = config.icon

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '4px 10px',
      borderRadius: 6,
      background: `${config.color}15`,
      color: config.color,
      fontSize: 11,
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.05em'
    }}>
      <Icon size={12} fill={status === 'termine' ? config.color : 'none'} />
      {config.label}
    </div>
  )
}

function ChantierCard({ chantier }: { chantier: Chantier }) {
  const date = new Date(chantier.date_debut)
  const dateStr = date.toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long'
  })

  return (
    <div className="card" style={{ padding: '20px 24px', marginBottom: 12 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 4px', color: 'var(--text)' }}>
            {chantier.titre}
          </h3>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {chantier.client_nom || 'Client inconnu'}
          </div>
        </div>
        <StatusBadge status={chantier.statut} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'auto auto auto', gap: 16, fontSize: 13, color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Calendar size={14} />
          <span style={{ textTransform: 'capitalize' }}>{dateStr}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Clock size={14} />
          <span>
            {chantier.heure_debut || '08:00'}
            {chantier.duree_heures && ` (${chantier.duree_heures}h)`}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <MapPin size={14} />
          <span>{chantier.ville || chantier.adresse}</span>
        </div>
      </div>
    </div>
  )
}

export default function PlanningPage() {
  const [chantiers, setChantiers] = useState<Chantier[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/api/chantiers?limit=50`)
      .then(res => res.json())
      .then(data => {
        const sorted = (data.chantiers || data || []).sort((a: Chantier, b: Chantier) =>
          new Date(a.date_debut).getTime() - new Date(b.date_debut).getTime()
        )
        setChantiers(sorted)
      })
      .catch(err => console.error('Erreur chantiers:', err))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={{ padding: '32px 36px', display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)' }}>
        <Loader2 size={18} className="animate-spin" /> Chargement...
      </div>
    )
  }

  const planifies = chantiers.filter(c => c.statut === 'planifie')
  const enCours = chantiers.filter(c => c.statut === 'en_cours')
  const termines = chantiers.filter(c => c.statut === 'termine')

  return (
    <div style={{ padding: '32px 36px', maxWidth: 1200 }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0, letterSpacing: '-0.5px' }}>
          <Calendar size={28} style={{ display: 'inline', marginRight: 10, verticalAlign: 'middle' }} />
          Planning
        </h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 6, fontSize: 14 }}>
          Chantiers planifiés par Claude
        </p>
      </div>

      {chantiers.length === 0 ? (
        <div className="card" style={{ padding: '48px 24px', textAlign: 'center' }}>
          <Calendar size={48} color="var(--text-muted)" style={{ margin: '0 auto 16px', opacity: 0.3 }} />
          <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>
            Aucun chantier planifié
          </div>
        </div>
      ) : (
        <>
          {planifies.length > 0 && (
            <div style={{ marginBottom: 32 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>
                📅 À venir ({planifies.length})
              </h2>
              {planifies.map(chantier => <ChantierCard key={chantier.id} chantier={chantier} />)}
            </div>
          )}
        </>
      )}
    </div>
  )
}
