'use client'
import { useEffect, useState, useCallback } from 'react'
import { fetchClients } from '@/lib/api'
import { FileText, Euro, TrendingUp, Clock, Search, Plus, Loader2, X, Check, Download } from 'lucide-react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Devis = {
  id: number; numero: string; client_id: number; client_name: string
  service_type: string; description: string | null
  montant_ht: number; montant_ttc: number; tva_pct: number
  frequence: string; status: string; created_at: string; sent_at: string | null
}
type Stats = { total: number; envoyes: number; acceptes: number; ca_pipeline: number; ca_signe: number; taux_conversion: number }

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  brouillon: { label: '✏️ Brouillon',  color: '#64748b' },
  envoye:    { label: '📤 Envoyé',     color: '#3b82f6' },
  accepte:   { label: '✅ Accepté',    color: '#22c55e' },
  refuse:    { label: '❌ Refusé',     color: '#ef4444' },
  expire:    { label: '⏰ Expiré',     color: '#f97316' },
}

const SERVICE_LABELS: Record<string, string> = {
  bureaux: '🏢 Bureaux', fin_chantier: '🔨 Fin de chantier',
  copropriete: '🏘 Copropriété', autre: '📦 Autre',
}

const FREQ_LABELS: Record<string, string> = {
  unique: 'Unique', hebdo: 'Hebdo', bihebdo: 'Bi-hebdo', mensuel: 'Mensuel',
}

function KpiCard({ icon: Icon, label, value, sub, color }: { icon: React.ElementType; label: string; value: string | number; sub?: string; color: string }) {
  return (
    <div className="card" style={{ padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 16 }}>
      <div style={{ width: 44, height: 44, borderRadius: 12, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={20} color={color} strokeWidth={1.8} />
      </div>
      <div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 500 }}>{label}</div>
        <div style={{ fontFamily: 'Syne', fontSize: 24, fontWeight: 700, lineHeight: 1.2, marginTop: 2 }}>{value}</div>
        {sub && <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>{sub}</div>}
      </div>
    </div>
  )
}

function NewDevisModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [clients, setClients] = useState<any[]>([])
  const [form, setForm] = useState({
    client_id: '', service_type: 'bureaux', description: '',
    surface_m2: '', frequence: 'unique', montant_ht: '', tva_pct: '20', notes: '',
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => { fetchClients().then(setClients) }, [])

  const ht  = parseFloat(form.montant_ht)  || 0
  const tva = parseFloat(form.tva_pct)     || 20
  const ttc = Math.round(ht * (1 + tva / 100) * 100) / 100

  const handleSubmit = async () => {
    if (!form.client_id || !form.montant_ht) return
    setSaving(true)
    try {
      await fetch(`${API}/api/devis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, client_id: parseInt(form.client_id), montant_ht: ht, tva_pct: tva, surface_m2: parseFloat(form.surface_m2) || null }),
      })
      onCreated(); onClose()
    } finally { setSaving(false) }
  }

  const inputStyle = { width: '100%', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '9px 12px', color: 'var(--text)', fontSize: 13, outline: 'none', boxSizing: 'border-box' as const }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="card" style={{ width: 560, maxHeight: '88vh', overflowY: 'auto', padding: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 style={{ fontFamily: 'Syne', fontSize: 18, fontWeight: 700, margin: 0 }}>Nouveau devis</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X size={18} /></button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Client */}
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Client *</label>
            <select value={form.client_id} onChange={e => setForm(f => ({ ...f, client_id: e.target.value }))} style={inputStyle}>
              <option value="">— Sélectionner un client —</option>
              {clients.map(c => <option key={c.id} value={c.id}>{c.company_name}{c.city ? ` (${c.city})` : ''}</option>)}
            </select>
          </div>

          {/* Service + Fréquence */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Type de prestation</label>
              <select value={form.service_type} onChange={e => setForm(f => ({ ...f, service_type: e.target.value }))} style={inputStyle}>
                <option value="bureaux">🏢 Bureaux</option>
                <option value="fin_chantier">🔨 Fin de chantier</option>
                <option value="copropriete">🏘 Copropriété</option>
                <option value="autre">📦 Autre</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Fréquence</label>
              <select value={form.frequence} onChange={e => setForm(f => ({ ...f, frequence: e.target.value }))} style={inputStyle}>
                <option value="unique">Prestation unique</option>
                <option value="hebdo">Hebdomadaire</option>
                <option value="bihebdo">Bi-hebdomadaire</option>
                <option value="mensuel">Mensuelle</option>
              </select>
            </div>
          </div>

          {/* Description */}
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Description du chantier</label>
            <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Ex: Nettoyage complet de bureaux 3 pièces, vitres comprises..." rows={3}
              style={{ ...inputStyle, resize: 'vertical' as const }} />
          </div>

          {/* Surface */}
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Superficie (m²)</label>
            <input type="number" value={form.surface_m2} onChange={e => setForm(f => ({ ...f, surface_m2: e.target.value }))}
              placeholder="Ex: 120" style={inputStyle} />
          </div>

          {/* Montants */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Montant HT (€) *</label>
              <input type="number" value={form.montant_ht} onChange={e => setForm(f => ({ ...f, montant_ht: e.target.value }))}
                placeholder="0.00" style={inputStyle} />
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>TVA (%)</label>
              <select value={form.tva_pct} onChange={e => setForm(f => ({ ...f, tva_pct: e.target.value }))} style={inputStyle}>
                <option value="20">20% (standard)</option>
                <option value="10">10% (réduit)</option>
                <option value="5.5">5,5%</option>
                <option value="0">0% (exonéré)</option>
              </select>
            </div>
          </div>

          {/* Calcul TTC live */}
          {ht > 0 && (
            <div style={{ background: 'var(--surface)', borderRadius: 10, padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Total TTC</div>
              <div style={{ fontFamily: 'Syne', fontSize: 22, fontWeight: 700, color: '#22c55e' }}>{ttc.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} €</div>
            </div>
          )}

          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Notes internes</label>
            <textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} rows={2} style={{ ...inputStyle, resize: 'vertical' as const }} />
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '9px 18px', borderRadius: 8, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-muted)', fontSize: 13, cursor: 'pointer' }}>Annuler</button>
          <button onClick={handleSubmit} disabled={saving || !form.client_id || !form.montant_ht} style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--accent)', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, opacity: (!form.client_id || !form.montant_ht) ? 0.5 : 1 }}>
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Créer le devis
          </button>
        </div>
      </div>
    </div>
  )
}

export default function DevisPage() {
  const [devisList, setDevisList] = useState<Devis[]>([])
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
      const [d, s] = await Promise.all([
        fetch(`${API}/api/devis?${params}`).then(r => r.json()),
        fetch(`${API}/api/devis/stats/summary`).then(r => r.json()),
      ])
      setDevisList(d); setStats(s)
    } finally { setLoading(false) }
  }, [search, statusFilter])

  useEffect(() => { const t = setTimeout(load, 300); return () => clearTimeout(t) }, [load])

  const inputStyle = { background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '7px 12px', color: 'var(--text)', fontSize: 13, outline: 'none' }

  const changeStatus = async (id: number, status: string) => {
    await fetch(`${API}/api/devis/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) })
    load()
  }

  return (
    <div style={{ padding: '32px 36px' }}>
      {showModal && <NewDevisModal onClose={() => setShowModal(false)} onCreated={load} />}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontFamily: 'Syne', fontSize: 28, fontWeight: 800, margin: 0 }}>Devis</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 4, fontSize: 14 }}>{devisList.length} devis</p>
        </div>
        <button onClick={() => setShowModal(true)} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--accent)', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
          <Plus size={15} /> Nouveau devis
        </button>
      </div>

      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
          <KpiCard icon={FileText}    label="Total devis"       value={stats.total}              color="#3b82f6" />
          <KpiCard icon={Clock}       label="En attente"        value={stats.envoyes}            color="#f97316" />
          <KpiCard icon={TrendingUp}  label="Taux de conversion" value={`${stats.taux_conversion}%`} color="#22c55e" />
          <KpiCard icon={Euro}        label="CA signé HT"       value={`${(stats.ca_signe ?? 0).toLocaleString('fr-FR')} €`} sub={`Pipeline : ${(stats.ca_pipeline ?? 0).toLocaleString('fr-FR')} €`} color="#a78bfa" />
        </div>
      )}

      <div className="card" style={{ padding: '14px 20px', marginBottom: 20, display: 'flex', gap: 12 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input placeholder="Rechercher un client..." value={search} onChange={e => setSearch(e.target.value)} style={{ ...inputStyle, paddingLeft: 30, width: '100%' }} />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={inputStyle}>
          <option value="">Tous les statuts</option>
          <option value="brouillon">Brouillon</option>
          <option value="envoye">Envoyé</option>
          <option value="accepte">Accepté</option>
          <option value="refuse">Refusé</option>
          <option value="expire">Expiré</option>
        </select>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60, gap: 10, color: 'var(--text-muted)' }}>
            <Loader2 size={18} className="animate-spin" /> Chargement...
          </div>
        ) : devisList.length === 0 ? (
          <div style={{ padding: 64, textAlign: 'center' }}>
            <FileText size={40} color="var(--text-dim)" style={{ margin: '0 auto 16px' }} />
            <div style={{ fontFamily: 'Syne', fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Aucun devis encore</div>
            <div style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 20 }}>Crée ton premier devis pour un client.</div>
            <button onClick={() => setShowModal(true)} style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--accent)', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
              + Créer un devis
            </button>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Numéro', 'Client', 'Prestation', 'Montant HT', 'TTC', 'Statut', 'Date', 'Action'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {devisList.map((d, i) => {
                const sc = STATUS_CONFIG[d.status] || STATUS_CONFIG.brouillon
                return (
                  <tr key={d.id} style={{ borderBottom: i < devisList.length - 1 ? '1px solid var(--border-soft)' : 'none' }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                    <td style={{ padding: '14px 16px', fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)' }}>{d.numero}</td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{d.client_name || '—'}</div>
                      {d.description && <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.description}</div>}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 12, color: 'var(--text-muted)' }}>
                      <div>{SERVICE_LABELS[d.service_type] || d.service_type}</div>
                      <div style={{ fontSize: 11, marginTop: 2 }}>{FREQ_LABELS[d.frequence] || d.frequence}</div>
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 14, fontWeight: 600 }}>{(d.montant_ht || 0).toLocaleString('fr-FR')} €</td>
                    <td style={{ padding: '14px 16px', fontSize: 13, color: '#22c55e', fontWeight: 600 }}>{(d.montant_ttc || 0).toLocaleString('fr-FR')} €</td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, background: `${sc.color}18`, color: sc.color, border: `1px solid ${sc.color}30` }}>
                        {sc.label}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 12, color: 'var(--text-muted)' }}>
                      {d.created_at ? new Date(d.created_at).toLocaleDateString('fr-FR') : '—'}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <select
                          value={d.status}
                          onChange={e => changeStatus(d.id, e.target.value)}
                          style={{ fontSize: 11, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: '4px 8px', color: 'var(--text-muted)', cursor: 'pointer', outline: 'none' }}
                        >
                          <option value="brouillon">Brouillon</option>
                          <option value="envoye">Envoyé</option>
                          <option value="accepte">Accepté</option>
                          <option value="refuse">Refusé</option>
                          <option value="expire">Expiré</option>
                        </select>
                        <a
                          href={`${API}/api/devis/${d.id}/pdf`}
                          target="_blank"
                          rel="noreferrer"
                          title="Télécharger le PDF"
                          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--accent)', textDecoration: 'none', flexShrink: 0 }}
                        >
                          <Download size={13} />
                        </a>
                      </div>
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