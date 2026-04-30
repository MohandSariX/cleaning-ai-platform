'use client'
import { useEffect, useState } from 'react'
import { TrendingUp, FileText, CheckCircle, XCircle, DollarSign, BarChart3, Loader2 } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend
} from 'recharts'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type OverviewStats = {
  period_days: number
  total: number
  envoyes: number
  acceptes: number
  refuses: number
  ca_total: number
  ca_accepte: number
  ca_pipeline: number
  taux_envoi: number
  taux_acceptation: number
  taux_refus: number
  montant_moyen: number
  montant_moyen_accepte: number
}

type TypeAnalytics = {
  service_type: string
  total: number
  envoyes: number
  acceptes: number
  refuses: number
  ca_total: number
  ca_accepte: number
  taux_acceptation: number
  montant_moyen: number
}

type MontantAnalytics = {
  tranche: string
  total: number
  envoyes: number
  acceptes: number
  taux_acceptation: number
}

type EvolutionData = {
  date: string
  created: number
  envoyes: number
  acceptes: number
  ca: number
}

type TopClient = {
  client_id: number
  company_name: string
  devis_count: number
  ca_total: number
}

function StatCard({ icon: Icon, label, value, subvalue, color }: {
  icon: React.ElementType
  label: string
  value: string | number
  subvalue?: string
  color: string
}) {
  return (
    <div className="card" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <div style={{
          width: 48,
          height: 48,
          borderRadius: 10,
          background: `${color}15`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Icon size={24} color={color} strokeWidth={2} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: 11,
            color: 'var(--text-muted)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: 6
          }}>
            {label}
          </div>
          <div style={{
            fontFamily: 'DM Sans',
            fontSize: 28,
            fontWeight: 700,
            color: 'var(--text)',
            letterSpacing: '-0.5px',
            lineHeight: 1
          }}>
            {value}
          </div>
          {subvalue && (
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              {subvalue}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function DevisAnalyticsPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null)
  const [byType, setByType] = useState<TypeAnalytics[]>([])
  const [byMontant, setByMontant] = useState<MontantAnalytics[]>([])
  const [evolution, setEvolution] = useState<EvolutionData[]>([])
  const [topClients, setTopClients] = useState<TopClient[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState(30)

  const loadData = async () => {
    setLoading(true)
    try {
      const [overviewRes, typeRes, montantRes, evolutionRes, clientsRes] = await Promise.all([
        fetch(`${API}/api/devis/analytics/overview?days=${period}`),
        fetch(`${API}/api/devis/analytics/by-type?days=90`),
        fetch(`${API}/api/devis/analytics/by-montant?days=90`),
        fetch(`${API}/api/devis/analytics/evolution?days=${period}`),
        fetch(`${API}/api/devis/analytics/top-clients?limit=10`),
      ])

      setOverview(await overviewRes.json())
      setByType(await typeRes.json())
      setByMontant(await montantRes.json())
      setEvolution(await evolutionRes.json())
      setTopClients(await clientsRes.json())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [period])

  if (loading) {
    return (
      <div style={{ padding: '32px 36px', display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)' }}>
        <Loader2 size={18} className="animate-spin" /> Chargement analytics...
      </div>
    )
  }

  if (!overview) return null

  const COLORS = ['#3b82f6', '#22c55e', '#f97316', '#8b5cf6', '#eab308']

  return (
    <div style={{ padding: '32px 36px', maxWidth: 1400 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Analytics Devis</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 6, fontSize: 13 }}>
            Analyse détaillée des performances devis
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {[7, 30, 90].map(days => (
            <button
              key={days}
              onClick={() => setPeriod(days)}
              style={{
                padding: '8px 16px',
                borderRadius: 8,
                border: 'none',
                background: period === days ? '#f5a623' : 'var(--surface)',
                color: period === days ? '#fff' : 'var(--text)',
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {days}j
            </button>
          ))}
        </div>
      </div>

      {/* Stats Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20, marginBottom: 28 }}>
        <StatCard
          icon={FileText}
          label="Total devis"
          value={overview.total}
          subvalue={`${overview.envoyes} envoyés`}
          color="#3b82f6"
        />
        <StatCard
          icon={CheckCircle}
          label="Taux acceptation"
          value={`${overview.taux_acceptation}%`}
          subvalue={`${overview.acceptes} acceptés`}
          color="#22c55e"
        />
        <StatCard
          icon={DollarSign}
          label="CA signé"
          value={`${overview.ca_accepte.toLocaleString('fr-FR')} €`}
          subvalue={`${overview.ca_pipeline.toLocaleString('fr-FR')} € pipeline`}
          color="#f5a623"
        />
        <StatCard
          icon={TrendingUp}
          label="Montant moyen"
          value={`${overview.montant_moyen.toLocaleString('fr-FR')} €`}
          subvalue={`${overview.montant_moyen_accepte.toLocaleString('fr-FR')} € accepté`}
          color="#8b5cf6"
        />
      </div>

      {/* Évolution temporelle */}
      <div className="card" style={{ padding: '24px', marginBottom: 28 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20 }}>
          Évolution sur {period} jours
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={evolution}>
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              tickFormatter={(value) => new Date(value).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })}
            />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: 'var(--card)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                fontSize: 12
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="created" stroke="#3b82f6" name="Créés" strokeWidth={2} />
            <Line type="monotone" dataKey="envoyes" stroke="#f97316" name="Envoyés" strokeWidth={2} />
            <Line type="monotone" dataKey="acceptes" stroke="#22c55e" name="Acceptés" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 28 }}>
        {/* Par type de prestation */}
        <div className="card" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20 }}>
            Par type de prestation
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={byType}>
              <XAxis dataKey="service_type" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: 'var(--card)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  fontSize: 12
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="acceptes" fill="#22c55e" name="Acceptés" />
              <Bar dataKey="refuses" fill="#ef4444" name="Refusés" />
              <Bar dataKey="envoyes" fill="#3b82f6" name="Envoyés" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Par tranche de montant */}
        <div className="card" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20 }}>
            Taux acceptation par montant
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={byMontant}>
              <XAxis dataKey="tranche" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: 'var(--card)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  fontSize: 12
                }}
                formatter={(value: number) => `${value}%`}
              />
              <Bar dataKey="taux_acceptation" fill="#f5a623" name="Taux acceptation (%)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Clients */}
      <div className="card" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20 }}>
          Top 10 Clients (CA devis signés)
        </h2>
        {topClients.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: 13 }}>
            Aucun devis signé pour le moment
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {topClients.map((client, i) => (
              <div
                key={client.client_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '14px 16px',
                  background: 'var(--surface)',
                  borderRadius: 8
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: 6,
                    background: COLORS[i % COLORS.length] + '20',
                    color: COLORS[i % COLORS.length],
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 14,
                    fontWeight: 700
                  }}>
                    {i + 1}
                  </div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>
                      {client.company_name}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {client.devis_count} devis
                    </div>
                  </div>
                </div>
                <div style={{
                  fontFamily: 'DM Sans',
                  fontSize: 18,
                  fontWeight: 700,
                  color: COLORS[i % COLORS.length],
                  letterSpacing: '-0.5px'
                }}>
                  {client.ca_total.toLocaleString('fr-FR')} €
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
