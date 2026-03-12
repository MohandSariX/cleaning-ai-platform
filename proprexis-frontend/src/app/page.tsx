'use client'
import { useEffect, useState } from 'react'
import { fetchStats } from '@/lib/api'
import {
  Users, Mail, Globe, Phone,
  TrendingUp, Star, AlertCircle, Loader2
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts'

type Stats = {
  total: number
  with_email: number
  with_phone: number
  with_web: number
  email_rate: number
  avg_score: number
  score_distribution: { haute: number; moyenne: number; faible: number; nulle: number }
  by_city: { city: string; count: number }[]
}

const SCORE_COLORS = {
  haute:   '#22c55e',
  moyenne: '#eab308',
  faible:  '#f97316',
  nulle:   '#475569',
}

const SCORE_LABELS = {
  haute:   '🔥 Priorité haute',
  moyenne: '⚡ Priorité moyenne',
  faible:  '🌱 Priorité faible',
  nulle:   '❄️ Non prioritaire',
}

function KpiCard({ icon: Icon, label, value, sub, color }: {
  icon: React.ElementType
  label: string
  value: string | number
  sub?: string
  color?: string
}) {
  return (
    <div className="card" style={{ padding: '20px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8, fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            {label}
          </div>
          <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 32, fontWeight: 700, color: 'var(--text)', lineHeight: 1 }}>
            {value}
          </div>
          {sub && (
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>{sub}</div>
          )}
        </div>
        <div style={{
          width: 40, height: 40, borderRadius: 10,
          background: color ? `${color}18` : 'var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={18} color={color || 'var(--text-muted)'} strokeWidth={1.8} />
        </div>
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
      <div style={{ color: 'var(--text)', fontWeight: 600 }}>{payload[0].value} prospects</div>
    </div>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch(() => setError('Impossible de joindre l\'API. Vérifiez que FastAPI tourne sur le port 8000.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 12, color: 'var(--text-muted)' }}>
      <Loader2 size={20} className="animate-spin" />
      Chargement...
    </div>
  )

  if (error) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      <div className="card" style={{ padding: 32, maxWidth: 400, textAlign: 'center' }}>
        <AlertCircle size={32} color="var(--red)" style={{ margin: '0 auto 16px' }} />
        <div style={{ fontFamily: 'Syne', fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Connexion impossible</div>
        <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{error}</div>
        <code style={{ display: 'block', marginTop: 16, padding: '8px 12px', background: 'var(--surface)', borderRadius: 6, fontSize: 12, color: 'var(--accent)' }}>
          uvicorn main:app --reload
        </code>
      </div>
    </div>
  )

  if (!stats) return null

  const pieData = Object.entries(stats.score_distribution).map(([key, val]) => ({
    name: SCORE_LABELS[key as keyof typeof SCORE_LABELS],
    value: val,
    color: SCORE_COLORS[key as keyof typeof SCORE_COLORS],
  })).filter(d => d.value > 0)

  const topCities = stats.by_city.slice(0, 8)

  return (
    <div style={{ padding: '32px 36px', maxWidth: 1200 }}>

      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: 'Syne', fontSize: 28, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' }}>
          Dashboard
        </h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 4, fontSize: 14 }}>
          Vue d'ensemble de ta pipeline commerciale
        </p>
      </div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        <KpiCard icon={Users}     label="Total Prospects" value={stats.total}          color="#3b82f6" />
        <KpiCard icon={Mail}      label="Avec Email"       value={stats.with_email}     sub={`${stats.email_rate}% du total`} color="#22c55e" />
        <KpiCard icon={Phone}     label="Avec Téléphone"   value={stats.with_phone}     color="#a78bfa" />
        <KpiCard icon={TrendingUp} label="Score Moyen"     value={`${stats.avg_score}/100`} color="#f97316" />
      </div>

      {/* Deuxième ligne KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
        <KpiCard icon={Star}  label="🔥 Priorité haute"   value={stats.score_distribution.haute}   color="#22c55e" />
        <KpiCard icon={Star}  label="⚡ Priorité moyenne"  value={stats.score_distribution.moyenne} color="#eab308" />
        <KpiCard icon={Star}  label="🌱 Priorité faible"   value={stats.score_distribution.faible}  color="#f97316" />
        <KpiCard icon={Globe} label="Avec Site Web"        value={stats.with_web}                   color="#06b6d4" />
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

        {/* Bar chart villes */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 15, fontWeight: 700, margin: '0 0 20px', color: 'var(--text)' }}>
            Prospects par ville
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={topCities} margin={{ top: 0, right: 0, bottom: 20, left: -20 }}>
              <XAxis
                dataKey="city"
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                angle={-35}
                textAnchor="end"
                interval={0}
              />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {topCities.map((_, i) => (
                  <Cell key={i} fill={i === 0 ? '#3b82f6' : '#1e3a5f'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie chart scores */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 15, fontWeight: 700, margin: '0 0 20px', color: 'var(--text)' }}>
            Distribution des scores
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
            <ResponsiveContainer width={180} height={180}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
              {pieData.map((entry, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 2, background: entry.color, flexShrink: 0 }} />
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', flex: 1 }}>{entry.name}</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{entry.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
