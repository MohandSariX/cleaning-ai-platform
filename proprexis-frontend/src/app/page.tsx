'use client'
import { useEffect, useRef, useState } from 'react'
import { fetchStats } from '@/lib/api'
import {
  Users, Mail, Globe, Phone, TrendingUp, Star,
  AlertCircle, Loader2, Search, Plus, X, Play, Square, ChevronDown
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts'

import { SchedulerPanel } from '@/components/SchedulerPanel'
import { RapportPanel } from '@/components/RapportPanel'


const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Stats = {
  total: number; with_email: number; with_phone: number; with_web: number
  email_rate: number; avg_score: number
  score_distribution: { haute: number; moyenne: number; faible: number; nulle: number }
  by_city: { city: string; count: number }[]
}

type ScrapeStatus = { running: boolean; log: string[]; done: number; total: number }

const SCORE_COLORS = { haute: '#22c55e', moyenne: '#eab308', faible: '#f97316', nulle: '#475569' }
const SCORE_LABELS = { haute: '🔥 Priorité haute', moyenne: '⚡ Priorité moyenne', faible: '🌱 Priorité faible', nulle: '❄️ Non prioritaire' }

const QUERY_PRESETS = [
  { label: 'Nettoyage', value: 'nettoyage' },
  { label: 'BTP / Construction', value: 'construction btp' },
  { label: 'Promoteur immobilier', value: 'promoteur immobilier' },
  { label: 'Agence immobilière', value: 'agence immobiliere' },
  { label: 'Syndic copropriété', value: 'syndic copropriete' },
  { label: 'Architecte', value: 'architecte' },
  { label: 'Rénovation', value: 'renovation travaux' },
  { label: 'Hôtel', value: 'hotel' },
  { label: 'Restaurant', value: 'restaurant' },
]

function KpiCard({ icon: Icon, label, value, sub, color }: {
  icon: React.ElementType; label: string; value: string | number; sub?: string; color?: string
}) {
  return (
    <div className="card" style={{ padding: '20px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8, fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>{label}</div>
          <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 32, fontWeight: 700, color: 'var(--text)', lineHeight: 1 }}>{value}</div>
          {sub && <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>{sub}</div>}
        </div>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: color ? `${color}18` : 'var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
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

// ── Panneau Scraping ──────────────────────────────────────────────────────────
function ScrapePanel({ onDone }: { onDone: () => void }) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('nettoyage')
  const [customQuery, setCustomQuery] = useState('')
  const [useCustom, setUseCustom] = useState(false)
  const [cities, setCities] = useState<string[]>(['Paris'])
  const [cityInput, setCityInput] = useState('')
  const [maxPages, setMaxPages] = useState(2)
  const [runScoring, setRunScoring] = useState(true)
  const [status, setStatus] = useState<ScrapeStatus>({ running: false, log: [], done: 0, total: 0 })
  const logRef = useRef<HTMLDivElement>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  const addCity = () => {
    const v = cityInput.trim()
    if (v && !cities.includes(v)) setCities(prev => [...prev, v])
    setCityInput('')
  }

  const removeCity = (c: string) => setCities(prev => prev.filter(x => x !== c))

  const startPoll = () => {
    pollRef.current = setInterval(async () => {
      const res = await fetch(`${API}/api/scrape/status`)
      const data: ScrapeStatus = await res.json()
      setStatus(data)
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
      if (!data.running) {
        clearInterval(pollRef.current!)
        onDone()
      }
    }, 1500)
  }

  const handleStart = async () => {
    const finalQuery = useCustom ? customQuery : query
    if (!finalQuery.trim() || cities.length === 0) return
    await fetch(`${API}/api/scrape/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: finalQuery, locations: cities, max_pages: maxPages, run_scoring: runScoring }),
    })
    setStatus({ running: true, log: [], done: 0, total: 0 })
    startPoll()
  }

  const handleStop = async () => {
    await fetch(`${API}/api/scrape/stop`, { method: 'POST' })
    clearInterval(pollRef.current!)
  }

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  return (
    <div className="card" style={{ marginBottom: 28, overflow: 'hidden' }}>
      {/* Header cliquable */}
      <button onClick={() => setOpen(o => !o)} style={{
        width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '18px 24px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: '#3b82f618', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Search size={15} color="#3b82f6" />
          </div>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: 14 }}>Lancer un scraping</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 1 }}>Pages Jaunes → scoring automatique</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {status.running && (
            <span style={{ fontSize: 12, color: '#f97316', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 5 }}>
              <Loader2 size={13} className="animate-spin" /> En cours...
            </span>
          )}
          <ChevronDown size={16} color="var(--text-muted)" style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
        </div>
      </button>

      {open && (
        <div style={{ padding: '0 24px 24px', borderTop: '1px solid var(--border)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: 20 }}>

            {/* Colonne gauche — config */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

              {/* Type d'entreprise */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 8 }}>
                  Type d'entreprise
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                  {QUERY_PRESETS.map(p => (
                    <button key={p.value} onClick={() => { setQuery(p.value); setUseCustom(false) }} style={{
                      padding: '5px 10px', borderRadius: 6, border: '1px solid var(--border)',
                      background: !useCustom && query === p.value ? 'var(--accent)' : 'transparent',
                      color: !useCustom && query === p.value ? 'white' : 'var(--text-muted)',
                      fontSize: 12, cursor: 'pointer',
                    }}>
                      {p.label}
                    </button>
                  ))}
                  <button onClick={() => setUseCustom(true)} style={{
                    padding: '5px 10px', borderRadius: 6, border: '1px solid var(--border)',
                    background: useCustom ? 'var(--accent)' : 'transparent',
                    color: useCustom ? 'white' : 'var(--text-muted)',
                    fontSize: 12, cursor: 'pointer',
                  }}>
                    Autre...
                  </button>
                </div>
                {useCustom && (
                  <input value={customQuery} onChange={e => setCustomQuery(e.target.value)}
                    placeholder="ex: plombier, électricien..." style={{
                      width: '100%', padding: '8px 12px', borderRadius: 7,
                      border: '1px solid var(--border)', background: 'var(--card)',
                      color: 'var(--text)', fontSize: 13, outline: 'none', boxSizing: 'border-box' as const,
                    }} />
                )}
              </div>

              {/* Pages */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 8 }}>
                  Pages / ville <span style={{ color: 'var(--text-dim)', fontWeight: 400 }}>(~20 résultats/page)</span>
                </label>
                <div style={{ display: 'flex', gap: 6 }}>
                  {[1, 2, 3, 5, 10].map(n => (
                    <button key={n} onClick={() => setMaxPages(n)} style={{
                      width: 44, height: 36, borderRadius: 7, border: '1px solid var(--border)',
                      background: maxPages === n ? 'var(--accent)' : 'transparent',
                      color: maxPages === n ? 'white' : 'var(--text-muted)',
                      fontSize: 13, fontWeight: 600, cursor: 'pointer',
                    }}>
                      {n}
                    </button>
                  ))}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 5 }}>
                  ≈ {maxPages * cities.length * 20} prospects max
                </div>
              </div>

              {/* Scoring auto */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <button onClick={() => setRunScoring(v => !v)} style={{
                  width: 38, height: 22, borderRadius: 11, border: 'none', cursor: 'pointer',
                  background: runScoring ? 'var(--accent)' : 'var(--border)', position: 'relative', transition: 'background 0.2s',
                }}>
                  <div style={{
                    width: 16, height: 16, borderRadius: '50%', background: 'white',
                    position: 'absolute', top: 3, left: runScoring ? 19 : 3, transition: 'left 0.2s',
                  }} />
                </button>
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Scoring automatique après scraping</span>
              </div>
            </div>

            {/* Colonne droite — villes */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 8 }}>
                Villes ciblées
              </label>
              <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
                <input
                  value={cityInput}
                  onChange={e => setCityInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addCity()}
                  placeholder="Ajouter une ville..."
                  style={{ flex: 1, padding: '8px 12px', borderRadius: 7, border: '1px solid var(--border)', background: 'var(--card)', color: 'var(--text)', fontSize: 13, outline: 'none' }}
                />
                <button onClick={addCity} style={{ padding: '8px 12px', borderRadius: 7, border: 'none', background: 'var(--accent)', color: 'white', cursor: 'pointer' }}>
                  <Plus size={15} />
                </button>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, minHeight: 36 }}>
                {cities.map(c => (
                  <span key={c} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 20, background: '#3b82f618', color: '#3b82f6', fontSize: 12, fontWeight: 500 }}>
                    {c}
                    <button onClick={() => removeCity(c)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#3b82f6', padding: 0, display: 'flex' }}>
                      <X size={11} />
                    </button>
                  </span>
                ))}
              </div>

              {/* Raccourcis villes */}
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Raccourcis :</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {['Saint-Maur-des-Fossés', 'Créteil', 'Vincennes', 'Champigny-sur-Marne', 'Joinville-le-Pont', 'Nogent-sur-Marne', 'Ivry-sur-Seine', 'Charenton-le-Pont'].map(c => (
                    <button key={c} onClick={() => { if (!cities.includes(c)) setCities(prev => [...prev, c]) }} style={{
                      padding: '3px 8px', borderRadius: 5, border: '1px solid var(--border)',
                      background: cities.includes(c) ? '#3b82f618' : 'transparent',
                      color: cities.includes(c) ? '#3b82f6' : 'var(--text-muted)',
                      fontSize: 11, cursor: 'pointer',
                    }}>
                      {c}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Bouton lancer + logs */}
          <div style={{ marginTop: 20, borderTop: '1px solid var(--border)', paddingTop: 16 }}>
            <div style={{ display: 'flex', gap: 10, marginBottom: status.log.length > 0 ? 12 : 0 }}>
              {!status.running ? (
                <button onClick={handleStart} style={{
                  display: 'flex', alignItems: 'center', gap: 8, padding: '10px 24px',
                  borderRadius: 8, border: 'none', background: 'var(--accent)', color: 'white',
                  fontSize: 13, fontWeight: 600, cursor: 'pointer',
                }}>
                  <Play size={14} fill="white" /> Lancer le scraping
                </button>
              ) : (
                <button onClick={handleStop} style={{
                  display: 'flex', alignItems: 'center', gap: 8, padding: '10px 24px',
                  borderRadius: 8, border: 'none', background: '#ef4444', color: 'white',
                  fontSize: 13, fontWeight: 600, cursor: 'pointer',
                }}>
                  <Square size={14} fill="white" /> Arrêter
                </button>
              )}
              {status.log.length > 0 && !status.running && (
                <button onClick={() => setStatus({ running: false, log: [], done: 0, total: 0 })} style={{
                  padding: '10px 16px', borderRadius: 8, border: '1px solid var(--border)',
                  background: 'transparent', color: 'var(--text-muted)', fontSize: 13, cursor: 'pointer',
                }}>
                  Effacer
                </button>
              )}
            </div>

            {status.log.length > 0 && (
              <div ref={logRef} style={{
                background: '#0a0f1a', borderRadius: 8, padding: '12px 16px',
                fontFamily: 'monospace', fontSize: 12, color: '#94a3b8',
                maxHeight: 160, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4,
              }}>
                {status.log.map((line, i) => (
                  <div key={i} style={{
                    color: line.startsWith('✅') || line.startsWith('🎉') ? '#22c55e'
                      : line.startsWith('❌') ? '#ef4444'
                      : line.startsWith('⚙️') ? '#f97316'
                      : '#94a3b8'
                  }}>
                    {line}
                  </div>
                ))}
                {status.running && <div style={{ color: '#3b82f6' }}>⏳ En cours...</div>}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Dashboard principal ───────────────────────────────────────────────────────
export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadStats = () => {
    fetchStats()
      .then(setStats)
      .catch(() => setError("Impossible de joindre l'API. Vérifiez que FastAPI tourne sur le port 8000."))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadStats() }, [])

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 12, color: 'var(--text-muted)' }}>
      <Loader2 size={20} className="animate-spin" /> Chargement...
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
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontFamily: 'Syne', fontSize: 28, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' }}>Dashboard</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 4, fontSize: 14 }}>Vue d'ensemble de ta pipeline commerciale</p>
      </div>

      {/* Panneau scraping */}
      <ScrapePanel onDone={loadStats} />
      <SchedulerPanel />
      <RapportPanel />

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        <KpiCard icon={Users}      label="Total Prospects"  value={stats.total}               color="#3b82f6" />
        <KpiCard icon={Mail}       label="Avec Email"        value={stats.with_email}          sub={`${stats.email_rate}% du total`} color="#22c55e" />
        <KpiCard icon={Phone}      label="Avec Téléphone"    value={stats.with_phone}          color="#a78bfa" />
        <KpiCard icon={TrendingUp} label="Score Moyen"       value={`${stats.avg_score}/100`}  color="#f97316" />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
        <KpiCard icon={Star}  label="🔥 Priorité haute"   value={stats.score_distribution.haute}   color="#22c55e" />
        <KpiCard icon={Star}  label="⚡ Priorité moyenne"  value={stats.score_distribution.moyenne} color="#eab308" />
        <KpiCard icon={Star}  label="🌱 Priorité faible"   value={stats.score_distribution.faible}  color="#f97316" />
        <KpiCard icon={Globe} label="Avec Site Web"        value={stats.with_web}                   color="#06b6d4" />
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 15, fontWeight: 700, margin: '0 0 20px', color: 'var(--text)' }}>Prospects par ville</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={topCities} margin={{ top: 0, right: 0, bottom: 20, left: -20 }}>
              <XAxis dataKey="city" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} angle={-35} textAnchor="end" interval={0} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {topCities.map((_, i) => <Cell key={i} fill={i === 0 ? '#3b82f6' : '#1e3a5f'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 15, fontWeight: 700, margin: '0 0 20px', color: 'var(--text)' }}>Distribution des scores</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
            <ResponsiveContainer width={180} height={180}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value">
                  {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
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