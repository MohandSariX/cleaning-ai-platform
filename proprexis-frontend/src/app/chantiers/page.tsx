'use client'
import { useEffect, useState, useCallback } from 'react'
import { Briefcase, Clock, CheckCircle, Calendar, Search, Plus, Loader2, X, Check, MapPin, Ruler } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Chantier = {
  id: number; client_id: number; client_name: string
  titre: string; type: string; ville: string | null
  surface_m2: number | null; date_debut: string | null; date_fin: string | null
  heure_debut: string | null; duree_heures: number | null
  status: string; recurrence: string; created_at: string
}
type Stats = { total: number; planifies: number; en_cours: number; termines: number; surface_totale: number }

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  planifie:  { label: '📅 Planifié',   color: '#3b82f6' },
  en_cours:  { label: '⚡ En cours',   color: '#f97316' },
  termine:   { label: '✅ Terminé',    color: '#22c55e' },
  annule:    { label: '✕ Annulé',      color: '#64748b' },
}

const TYPE_LABELS: Record<string, string> = {
  bureaux: '🏢 Bureaux', fin_chantier: '🔨 Fin de chantier',
  copropriete: '🏘 Copropriété', autre: '📦 Autre',
}

const FREQ_LABELS: Record<string, string> = {
  unique: 'Unique', hebdo: 'Hebdo', bihebdo: 'Bi-hebdo', mensuel: 'Mensuel',
}

function KpiCard({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: string | number; color: string }) {
  return (
    <div className="card" style={{ padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 16 }}>
      <div style={{ width: 44, height: 44, borderRadius: 12, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Icon size={20} color={color} strokeWidth={1.8} />
      </div>
      <div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 500 }}>{label}</div>
        <div style={{ fontFamily: 'Syne', fontSize: 24, fontWeight: 700, lineHeight: 1.2, marginTop: 2 }}>{value}</div>
      </div>
    </div>
  )
}

function NewChantierModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [clients, setClients] = useState<any[]>([])
  const [form, setForm] = useState({
    client_id: '', titre: '', type: 'bureaux', adresse: '', ville: '',
    surface_m2: '', date_debut: '', date_fin: '', heure_debut: '',
    duree_heures: '', recurrence: 'unique', notes: '',
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetch(`${API}/api/clients`).then(r => r.json()).then(setClients)
  }, [])

  const handleSubmit = async () => {
    if (!form.client_id || !form.titre) return
    setSaving(true)
    try {
      await fetch(`${API}/api/chantiers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          client_id: parseInt(form.client_id),
          surface_m2: parseFloat(form.surface_m2) || null,
          duree_heures: parseFloat(form.duree_heures) || null,
          date_debut: form.date_debut || null,
          date_fin: form.date_fin || null,
          heure_debut: form.heure_debut || null,
          status: 'planifie',
        }),
      })
      onCreated(); onClose()
    } finally { setSaving(false) }
  }

  const inputStyle = { width: '100%', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '9px 12px', color: 'var(--text)', fontSize: 13, outline: 'none', boxSizing: 'border-box' as const }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="card" style={{ width: 560, maxHeight: '88vh', overflowY: 'auto', padding: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 style={{ fontFamily: 'Syne', fontSize: 18, fontWeight: 700, margin: 0 }}>Nouveau chantier</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X size={18} /></button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Client *</label>
            <select value={form.client_id} onChange={e => setForm(f => ({ ...f, client_id: e.target.value }))} style={inputStyle}>
              <option value="">— Sélectionner un client —</option>
              {clients.map(c => <option key={c.id} value={c.id}>{c.company_name}{c.city ? ` (${c.city})` : ''}</option>)}
            </select>
          </div>

          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Intitulé du chantier *</label>
            <input value={form.titre} onChange={e => setForm(f => ({ ...f, titre: e.target.value }))}
              placeholder="Ex: Nettoyage fin de chantier — 12 rue du Port" style={inputStyle} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Type</label>
              <select value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))} style={inputStyle}>
                <option value="bureaux">🏢 Bureaux</option>
                <option value="fin_chantier">🔨 Fin de chantier</option>
                <option value="copropriete">🏘 Copropriété</option>
                <option value="autre">📦 Autre</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Récurrence</label>
              <select value={form.recurrence} onChange={e => setForm(f => ({ ...f, recurrence: e.target.value }))} style={inputStyle}>
                <option value="unique">Prestation unique</option>
                <option value="hebdo">Hebdomadaire</option>
                <option value="bihebdo">Bi-hebdomadaire</option>
                <option value="mensuel">Mensuelle</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Adresse du chantier</label>
              <input value={form.adresse} onChange={e => setForm(f => ({ ...f, adresse: e.target.value }))} placeholder="12 rue de la Paix" style={inputStyle} />
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Ville</label>
              <input value={form.ville} onChange={e => setForm(f => ({ ...f, ville: e.target.value }))} placeholder="Paris" style={inputStyle} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Surface (m²)</label>
              <input type="number" value={form.surface_m2} onChange={e => setForm(f => ({ ...f, surface_m2: e.target.value }))} placeholder="120" style={inputStyle} />
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Heure début</label>
              <input type="time" value={form.heure_debut} onChange={e => setForm(f => ({ ...f, heure_debut: e.target.value }))} style={inputStyle} />
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Durée (h)</label>
              <input type="number" step="0.5" value={form.duree_heures} onChange={e => setForm(f => ({ ...f, duree_heures: e.target.value }))} placeholder="3" style={inputStyle} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Date de début</label>
              <input type="date" value={form.date_debut} onChange={e => setForm(f => ({ ...f, date_debut: e.target.value }))} style={inputStyle} />
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Date de fin</label>
              <input type="date" value={form.date_fin} onChange={e => setForm(f => ({ ...f, date_fin: e.target.value }))} style={inputStyle} />
            </div>
          </div>

          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Notes</label>
            <textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} rows={2} style={{ ...inputStyle, resize: 'vertical' as const }} />
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '9px 18px', borderRadius: 8, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-muted)', fontSize: 13, cursor: 'pointer' }}>Annuler</button>
          <button onClick={handleSubmit} disabled={saving || !form.client_id || !form.titre} style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--accent)', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, opacity: (!form.client_id || !form.titre) ? 0.5 : 1 }}>
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Créer le chantier
          </button>
        </div>
      </div>
    </div>
  )
}

export default function ChantiersPage() {
  const [chantiers, setChantiers] = useState<Chantier[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showModal, setShowModal] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (statusFilter) params.set('status', statusFilter)
      const [c, s] = await Promise.all([
        fetch(`${API}/api/chantiers?${params}`).then(r => r.json()),
        fetch(`${API}/api/chantiers/stats/summary`).then(r => r.json()),
      ])
      setChantiers(c); setStats(s)
    } finally { setLoading(false) }
  }, [search, statusFilter])

  useEffect(() => { const t = setTimeout(load, 300); return () => clearTimeout(t) }, [load])

  const changeStatus = async (id: number, status: string) => {
    await fetch(`${API}/api/chantiers/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) })
    load()
  }

  const inputStyle = { background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '7px 12px', color: 'var(--text)', fontSize: 13, outline: 'none' }

  return (
    <div style={{ padding: '32px 36px' }}>
      {showModal && <NewChantierModal onClose={() => setShowModal(false)} onCreated={load} />}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontFamily: 'Syne', fontSize: 28, fontWeight: 800, margin: 0 }}>Chantiers</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 4, fontSize: 14 }}>{chantiers.length} chantier{chantiers.length > 1 ? 's' : ''}</p>
        </div>
        <button onClick={() => setShowModal(true)} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--accent)', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
          <Plus size={15} /> Nouveau chantier
        </button>
      </div>

      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
          <KpiCard icon={Briefcase}    label="Total chantiers"  value={stats.total}          color="#3b82f6" />
          <KpiCard icon={Calendar}     label="Planifiés"        value={stats.planifies}      color="#a78bfa" />
          <KpiCard icon={Clock}        label="En cours"         value={stats.en_cours}       color="#f97316" />
          <KpiCard icon={Ruler}        label="Surface totale"   value={`${stats.surface_totale.toLocaleString('fr-FR')} m²`} color="#22c55e" />
        </div>
      )}

      <div className="card" style={{ padding: '14px 20px', marginBottom: 20, display: 'flex', gap: 12 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input placeholder="Rechercher un client..." value={search} onChange={e => setSearch(e.target.value)} style={{ ...inputStyle, paddingLeft: 30, width: '100%' }} />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={inputStyle}>
          <option value="">Tous les statuts</option>
          <option value="planifie">Planifié</option>
          <option value="en_cours">En cours</option>
          <option value="termine">Terminé</option>
          <option value="annule">Annulé</option>
        </select>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60, gap: 10, color: 'var(--text-muted)' }}>
            <Loader2 size={18} className="animate-spin" /> Chargement...
          </div>
        ) : chantiers.length === 0 ? (
          <div style={{ padding: 64, textAlign: 'center' }}>
            <Briefcase size={40} color="var(--text-dim)" style={{ margin: '0 auto 16px' }} />
            <div style={{ fontFamily: 'Syne', fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Aucun chantier encore</div>
            <div style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 20 }}>Planifie ta première intervention.</div>
            <button onClick={() => setShowModal(true)} style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--accent)', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
              + Créer un chantier
            </button>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Chantier', 'Client', 'Type', 'Date', 'Durée', 'Statut', 'Action'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {chantiers.map((c, i) => {
                const sc = STATUS_CONFIG[c.status] || STATUS_CONFIG.planifie
                return (
                  <tr key={c.id} style={{ borderBottom: i < chantiers.length - 1 ? '1px solid var(--border-soft)' : 'none' }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{c.titre}</div>
                      {c.ville && <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 3 }}><MapPin size={10} />{c.ville}</div>}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 13, fontWeight: 500 }}>{c.client_name || '—'}</td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{TYPE_LABELS[c.type] || c.type}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>{FREQ_LABELS[c.recurrence] || c.recurrence}</div>
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 12, color: 'var(--text-muted)' }}>
                      {c.date_debut ? new Date(c.date_debut).toLocaleDateString('fr-FR') : '—'}
                      {c.heure_debut && <div style={{ fontSize: 11, marginTop: 2 }}>🕐 {c.heure_debut}</div>}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 13, color: 'var(--text-muted)' }}>
                      {c.duree_heures ? `${c.duree_heures}h` : '—'}
                      {c.surface_m2 && <div style={{ fontSize: 11, marginTop: 2 }}>{c.surface_m2} m²</div>}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, background: `${sc.color}18`, color: sc.color, border: `1px solid ${sc.color}30` }}>
                        {sc.label}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <select value={c.status} onChange={e => changeStatus(c.id, e.target.value)}
                        style={{ fontSize: 11, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: '4px 8px', color: 'var(--text-muted)', cursor: 'pointer', outline: 'none' }}>
                        <option value="planifie">Planifié</option>
                        <option value="en_cours">En cours</option>
                        <option value="termine">Terminé</option>
                        <option value="annule">Annulé</option>
                      </select>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}