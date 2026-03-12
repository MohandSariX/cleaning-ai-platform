'use client'
import { useEffect, useState } from 'react'
import { fetchProspect, updateProspect } from '@/lib/api'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Mail, Phone, Globe, MapPin, Building2, Star, Loader2, Check } from 'lucide-react'
import Link from 'next/link'

type Prospect = {
  id: number
  company_name: string
  city: string
  address: string
  website: string | null
  email: string | null
  phone: string | null
  lead_score: number
  score_label: string
  score_explanation: string
  status: string
  industry: string
  created_at: string
}

const STATUSES = [
  { value: 'new',             label: 'Nouveau',    color: '#3b82f6' },
  { value: 'scored',          label: 'Scoré',      color: '#8b5cf6' },
  { value: 'email_generated', label: 'Email prêt', color: '#06b6d4' },
  { value: 'contacted',       label: 'Contacté',   color: '#f97316' },
  { value: 'replied',         label: 'Répondu',    color: '#eab308' },
  { value: 'signed',          label: 'Signé ✓',    color: '#22c55e' },
  { value: 'lost',            label: 'Perdu',      color: '#64748b' },
]

export default function ProspectPage() {
  const { id } = useParams()
  const router = useRouter()
  const [prospect, setProspect] = useState<Prospect | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetchProspect(Number(id)).then(setProspect).finally(() => setLoading(false))
  }, [id])

  const handleStatusChange = async (newStatus: string) => {
    if (!prospect) return
    setSaving(true)
    const updated = await updateProspect(prospect.id, { status: newStatus })
    setProspect(updated)
    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 10, color: 'var(--text-muted)' }}>
      <Loader2 size={18} className="animate-spin" /> Chargement...
    </div>
  )

  if (!prospect) return (
    <div style={{ padding: 32, color: 'var(--text-muted)' }}>Prospect introuvable.</div>
  )

  const scoreColor = prospect.score_label?.includes('haute') ? '#22c55e'
    : prospect.score_label?.includes('moyenne') ? '#eab308'
    : prospect.score_label?.includes('faible') ? '#f97316'
    : '#64748b'

  const explanationLines = prospect.score_explanation?.split('\n') || []

  return (
    <div style={{ padding: '32px 36px', maxWidth: 900 }}>

      {/* Back */}
      <Link href="/prospects" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-muted)', textDecoration: 'none', marginBottom: 24 }}>
        <ArrowLeft size={14} /> Retour aux prospects
      </Link>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontFamily: 'Syne', fontSize: 26, fontWeight: 800, margin: 0 }}>
            {prospect.company_name}
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
            <span style={{
              padding: '3px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700,
              background: `${scoreColor}18`, color: scoreColor, border: `1px solid ${scoreColor}30`,
            }}>
              {prospect.score_label}
            </span>
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              Score : <strong style={{ color: 'var(--text)' }}>{prospect.lead_score}/100</strong>
            </span>
          </div>
        </div>

        {/* Score visuel */}
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 72, height: 72, borderRadius: '50%',
            background: `conic-gradient(${scoreColor} ${prospect.lead_score * 3.6}deg, var(--border) 0deg)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            position: 'relative',
          }}>
            <div style={{
              width: 56, height: 56, borderRadius: '50%', background: 'var(--card)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: 'Syne', fontWeight: 800, fontSize: 16, color: scoreColor,
            }}>
              {prospect.lead_score}
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* Infos */}
        <div className="card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 14, fontWeight: 700, margin: '0 0 16px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Coordonnées
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {prospect.email && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Mail size={15} color="var(--accent)" />
                <a href={`mailto:${prospect.email}`} style={{ color: 'var(--accent)', fontSize: 13, textDecoration: 'none' }}>
                  {prospect.email}
                </a>
              </div>
            )}
            {prospect.phone && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Phone size={15} color="var(--text-muted)" />
                <span style={{ fontSize: 13 }}>{prospect.phone}</span>
              </div>
            )}
            {prospect.website && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Globe size={15} color="var(--text-muted)" />
                <a href={`https://${prospect.website.replace(/^https?:\/\//, '')}`} target="_blank" rel="noreferrer"
                  style={{ fontSize: 13, color: 'var(--text-muted)', textDecoration: 'none' }}>
                  {prospect.website}
                </a>
              </div>
            )}
            {prospect.address && (
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <MapPin size={15} color="var(--text-muted)" style={{ marginTop: 2 }} />
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{prospect.address}</span>
              </div>
            )}
            {prospect.city && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Building2 size={15} color="var(--text-muted)" />
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{prospect.city}</span>
              </div>
            )}
          </div>
        </div>

        {/* Statut */}
        <div className="card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 14, fontWeight: 700, margin: '0 0 16px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Statut pipeline
            {saving && <Loader2 size={13} className="animate-spin" style={{ marginLeft: 8, display: 'inline' }} />}
            {saved && <Check size={13} color="#22c55e" style={{ marginLeft: 8, display: 'inline' }} />}
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {STATUSES.map(s => (
              <button key={s.value} onClick={() => handleStatusChange(s.value)} style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 12px', borderRadius: 8, border: 'none', cursor: 'pointer',
                background: prospect.status === s.value ? `${s.color}18` : 'transparent',
                color: prospect.status === s.value ? s.color : 'var(--text-muted)',
                fontSize: 13, fontWeight: prospect.status === s.value ? 600 : 400,
                textAlign: 'left', transition: 'all 0.15s',
              }}>
                <div style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: prospect.status === s.value ? s.color : 'var(--border)',
                  flexShrink: 0,
                }} />
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Détail scoring */}
        <div className="card" style={{ padding: 24, gridColumn: '1 / -1' }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 14, fontWeight: 700, margin: '0 0 16px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            <Star size={14} style={{ display: 'inline', marginRight: 6 }} />
            Détail du scoring
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {explanationLines.map((line, i) => (
              <div key={i} style={{
                fontSize: 13,
                color: i === 0 ? 'var(--text)' : 'var(--text-muted)',
                fontWeight: i === 0 ? 600 : 400,
                padding: i === 0 ? '0 0 8px' : 0,
                borderBottom: i === 0 ? '1px solid var(--border-soft)' : 'none',
              }}>
                {line}
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
