'use client'
import { useEffect, useState, useCallback } from 'react'
import { Receipt, Euro, Clock, AlertTriangle, Search, Plus, Loader2, X, Check, TrendingUp, Download } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Facture = {
  id: number; numero: string; client_id: number; client_name: string
  montant_ht: number; montant_ttc: number; tva_pct: number
  description: string | null; status: string
  date_emission: string | null; date_echeance: string | null; date_paiement: string | null
  created_at: string
}
type Stats = {
  total: number; payees: number; en_attente: number; en_retard: number
  ca_encaisse: number; ca_en_attente: number
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  brouillon:  { label: '✏️ Brouillon',    color: '#64748b' },
  envoyee:    { label: '📤 Envoyée',      color: '#3b82f6' },
  payee:      { label: '✅ Payée',        color: '#22c55e' },
  en_retard:  { label: '⚠️ En retard',   color: '#ef4444' },
  annulee:    { label: '✕ Annulée',       color: '#94a3b8' },
}

function KpiCard({ icon: Icon, label, value, sub, color }: { icon: React.ElementType; label: string; value: string | number; sub?: string; color: string }) {
  return (
    <div className="card" style={{ padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 16 }}>
      <div style={{ width: 44, height: 44, borderRadius: 12, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Icon size={20} color={color} strokeWidth={1.8} />
      </div>
      <div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 500 }}>{label}</div>
        <div style={{ fontFamily: 'DM Sans', fontSize: 24, fontWeight: 700, lineHeight: 1.2, marginTop: 2 }}>{value}</div>
        {sub && <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>{sub}</div>}
      </div>
    </div>
  )
}

function NewFactureModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [clients, setClients] = useState<any[]>([])
  const [form, setForm] = useState({
    client_id: '', description: '', montant_ht: '', tva_pct: '20',
    date_emission: new Date().toISOString().split('T')[0],
    date_echeance: '', notes: '',
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetch(`${API}/api/clients`).then(r => r.json()).then(setClients)
  }, [])

  const ht  = parseFloat(form.montant_ht) || 0
  const tva = parseFloat(form.tva_pct) || 20
  const ttc = Math.round(ht * (1 + tva / 100) * 100) / 100

  const handleSubmit = async () => {
    if (!form.client_id || !form.montant_ht) return
    setSaving(true)
    try {
      await fetch(`${API}/api/factures`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          client_id: parseInt(form.client_id),
          montant_ht: ht,
          tva_pct: tva,
          date_emission: form.date_emission || null,
          date_echeance: form.date_echeance || null,
          status: 'brouillon',
        }),
      })
      onCreated(); onClose()
    } finally { setSaving(false) }
  }

  const inputStyle = { width: '100%', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '9px 12px', color: 'var(--text)', fontSize: 13, outline: 'none', boxSizing: 'border-box' as const }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="card" style={{ width: 520, maxHeight: '88vh', overflowY: 'auto', padding: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 style={{ fontFamily: 'DM Sans', fontSize: 18, fontWeight: 700, margin: 0 }}>Nouvelle facture</h2>
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
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Description</label>
            <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Ex: Nettoyage bureaux — janvier 2024" rows={2}
              style={{ ...inputStyle, resize: 'vertical' as const }} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Montant HT (€) *</label>
              <input type="number" value={form.montant_ht} onChange={e => setForm(f => ({ ...f, montant_ht: e.target.value }))} placeholder="0.00" style={inputStyle} />
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

          {ht > 0 && (
            <div style={{ background: 'var(--surface)', borderRadius: 10, padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>HT : {ht.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} €</div>
                <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>TVA ({tva}%) : {(ttc - ht).toFixed(2)} €</div>
              </div>
              <div style={{ fontFamily: 'DM Sans', fontSize: 22, fontWeight: 700, color: '#22c55e' }}>
                {ttc.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} € TTC
              </div>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Date d'émission</label>
              <input type="date" value={form.date_emission} onChange={e => setForm(f => ({ ...f, date_emission: e.target.value }))} style={inputStyle} />
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Date d'échéance</label>
              <input type="date" value={form.date_echeance} onChange={e => setForm(f => ({ ...f, date_echeance: e.target.value }))} style={inputStyle} />
            </div>
          </div>

          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Notes internes</label>
            <textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} rows={2} style={{ ...inputStyle, resize: 'vertical' as const }} />
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '9px 18px', borderRadius: 8, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-muted)', fontSize: 13, cursor: 'pointer' }}>Annuler</button>
          <button onClick={handleSubmit} disabled={saving || !form.client_id || !form.montant_ht}
            style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--accent)', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, opacity: (!form.client_id || !form.montant_ht) ? 0.5 : 1 }}>
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Créer la facture
          </button>
        </div>
      </div>
    </div>
  )
}

export default function FacturationPage() {
  const [factures, setFactures] = useState<Facture[]>([])
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
      const [f, s] = await Promise.all([
        fetch(`${API}/api/factures?${params}`).then(r => r.json()),
        fetch(`${API}/api/factures/stats/summary`).then(r => r.json()),
      ])
      setFactures(f); setStats(s)
    } finally { setLoading(false) }
  }, [search, statusFilter])

  useEffect(() => { const t = setTimeout(load, 300); return () => clearTimeout(t) }, [load])

  const changeStatus = async (id: number, status: string) => {
    await fetch(`${API}/api/factures/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) })
    load()
  }

  const inputStyle = { background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '7px 12px', color: 'var(--text)', fontSize: 13, outline: 'none' }

  const isEnRetard = (f: Facture) => f.status === 'envoyee' && f.date_echeance && new Date(f.date_echeance) < new Date()

  return (
    <div style={{ padding: '32px 36px' }}>
      {showModal && <NewFactureModal onClose={() => setShowModal(false)} onCreated={load} />}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontFamily: 'DM Sans', fontSize: 28, fontWeight: 800, margin: 0 }}>Facturation</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 4, fontSize: 14 }}>{factures.length} facture{factures.length > 1 ? 's' : ''}</p>
        </div>
        <button onClick={() => setShowModal(true)} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--accent)', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
          <Plus size={15} /> Nouvelle facture
        </button>
      </div>

      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
          <KpiCard icon={TrendingUp}     label="CA encaissé HT"  value={`${(stats.ca_encaisse ?? 0).toLocaleString('fr-FR')} €`}   color="#22c55e" />
          <KpiCard icon={Clock}          label="En attente"       value={`${(stats.ca_en_attente ?? 0).toLocaleString('fr-FR')} €`}  sub={`${stats.en_attente} facture${stats.en_attente > 1 ? 's' : ''}`} color="#3b82f6" />
          <KpiCard icon={AlertTriangle}  label="En retard"        value={stats.en_retard}   color="#ef4444" />
          <KpiCard icon={Receipt}        label="Total factures"   value={stats.total}        color="#a78bfa" />
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
          <option value="envoyee">Envoyée</option>
          <option value="payee">Payée</option>
          <option value="en_retard">En retard</option>
          <option value="annulee">Annulée</option>
        </select>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60, gap: 10, color: 'var(--text-muted)' }}>
            <Loader2 size={18} className="animate-spin" /> Chargement...
          </div>
        ) : factures.length === 0 ? (
          <div style={{ padding: 64, textAlign: 'center' }}>
            <Receipt size={40} color="var(--text-dim)" style={{ margin: '0 auto 16px' }} />
            <div style={{ fontFamily: 'DM Sans', fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Aucune facture encore</div>
            <div style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 20 }}>Crée ta première facture après un chantier.</div>
            <button onClick={() => setShowModal(true)} style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--accent)', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
              + Créer une facture
            </button>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Numéro', 'Client', 'Description', 'Montant HT', 'TTC', 'Échéance', 'Statut', 'Action'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {factures.map((f, i) => {
                const sc = STATUS_CONFIG[f.status] || STATUS_CONFIG.brouillon
                const retard = isEnRetard(f)
                return (
                  <tr key={f.id} style={{ borderBottom: i < factures.length - 1 ? '1px solid var(--border-soft)' : 'none', background: retard ? '#ef444408' : 'transparent' }}
                    onMouseEnter={e => (e.currentTarget.style.background = retard ? '#ef444412' : 'var(--surface)')}
                    onMouseLeave={e => (e.currentTarget.style.background = retard ? '#ef444408' : 'transparent')}>
                    <td style={{ padding: '14px 16px', fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)' }}>{f.numero}</td>
                    <td style={{ padding: '14px 16px', fontWeight: 600, fontSize: 13 }}>{f.client_name || '—'}</td>
                    <td style={{ padding: '14px 16px', fontSize: 12, color: 'var(--text-muted)', maxWidth: 200 }}>
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.description || '—'}</div>
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 14, fontWeight: 600 }}>{(f.montant_ht ?? 0).toLocaleString('fr-FR')} €</td>
                    <td style={{ padding: '14px 16px', fontSize: 13, color: '#22c55e', fontWeight: 600 }}>{(f.montant_ttc ?? 0).toLocaleString('fr-FR')} €</td>
                    <td style={{ padding: '14px 16px', fontSize: 12, color: retard ? '#ef4444' : 'var(--text-muted)', fontWeight: retard ? 600 : 400 }}>
                      {f.date_echeance ? new Date(f.date_echeance).toLocaleDateString('fr-FR') : '—'}
                      {retard && <div style={{ fontSize: 10, marginTop: 2 }}>⚠️ dépassée</div>}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, background: `${sc.color}18`, color: sc.color, border: `1px solid ${sc.color}30` }}>
                        {sc.label}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <select value={f.status} onChange={e => changeStatus(f.id, e.target.value)}
                          style={{ fontSize: 11, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: '4px 8px', color: 'var(--text-muted)', cursor: 'pointer', outline: 'none' }}>
                          <option value="brouillon">Brouillon</option>
                          <option value="envoyee">Envoyée</option>
                          <option value="payee">Payée</option>
                          <option value="en_retard">En retard</option>
                          <option value="annulee">Annulée</option>
                        </select>
                        <a href={`${API}/api/factures/${f.id}/pdf`} target="_blank" rel="noreferrer" title="Télécharger la facture PDF"
                          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--accent)', textDecoration: 'none', flexShrink: 0 }}>
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