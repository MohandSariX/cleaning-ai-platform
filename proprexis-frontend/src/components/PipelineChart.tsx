'use client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

type ChartData = {
  days: Array<{
    date: string
    new: number
    contacted: number
    replied: number
  }>
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--card)',
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '10px 14px',
      fontSize: 12
    }}>
      <div style={{ fontWeight: 600, marginBottom: 6, color: 'var(--text)' }}>{label}</div>
      {payload.map((entry: any, i: number) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: entry.color }} />
          <span style={{ color: 'var(--text-muted)' }}>{entry.name}:</span>
          <span style={{ fontWeight: 600, color: 'var(--text)' }}>{entry.value}</span>
        </div>
      ))}
    </div>
  )
}

export function PipelineChart({ data }: { data: ChartData }) {
  return (
    <div className="card" style={{ padding: '24px' }}>
      <h3 style={{ fontFamily: 'Syne', fontSize: 16, fontWeight: 700, margin: '0 0 20px' }}>
        📈 Évolution pipeline (7 derniers jours)
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data.days} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            stroke="var(--border)"
          />
          <YAxis
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            stroke="var(--border)"
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: 12, color: 'var(--text-muted)' }}
            iconType="circle"
          />
          <Line
            type="monotone"
            dataKey="new"
            name="Nouveaux"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="contacted"
            name="Contactés"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="replied"
            name="Réponses"
            stroke="#22c55e"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
