'use client'
import { useEffect, useState, useCallback } from 'react'
import { fetchProspects, fetchCities } from '@/lib/api'
import { Search, Filter, Mail, Phone, Globe, MapPin, ExternalLink, Loader2 } from 'lucide-react'
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
  status: string
}

function ScoreBadge({ label, score }: { label: string; score: number }) {
  const cls = label?.includes('haute') ? 'badge-haute'
    : label?.includes('moyenne') ? 'badge-moyenne'
    : label?.includes('faible') ? 'badge-faible'
    : 'badge-nulle'
  return (
    <span className={cls} style={{ padding: '2px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap' }}>
      {score}pts
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; color: string }> = {
    new:             { label: 'Nouveau',   color: '#3b82f6' },
    scored:          { label: 'Scoré',     color: '#8b5cf6' },
    email_generated: { label: 'Email prêt',color: '#06b6d4' },
    contacted:       { label: 'Contacté',  color: '#f97316' },
    replied:         { label: 'Répondu',   color: '#eab308' },
    signed:          { label: 'Signé ✓',   color: '#22c55e' },
    lost:            { label: 'Perdu',     color: '#64748b' },
  }
  const s = map[status] || { label: status, color: '#64748b' }
  return (
    <span style={{
      padding: '2px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600,
      background: `${s.color}18`, color: s.color, border: `1px solid ${s.color}30`,
    }}>
      {s.label}
    </span>
  )
}

export default function ProspectsPage() {
  const [prospects, setProspects] = useState<Prospect[]>([])
  const [cities, setCities] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  const [search, setSearch]     = useState('')
  const [city, setCity]         = useState('')
  const [status, setStatus]     = useState('')
  const [minScore, setMinScore] = useState('')
  const [hasEmail, setHasEmail] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchProspects({
        search:    search || undefined,
        city:      city || undefined,
        status:    status || undefined,
        min_score: minScore ? Number(minScore) : undefined,
        has_email: hasEmail === 'true' ? true : hasEmail === 'false' ? false : undefined,
        limit:     500,
      })
      setProspects(data)
    } finally {
      setLoading(false)
    }
  }, [search, city, status, minScore, hasEmail])

  useEffect(() => {
    fetchCities().then(setCities)
  }, [])

  useEffect(() => {
    const t = setTimeout(load, 300)
    return () => clearTimeout(t)
  }, [load])

  const inputStyle = {
    background: 'var(--card)',
    border: '1px solid var(--border)',
    borderRadius: 8,
    padding: '7px 12px',
    color: 'var(--text)',
    fontSize: 13,
    outline: 'none',
  }

  return (
    <div style={{ padding: '32px 36px' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontFamily: 'Syne', fontSize: 28, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' }}>
            Prospects
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 4, fontSize: 14 }}>
            {prospects.length} résultat{prospects.length > 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Filtres */}
      <div className="card" style={{ padding: '16px 20px', marginBottom: 20, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <Filter size={15} color="var(--text-muted)" />

        {/* Recherche */}
        <div style={{ position: 'relative', flex: '1 1 200px' }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            placeholder="Rechercher une entreprise..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ ...inputStyle, paddingLeft: 30, width: '100%' }}
          />
        </div>

        {/* Ville */}
        <select value={city} onChange={e => setCity(e.target.value)} style={{ ...inputStyle, minWidth: 160 }}>
          <option value="">Toutes les villes</option>
          {cities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        {/* Score min */}
        <select value={minScore} onChange={e => setMinScore(e.target.value)} style={{ ...inputStyle }}>
          <option value="">Tous les scores</option>
          <option value="75">🔥 Priorité haute (75+)</option>
          <option value="50">⚡ Moyenne (50+)</option>
          <option value="25">🌱 Faible (25+)</option>
        </select>

        {/* Email */}
        <select value={hasEmail} onChange={e => setHasEmail(e.target.value)} style={{ ...inputStyle }}>
          <option value="">Avec ou sans email</option>
          <option value="true">✉ Avec email</option>
          <option value="false">❌ Sans email</option>
        </select>

        {/* Statut */}
        <select value={status} onChange={e => setStatus(e.target.value)} style={{ ...inputStyle }}>
          <option value="">Tous les statuts</option>
          <option value="new">Nouveau</option>
          <option value="scored">Scoré</option>
          <option value="contacted">Contacté</option>
          <option value="replied">Répondu</option>
          <option value="signed">Signé</option>
          <option value="lost">Perdu</option>
        </select>
      </div>

      {/* Tableau */}
      <div className="card" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60, gap: 10, color: 'var(--text-muted)' }}>
            <Loader2 size={18} className="animate-spin" /> Chargement...
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Entreprise', 'Ville', 'Contact', 'Score', 'Statut', ''].map(h => (
                  <th key={h} style={{
                    padding: '12px 16px', textAlign: 'left', fontSize: 11,
                    fontWeight: 600, color: 'var(--text-muted)',
                    textTransform: 'uppercase', letterSpacing: '0.08em',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {prospects.map((p, i) => (
                <tr key={p.id} style={{
                  borderBottom: i < prospects.length - 1 ? '1px solid var(--border-soft)' : 'none',
                  transition: 'background 0.1s',
                }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  {/* Entreprise */}
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text)' }}>{p.company_name}</div>
                    {p.address && (
                      <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <MapPin size={10} /> {p.address.slice(0, 45)}{p.address.length > 45 ? '…' : ''}
                      </div>
                    )}
                  </td>

                  {/* Ville */}
                  <td style={{ padding: '14px 16px', fontSize: 13, color: 'var(--text-muted)' }}>
                    {p.city || '—'}
                  </td>

                  {/* Contact */}
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {p.email && (
                        <a href={`mailto:${p.email}`} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: 'var(--accent)', textDecoration: 'none' }}>
                          <Mail size={12} /> {p.email}
                        </a>
                      )}
                      {p.phone && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: 'var(--text-muted)' }}>
                          <Phone size={12} /> {p.phone}
                        </span>
                      )}
                      {p.website && !p.email && !p.phone && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: 'var(--text-dim)' }}>
                          <Globe size={12} /> {p.website}
                        </span>
                      )}
                      {!p.email && !p.phone && !p.website && (
                        <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>—</span>
                      )}
                    </div>
                  </td>

                  {/* Score */}
                  <td style={{ padding: '14px 16px' }}>
                    <ScoreBadge label={p.score_label} score={p.lead_score} />
                  </td>

                  {/* Statut */}
                  <td style={{ padding: '14px 16px' }}>
                    <StatusBadge status={p.status} />
                  </td>

                  {/* Action */}
                  <td style={{ padding: '14px 16px' }}>
                    <Link href={`/prospects/${p.id}`} style={{
                      display: 'flex', alignItems: 'center', gap: 4,
                      fontSize: 12, color: 'var(--text-muted)', textDecoration: 'none',
                    }}>
                      <ExternalLink size={13} /> Voir
                    </Link>
                  </td>
                </tr>
              ))}

              {prospects.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                    Aucun prospect trouvé avec ces filtres.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
