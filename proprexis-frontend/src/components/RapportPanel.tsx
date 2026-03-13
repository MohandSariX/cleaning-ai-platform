'use client'
import { useEffect, useState } from 'react'
import {
  AlertTriangle, RefreshCw, Loader2, ChevronRight,
  Clock, Star, Calendar, TrendingUp
} from 'lucide-react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Rapport = {
  last_update: string | null
  factures_retard: Array<{ id: number; numero: string; client_nom: string; montant_ttc: number; jours_retard: number; date_echeance: string }>
  prospects_relancer: Array<{ id: number; company_name: string; city: string; lead_score: number; score_label: string; jours_depuis_contact: number }>
  chantiers_aujourd_hui: Array<{ id: number; titre: string; client_nom: string; adresse: string; heure_debut: string; duree_heures: number; type: string }>
  nouveaux_prospects: Array<{ id: number; company_name: string; city: string; lead_score: number; score_label: string; industry: string }>
  stats: {
    factures_retard_count: number
    factures_retard_montant: number
    prospects_relancer_count: number
    chantiers_aujourd_hui_count: number
    nouveaux_prospects_count: number
  }
}

function Badge({ count, color }: { count: number; color: string }) {
  if (count === 0) return null
  return (
    <span style={{ minWidth: 20, height: 20, borderRadius: 10, background: color, color: 'white', fontSize: 11, fontWeight: 700, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: '0 6px' }}>
      {count}
    </span>
  )
}

