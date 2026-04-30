'use client'
import { useEffect, useState } from 'react'
import {
  Save, RefreshCw, Loader2, Building2, Euro,
  ChevronDown, ChevronUp, CheckCircle, AlertCircle, Monitor, Zap
} from 'lucide-react'
import { ThemeToggle } from '@/components/ThemeToggle'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Societe = {
  nom: string; forme_juridique: string; gerant: string
  email: string; telephone: string; adresse: string
  siret: string; numero_tva: string; iban: string; bic: string
}

type Tarif = {
  id: number; name: string; description: string
  unit: string; unit_price_ht: number; minimum_ht: number | null
  category: string; active: boolean
}

type AutonomyConfig = {
  devis_auto_threshold_ht: number
  discount_auto_max_pct: number
  chantier_auto_planning: boolean
  chantier_notification_client: boolean
  planning_conflict_escalate: boolean
}

function Section({ title, icon: Icon, children, defaultOpen = true }: {
  title: string; icon: React.ElementType; children: React.ReactNode; defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div onClick={() => setOpen(o => !o)} style={{
        padding: '16px 24px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', cursor: 'pointer'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: '#3b82f618', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon size={14} color="#3b82f6" />
          </div>
          <span style={{ fontWeight: 700, fontSize: 14 }}>{title}</span>
        </div>
        {open ? <ChevronUp size={15} color="var(--text-muted)" /> : <ChevronDown size={15} color="var(--text-muted)" />}
      </div>
      {open && <div style={{ padding: '0 24px 24px', borderTop: '1px solid var(--border)' }}>{children}</div>}
    </div>
  )
}

function Field({ label, value, onChange, placeholder, mono = false }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; mono?: boolean
}) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </label>
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          width: '100%', padding: '9px 12px', borderRadius: 7,
          border: '1px solid var(--border)', background: 'var(--surface)',
          color: 'var(--text)', fontSize: mono ? 13 : 14,
          fontFamily: mono ? 'monospace' : 'inherit', boxSizing: 'border-box'
        }}
      />
    </div>
  )
}

