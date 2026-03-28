'use client'
import { useEffect, useState, useRef } from 'react'
import {
  Mail, MessageSquare, FileText, Search, Zap,
  Database, Settings, AlertCircle, RefreshCw,
  Loader2, TrendingUp, CheckCircle, Clock,
  ChevronDown, ChevronUp, Filter
} from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Log = {
  id: number
  event_type: string
  event_sub: string | null
  message: string
  status: string
  prospect_id: number | null
  prospect_name: string | null
  metric_value: number | null
  ia_decision: string | null
  details: any
  created_at: string
}

type Summary = {
  date: string
  emails_envoyes: number
  emails_recus: number
  devis_envoyes: number
  devis_montant_total: number
  nouveaux_prospects: number
  prospects_enrichis: number
  signatures: number
  erreurs: number
  total_actions: number
}

type Stats = {
  emails_envoyes: number
  emails_recus: number
  taux_reponse_pct: number
  devis_envoyes: number
  ca_pipeline: number
  nouveaux_prospects: number
  signatures: number
}

const EVENT_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  email_sent:     { icon: Mail,         color: '#3b82f6', label: 'Email envoyé' },
  email_received: { icon: Mail,         color: '#a855f7', label: 'Email reçu' },
  qualification:  { icon: MessageSquare,color: '#06b6d4', label: 'Qualification' },
  devis_sent:     { icon: FileText,     color: '#22c55e', label: 'Devis' },
  scraping:       { icon: Search,       color: '#f97316', label: 'Scraping' },
  enrichment:     { icon: Database,     color: '#eab308', label: 'Enrichissement' },
  system:         { icon: Settings,     color: '#64748b', label: 'Système' },
  error:          { icon: AlertCircle,  color: '#ef4444', label: 'Erreur' },
  scheduler:      { icon: Clock,        color: '#8b5cf6', label: 'Scheduler' },
  watchdog:       { icon: Zap,          color: '#10b981', label: 'Watchdog' },
}

const STATUS_COLOR: Record<string, string> = {
  success: '#22c55e', warning: '#f97316',
  error: '#ef4444', info: '#3b82f6',
}

function KpiCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color: string }) {
  return (
    <div style={{ padding: '16px 20px', borderRadius: 10, background: `${color}08`, border: `1px solid ${color}20`, flex: 1 }}>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>{label}</div>
      <div style={{ fontFamily: 'Syne', fontSize: 28, fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

function LogItem({ log, showDetails }: { log: Log; showDetails: boolean }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = EVENT_CONFIG[log.event_type] || EVENT_CONFIG.system
  const Icon = cfg.icon
  const statusColor = STATUS_COLOR[log.status] || '#64748b'
  const time = new Date(log.created_at).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'
  })

  return (
    <div style={{
      padding: '10px 14px', borderRadius: 8,
      background: log.status === 'error' ? '#ef444408' : 'var(--surface)',
      border: `1px solid ${log.status === 'error' ? '#ef444430' : 'var(--border)'}`,
      transition: 'all 0.1s',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {/* Icône type */}
        <div style={{ width: 28, height: 28, borderRadius: 7, background: `${cfg.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Icon size={13} color={cfg.color} />
        </div>

        {/* Message */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, color: 'var(--text)', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {log.message}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 3 }}>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{time}</span>
            {log.prospect_name && (
              <a href={`/prospects/${log.prospect_id}`} style={{ fontSize: 10, color: cfg.color, textDecoration: 'none', fontWeight: 600 }}>
                → {log.prospect_name}
              </a>
            )}
            {log.metric_value !== null && log.metric_value !== undefined && (
              <span style={{ fontSize: 10, fontWeight: 600, color: cfg.color }}>
                {log.event_type === 'devis_sent' ? `${log.metric_value.toLocaleString('fr-FR')}€` : log.metric_value}
              </span>
            )}
          </div>
        </div>

        {/* Badge statut */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: statusColor, flexShrink: 0 }} />
          {(log.ia_decision || log.details) && (
            <button onClick={() => setExpanded(e => !e)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 2 }}>
              {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
          )}
        </div>
      </div>

      {/* Détails expandables */}
      {expanded && (
        <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--border)', fontSize: 11 }}>
          {log.ia_decision && (
            <div style={{ marginBottom: 6 }}>
              <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Décision IA : </span>
              <span style={{ color: 'var(--text)' }}>{log.ia_decision}</span>
            </div>
          )}
          {log.details && (
            <pre style={{ fontSize: 10, color: 'var(--text-muted)', background: 'var(--bg)', padding: '6px 10px', borderRadius: 5, overflow: 'auto', margin: 0 }}>
              {JSON.stringify(log.details, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}

export default function ActivitePage() {
  const [logs, setLogs] = useState<Log[]>([])
  const [total, setTotal] = useState(0)
  const [stats, setStats] = useState<Stats | null>(null)
  const [summaries, setSummaries] = useState<Summary[]>([])
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const [days, setDays] = useState(1)
  const [limit, setLimit] = useState(100)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const fetchAll = async () => {
    const type = filter === 'all' ? '' : `&event_type=${filter}`
    const [logsRes, statsRes, summRes] = await Promise.all([
      fetch(`${API}/api/activity/logs?limit=${limit}&days=${days}${type}`),
      fetch(`${API}/api/activity/stats`),
      fetch(`${API}/api/activity/summary?days=7`),
    ])
    const logsData = await logsRes.json()
    setLogs(logsData.logs || [])
    setTotal(logsData.total || 0)
    setStats(await statsRes.json())
    setSummaries(await summRes.json())
    setLoading(false)
  }

  useEffect(() => {
    fetchAll()
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchAll, 15000)
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [filter, days, limit, autoRefresh])

  const today = summaries[0]

  return (
    <div style={{ padding: '32px 36px', maxWidth: 1100 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontFamily: 'Syne', fontSize: 28, fontWeight: 800, margin: 0 }}>Journal d'activité</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 6, fontSize: 13 }}>
            {total} événements · mis à jour en temps réel
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={() => setAutoRefresh(a => !a)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '7px 12px',
              borderRadius: 7, border: '1px solid var(--border)',
              background: autoRefresh ? '#3b82f618' : 'transparent',
              color: autoRefresh ? '#3b82f6' : 'var(--text-muted)',
              fontSize: 12, cursor: 'pointer', fontWeight: autoRefresh ? 600 : 400
            }}
          >
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: autoRefresh ? '#22c55e' : 'var(--border)' }} />
            {autoRefresh ? 'Live' : 'Pausé'}
          </button>
          <button onClick={fetchAll} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 12px', borderRadius: 7, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer' }}>
            <RefreshCw size={13} /> Actualiser
          </button>
        </div>
      </div>

      {/* KPIs semaine */}
      {stats && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
          <KpiCard label="Emails envoyés" value={stats.emails_envoyes} sub="7 derniers jours" color="#3b82f6" />
          <KpiCard label="Taux de réponse" value={`${stats.taux_reponse_pct}%`} sub={`${stats.emails_recus} réponses`} color="#a855f7" />
          <KpiCard label="Devis envoyés" value={stats.devis_envoyes} sub={`${stats.ca_pipeline.toLocaleString('fr-FR')}€ pipeline`} color="#22c55e" />
          <KpiCard label="Nouveaux prospects" value={stats.nouveaux_prospects} sub="via scraping" color="#f97316" />
          <KpiCard label="Signatures" value={stats.signatures} sub="cette semaine" color="#eab308" />
        </div>
      )}

      {/* Résumé aujourd'hui */}
      {today && today.total_actions > 0 && (
        <div className="card" style={{ padding: '14px 20px', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Aujourd'hui</span>
          {[
            { label: 'actions', value: today.total_actions, color: '#3b82f6' },
            { label: 'emails', value: today.emails_envoyes, color: '#3b82f6' },
            { label: 'réponses', value: today.emails_recus, color: '#a855f7' },
            { label: 'devis', value: today.devis_envoyes, color: '#22c55e' },
            { label: 'prospects', value: today.nouveaux_prospects, color: '#f97316' },
            { label: 'erreurs', value: today.erreurs, color: '#ef4444' },
          ].map(({ label, value, color }) => value > 0 && (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: 18, color }}>{value}</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{label}</span>
            </div>
          ))}
          {today.devis_montant_total > 0 && (
            <div style={{ marginLeft: 'auto', fontSize: 13, fontWeight: 700, color: '#22c55e' }}>
              {today.devis_montant_total.toLocaleString('fr-FR')}€ TTC signés
            </div>
          )}
        </div>
      )}

      {/* Filtres */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <Filter size={13} color="var(--text-muted)" />
        {[
          { key: 'all', label: 'Tout' },
          { key: 'email_sent', label: '📧 Emails envoyés' },
          { key: 'email_received', label: '📬 Reçus' },
          { key: 'qualification', label: '🤖 Qualification' },
          { key: 'devis_sent', label: '📄 Devis' },
          { key: 'scraping', label: '🔍 Scraping' },
          { key: 'enrichment', label: '📊 Enrichissement' },
          { key: 'error', label: '❌ Erreurs' },
          { key: 'system', label: '⚙️ Système' },
        ].map(({ key, label }) => (
          <button key={key} onClick={() => setFilter(key)} style={{
            padding: '5px 12px', borderRadius: 20, border: '1px solid var(--border)',
            background: filter === key ? 'var(--accent)' : 'transparent',
            color: filter === key ? 'white' : 'var(--text-muted)',
            fontSize: 11, cursor: 'pointer', fontWeight: filter === key ? 600 : 400
          }}>
            {label}
          </button>
        ))}

        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
          <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '5px 8px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)', fontSize: 12 }}>
            <option value={1}>Aujourd'hui</option>
            <option value={7}>7 jours</option>
            <option value={30}>30 jours</option>
          </select>
        </div>
      </div>

      {/* Liste des logs */}
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', padding: 20 }}>
          <Loader2 size={16} className="animate-spin" /> Chargement...
        </div>
      ) : logs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
          <Clock size={32} style={{ opacity: 0.3, marginBottom: 12 }} />
          <div>Aucune activité pour cette période</div>
          <div style={{ fontSize: 12, marginTop: 4 }}>Les actions des agents apparaîtront ici en temps réel</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {logs.map(log => <LogItem key={log.id} log={log} showDetails={true} />)}
          {total > logs.length && (
            <button onClick={() => setLimit(l => l + 100)} style={{ padding: '10px', borderRadius: 8, border: '1px dashed var(--border)', background: 'transparent', color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer' }}>
              Charger plus ({total - logs.length} restants)
            </button>
          )}
        </div>
      )}
    </div>
  )
}