export function RapportPanel() {
  const [rapport, setRapport] = useState<Rapport | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [tab, setTab] = useState<'factures' | 'relances' | 'chantiers' | 'nouveaux'>('factures')

  const fetchRapport = async () => {
    try {
      const res = await fetch(`${API}/api/watchdog/rapport`)
      setRapport(await res.json())
    } catch {}
    setLoading(false)
  }

  const refresh = async () => {
    setRefreshing(true)
    await fetch(`${API}/api/watchdog/refresh`, { method: 'POST' })
    setTimeout(async () => {
      await fetchRapport()
      setRefreshing(false)
    }, 2000)
  }

  useEffect(() => { fetchRapport() }, [])

  if (loading) return null
  if (!rapport) return null

  const { stats } = rapport
  const totalAlertes = stats.factures_retard_count + stats.prospects_relancer_count

  const tabs = [
    { key: 'factures',  label: 'Factures en retard',    count: stats.factures_retard_count,      color: '#ef4444', icon: AlertTriangle },
    { key: 'relances',  label: 'À relancer',             count: stats.prospects_relancer_count,   color: '#f97316', icon: Clock },
    { key: 'chantiers', label: "Chantiers aujourd'hui",  count: stats.chantiers_aujourd_hui_count, color: '#3b82f6', icon: Calendar },
    { key: 'nouveaux',  label: 'Nouveaux prospects',     count: stats.nouveaux_prospects_count,   color: '#22c55e', icon: Star },
  ] as const

  return (
    <div className="card" style={{ marginBottom: 28 }}>
      {/* Header */}
      <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: totalAlertes > 0 ? '#ef444418' : '#22c55e18', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <TrendingUp size={15} color={totalAlertes > 0 ? '#ef4444' : '#22c55e'} />
          </div>
          <div>
            <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: 14 }}>
              Rapport du jour
              {totalAlertes > 0 && (
                <span style={{ marginLeft: 8, padding: '2px 8px', borderRadius: 10, background: '#ef444418', color: '#ef4444', fontSize: 11, fontWeight: 700 }}>
                  {totalAlertes} action{totalAlertes > 1 ? 's' : ''} requise{totalAlertes > 1 ? 's' : ''}
                </span>
              )}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>
              {rapport.last_update
                ? `Mis à jour ${new Date(rapport.last_update).toLocaleString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`
                : 'Jamais calculé'}
            </div>
          </div>
        </div>
        <button onClick={refresh} disabled={refreshing} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '6px 12px', borderRadius: 7, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer' }}>
          {refreshing ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
          Actualiser
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
        {tabs.map(t => {
          const Icon = t.icon
          const active = tab === t.key
          return (
            <button key={t.key} onClick={() => setTab(t.key as any)} style={{
              flex: 1, padding: '12px 8px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              border: 'none', background: 'none', cursor: 'pointer',
              borderBottom: active ? `2px solid ${t.color}` : '2px solid transparent',
              color: active ? t.color : 'var(--text-muted)',
              fontSize: 12, fontWeight: active ? 600 : 400,
            }}>
              <Icon size={13} />
              <span style={{ display: 'none' }}>{t.label}</span>
              <Badge count={t.count} color={t.color} />
            </button>
          )
        })}
      </div>

      {/* Contenu */}
      <div style={{ padding: '16px 24px', minHeight: 120 }}>

        {/* Factures en retard */}
        {tab === 'factures' && (
          rapport.factures_retard.length === 0
            ? <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>✅ Aucune facture en retard</div>
            : <>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>
                  Total en attente : <strong style={{ color: '#ef4444' }}>{stats.factures_retard_montant.toLocaleString('fr-FR')} € TTC</strong>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {rapport.factures_retard.map(f => (
                    <Link key={f.id} href="/facturation" style={{ textDecoration: 'none' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderRadius: 8, background: '#ef444408', border: '1px solid #ef444420', cursor: 'pointer' }}>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{f.client_nom}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{f.numero} · Échéance {f.date_echeance}</div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: 13, fontWeight: 700, color: '#ef4444' }}>{f.montant_ttc.toLocaleString('fr-FR')} €</div>
                            <div style={{ fontSize: 11, color: '#ef4444' }}>+{f.jours_retard}j de retard</div>
                          </div>
                          <ChevronRight size={14} color="var(--text-muted)" />
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </>
        )}

        {/* Prospects à relancer */}
        {tab === 'relances' && (
          rapport.prospects_relancer.length === 0
            ? <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>✅ Aucun prospect à relancer</div>
            : <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {rapport.prospects_relancer.map(p => (
                  <Link key={p.id} href={`/prospects/${p.id}`} style={{ textDecoration: 'none' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderRadius: 8, background: '#f9741608', border: '1px solid #f9741620' }}>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{p.company_name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{p.city} · Contacté il y a {p.jours_depuis_contact}j</div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: '#f97316' }}>{p.lead_score}/100</span>
                        <ChevronRight size={14} color="var(--text-muted)" />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
        )}

        {/* Chantiers du jour */}
        {tab === 'chantiers' && (
          rapport.chantiers_aujourd_hui.length === 0
            ? <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>Aucun chantier planifié aujourd'hui</div>
            : <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {rapport.chantiers_aujourd_hui.map(c => (
                  <Link key={c.id} href="/chantiers" style={{ textDecoration: 'none' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderRadius: 8, background: '#3b82f608', border: '1px solid #3b82f620' }}>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{c.titre}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{c.client_nom} · {c.adresse}</div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: 12, fontWeight: 600, color: '#3b82f6' }}>{c.heure_debut || '—'}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{c.duree_heures ? `${c.duree_heures}h` : ''}</div>
                        </div>
                        <ChevronRight size={14} color="var(--text-muted)" />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
        )}

        {/* Nouveaux prospects */}
        {tab === 'nouveaux' && (
          rapport.nouveaux_prospects.length === 0
            ? <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>Aucun nouveau prospect haute priorité cette nuit</div>
            : <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {rapport.nouveaux_prospects.map(p => (
                  <Link key={p.id} href={`/prospects/${p.id}`} style={{ textDecoration: 'none' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderRadius: 8, background: '#22c55e08', border: '1px solid #22c55e20' }}>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{p.company_name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{p.city} · {p.industry}</div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: '#22c55e' }}>{p.lead_score}/100</span>
                        <ChevronRight size={14} color="var(--text-muted)" />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
        )}
      </div>
    </div>
  )
}