export default function ParametresPage() {
  const [societe, setSociete] = useState<Societe | null>(null)
  const [tarifs, setTarifs] = useState<Tarif[]>([])
  const [autonomyConfig, setAutonomyConfig] = useState<AutonomyConfig | null>(null)
  const [savingSociete, setSavingSociete] = useState(false)
  const [savingTarif, setSavingTarif] = useState<number | null>(null)
  const [savingAutonomy, setSavingAutonomy] = useState(false)
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null)
  const [editedTarifs, setEditedTarifs] = useState<Record<number, Partial<Tarif>>>({})
  const [simulResult, setSimulResult] = useState<any>(null)
  const [simul, setSimul] = useState({ type: 'bureaux', superficie: '200', frequence: 'hebdo' })

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok })
    setTimeout(() => setToast(null), 3000)
  }

  const load = async () => {
    const [societeRes, productsRes, autonomyRes] = await Promise.all([
      fetch(`${API}/api/tenants/owner/config`),
      fetch(`${API}/api/products`),
      fetch(`${API}/api/escalations/config/autonomy`),
    ])
    const societeData = await societeRes.json()
    const productsData = await productsRes.json()
    const autonomyData = await autonomyRes.json()
    setSociete(societeData)
    setTarifs(productsData)
    setAutonomyConfig(autonomyData)
  }

  useEffect(() => { load() }, [])

  const saveSociete = async () => {
    if (!societe) return
    setSavingSociete(true)
    try {
      const res = await fetch(`${API}/api/tenants/owner/config`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(societe),
      })
      if (res.ok) showToast('Infos société sauvegardées ✓')
      else showToast('Erreur lors de la sauvegarde', false)
    } catch { showToast('Erreur réseau', false) }
    setSavingSociete(false)
  }

  const saveTarif = async (productId: number) => {
    const edit = editedTarifs[productId]
    if (!edit) return
    setSavingTarif(productId)
    try {
      const res = await fetch(`${API}/api/products/${productId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(edit),
      })
      if (res.ok) {
        showToast('Tarif mis à jour ✓')
        const updated = { ...editedTarifs }
        delete updated[productId]
        setEditedTarifs(updated)
        await load()
      }
    } catch { showToast('Erreur', false) }
    setSavingTarif(null)
  }

  const saveAutonomy = async () => {
    if (!autonomyConfig) return
    setSavingAutonomy(true)
    try {
      const res = await fetch(`${API}/api/escalations/config/autonomy`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(autonomyConfig),
      })
      if (res.ok) showToast('Config autonomie sauvegardée ✓')
      else showToast('Erreur lors de la sauvegarde', false)
    } catch { showToast('Erreur réseau', false) }
    setSavingAutonomy(false)
  }

  const simulate = async () => {
    const res = await fetch(`${API}/api/devis-rules/simulate?type_prestation=${simul.type}&superficie_m2=${simul.superficie}&frequence=${simul.frequence}`, { method: 'POST' })
    setSimulResult(await res.json())
  }

  if (!societe) return (
    <div style={{ padding: '32px 36px', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)' }}>
      <Loader2 size={16} className="animate-spin" /> Chargement...
    </div>
  )

  return (
    <div style={{ padding: '32px 36px', maxWidth: 800 }}>
      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', top: 24, right: 24, zIndex: 100,
          padding: '10px 16px', borderRadius: 8,
          background: toast.ok ? '#22c55e' : '#ef4444',
          color: 'white', fontSize: 13, fontWeight: 600,
          display: 'flex', alignItems: 'center', gap: 8,
          boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
        }}>
          {toast.ok ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
          {toast.msg}
        </div>
      )}

      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Paramètres</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 6, fontSize: 13 }}>
          Infos société, tarifs et configuration des devis
        </p>
      </div>

      {/* Infos société */}
      <Section title="Informations société" icon={Building2}>
        <div style={{ paddingTop: 20, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 20px' }}>
          <Field label="Nom" value={societe.nom} onChange={v => setSociete(s => s && ({ ...s, nom: v }))} />
          <Field label="Forme juridique" value={societe.forme_juridique} onChange={v => setSociete(s => s && ({ ...s, forme_juridique: v }))} />
          <Field label="Gérant" value={societe.gerant} onChange={v => setSociete(s => s && ({ ...s, gerant: v }))} />
          <Field label="Email" value={societe.email} onChange={v => setSociete(s => s && ({ ...s, email: v }))} placeholder="contact@proprexis.fr" />
          <Field label="Téléphone" value={societe.telephone} onChange={v => setSociete(s => s && ({ ...s, telephone: v }))} placeholder="06 XX XX XX XX" />
          <Field label="Adresse" value={societe.adresse} onChange={v => setSociete(s => s && ({ ...s, adresse: v }))} />
          <Field label="SIRET" value={societe.siret} onChange={v => setSociete(s => s && ({ ...s, siret: v }))} mono />
          <Field label="N° TVA intracommunautaire" value={societe.numero_tva} onChange={v => setSociete(s => s && ({ ...s, numero_tva: v }))} mono />
          <Field label="IBAN" value={societe.iban} onChange={v => setSociete(s => s && ({ ...s, iban: v }))} mono />
          <Field label="BIC" value={societe.bic} onChange={v => setSociete(s => s && ({ ...s, bic: v }))} mono />
        </div>
        <button onClick={saveSociete} disabled={savingSociete} style={{
          display: 'flex', alignItems: 'center', gap: 6, padding: '9px 18px',
          borderRadius: 8, border: 'none', background: '#3b82f6', color: 'white',
          fontSize: 13, fontWeight: 600, cursor: 'pointer'
        }}>
          {savingSociete ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
          Sauvegarder
        </button>
      </Section>

      {/* Apparence */}
      <Section title="Apparence" icon={Monitor} defaultOpen={true}>
        <div style={{ paddingTop: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text)', marginBottom: 4 }}>Thème de l'interface</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Basculer entre le mode nuit et le mode jour</div>
          </div>
          <ThemeToggle />
        </div>
      </Section>

      {/* Autonomie Claude */}
      {autonomyConfig && (
        <Section title="Autonomie Claude" icon={Zap} defaultOpen={false}>
          <div style={{ paddingTop: 20 }}>
            <div style={{ marginBottom: 24, padding: '12px 16px', borderRadius: 8, background: 'var(--surface)', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 13, color: 'var(--text)', marginBottom: 4, fontWeight: 600 }}>
                Seuils de décision automatique
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Définit quand Claude peut agir seul ou doit escalader pour validation
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 20px' }}>
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Seuil devis auto (€ HT)
                </label>
                <input
                  type="number"
                  value={autonomyConfig.devis_auto_threshold_ht}
                  onChange={e => setAutonomyConfig(c => c && ({ ...c, devis_auto_threshold_ht: parseFloat(e.target.value) }))}
                  style={{
                    width: '100%', padding: '9px 12px', borderRadius: 7,
                    border: '1px solid var(--border)', background: 'var(--surface)',
                    color: 'var(--text)', fontSize: 14, boxSizing: 'border-box'
                  }}
                />
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  Devis &lt; ce montant → création auto chantier
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Remise max auto (%)
                </label>
                <input
                  type="number"
                  value={autonomyConfig.discount_auto_max_pct}
                  onChange={e => setAutonomyConfig(c => c && ({ ...c, discount_auto_max_pct: parseFloat(e.target.value) }))}
                  style={{
                    width: '100%', padding: '9px 12px', borderRadius: 7,
                    border: '1px solid var(--border)', background: 'var(--surface)',
                    color: 'var(--text)', fontSize: 14, boxSizing: 'border-box'
                  }}
                />
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  Remise &lt; ce % → négociation auto
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={autonomyConfig.chantier_auto_planning}
                  onChange={e => setAutonomyConfig(c => c && ({ ...c, chantier_auto_planning: e.target.checked }))}
                  style={{ width: 16, height: 16, cursor: 'pointer' }}
                />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>Planification automatique chantiers</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Claude planifie les dates et horaires automatiquement</div>
                </div>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={autonomyConfig.chantier_notification_client}
                  onChange={e => setAutonomyConfig(c => c && ({ ...c, chantier_notification_client: e.target.checked }))}
                  style={{ width: 16, height: 16, cursor: 'pointer' }}
                />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>Notifications clients automatiques</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Envoyer email de confirmation au client</div>
                </div>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={autonomyConfig.planning_conflict_escalate}
                  onChange={e => setAutonomyConfig(c => c && ({ ...c, planning_conflict_escalate: e.target.checked }))}
                  style={{ width: 16, height: 16, cursor: 'pointer' }}
                />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>Escalader conflits planning</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Demander validation si chevauchement détecté</div>
                </div>
              </label>
            </div>

            <button onClick={saveAutonomy} disabled={savingAutonomy} style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '9px 18px',
              borderRadius: 8, border: 'none', background: '#f5a623', color: 'white',
              fontSize: 13, fontWeight: 600, cursor: 'pointer', marginTop: 20
            }}>
              {savingAutonomy ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
              Sauvegarder config autonomie
            </button>
          </div>
        </Section>
      )}

      {/* Tarifs */}
      <Section title="Grille tarifaire" icon={Euro}>
        <div style={{ paddingTop: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px 10px', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', padding: '0 0 8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <span>Prestation</span><span>Tarif</span><span>Min HT</span>
          </div>
          {tarifs.map(tarif => {
            const edit = editedTarifs[tarif.id] || {}
            const modified = !!editedTarifs[tarif.id]
            const isHourly = tarif.unit === 'heure'
            const unitLabel = isHourly ? '€/h' : '€/' + tarif.unit
            return (
              <div key={tarif.id} style={{
                display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0 10px',
                alignItems: 'center', padding: '10px 0',
                borderBottom: '1px solid var(--border)',
              }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>{tarif.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>{tarif.description}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <input
                    type="number"
                    step="0.5"
                    value={edit.unit_price_ht ?? tarif.unit_price_ht ?? ''}
                    onChange={e => {
                      const val = parseFloat(e.target.value)
                      setEditedTarifs(prev => ({
                        ...prev,
                        [tarif.id]: {
                          ...prev[tarif.id],
                          unit_price_ht: val
                        }
                      }))
                    }}
                    style={{ width: 70, padding: '6px 8px', borderRadius: 6, border: `1px solid ${modified ? '#3b82f6' : 'var(--border)'}`, background: 'var(--surface)', color: 'var(--text)', fontSize: 13 }}
                  />
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{unitLabel}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <input
                    type="number"
                    value={edit.minimum_ht ?? tarif.minimum_ht ?? ''}
                    onChange={e => setEditedTarifs(prev => ({ ...prev, [tarif.id]: { ...prev[tarif.id], minimum_ht: parseFloat(e.target.value) } }))}
                    style={{ width: 70, padding: '6px 8px', borderRadius: 6, border: `1px solid ${modified ? '#3b82f6' : 'var(--border)'}`, background: 'var(--surface)', color: 'var(--text)', fontSize: 13 }}
                  />
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>€</span>
                  {modified && (
                    <button onClick={() => saveTarif(tarif.id)} disabled={savingTarif === tarif.id} style={{
                      padding: '5px 10px', borderRadius: 6, border: 'none', background: '#3b82f6',
                      color: 'white', fontSize: 11, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4
                    }}>
                      {savingTarif === tarif.id ? <Loader2 size={10} className="animate-spin" /> : <Save size={10} />}
                      Sauver
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Simulateur */}
        <div style={{ marginTop: 20, padding: 16, borderRadius: 8, background: 'var(--surface)', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Simulateur de devis
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <select value={simul.type} onChange={e => setSimul(s => ({ ...s, type: e.target.value }))} style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)', fontSize: 12 }}>
              <option value="bureaux">Bureaux</option>
              <option value="fin_chantier">Fin de chantier</option>
              <option value="copropriete">Copropriété</option>
              <option value="vitrerie">Vitrerie</option>
            </select>
            <input type="number" value={simul.superficie} onChange={e => setSimul(s => ({ ...s, superficie: e.target.value }))} placeholder="m²" style={{ width: 80, padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)', fontSize: 12 }} />
            <select value={simul.frequence} onChange={e => setSimul(s => ({ ...s, frequence: e.target.value }))} style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)', fontSize: 12 }}>
              <option value="ponctuel">Ponctuel</option>
              <option value="hebdo">Hebdo</option>
              <option value="mensuel">Mensuel</option>
              <option value="trimestriel">Trimestriel</option>
              <option value="annuel">Annuel</option>
            </select>
            <button onClick={simulate} style={{ padding: '7px 14px', borderRadius: 6, border: 'none', background: '#3b82f6', color: 'white', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
              Calculer
            </button>
            {simulResult && (
              <div style={{ padding: '7px 14px', borderRadius: 6, background: '#22c55e10', border: '1px solid #22c55e30', fontSize: 12 }}>
                <strong style={{ color: '#22c55e' }}>{simulResult.montant_ttc?.toLocaleString('fr-FR')} € TTC</strong>
                <span style={{ color: 'var(--text-muted)', marginLeft: 6 }}>({simulResult.montant_ht?.toLocaleString('fr-FR')} € HT · {simulResult.duree_estimee_heures}h estimées)</span>
              </div>
            )}
          </div>
        </div>
      </Section>
    </div>
  )
}