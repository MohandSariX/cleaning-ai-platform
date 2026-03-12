'use client'
import { useEffect, useState, useCallback } from 'react'
import { ChevronLeft, ChevronRight, Plus, Loader2, X, Check, Clock, MapPin } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Chantier = {
  id: number; titre: string; client_name: string
  date_debut: string | null; date_fin: string | null
  heure_debut: string | null; duree_heures: number | null
  ville: string | null; type: string; status: string; recurrence: string
}

const TYPE_COLORS: Record<string, string> = {
  bureaux:      '#3b82f6',
  fin_chantier: '#f97316',
  copropriete:  '#a78bfa',
  autre:        '#64748b',
}

const STATUS_DOT: Record<string, string> = {
  planifie: '#3b82f6',
  en_cours: '#f97316',
  termine:  '#22c55e',
  annule:   '#64748b',
}

const DAYS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
const MONTHS = ['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre']

function getMonday(date: Date) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  d.setDate(diff)
  d.setHours(0, 0, 0, 0)
  return d
}

function addDays(date: Date, n: number) {
  const d = new Date(date)
  d.setDate(d.getDate() + n)
  return d
}

function isSameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
}

function ChantierCard({ c, onClick }: { c: Chantier; onClick: () => void }) {
  const color = TYPE_COLORS[c.type] || '#64748b'
  return (
    <div onClick={onClick} style={{
      background: `${color}15`, border: `1px solid ${color}40`,
      borderLeft: `3px solid ${color}`, borderRadius: 6,
      padding: '5px 8px', marginBottom: 4, cursor: 'pointer',
      transition: 'all 0.15s',
    }}
      onMouseEnter={e => (e.currentTarget.style.background = `${color}25`)}
      onMouseLeave={e => (e.currentTarget.style.background = `${color}15`)}
    >
      <div style={{ fontSize: 11, fontWeight: 600, color, lineHeight: 1.3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {c.heure_debut && <span style={{ marginRight: 4 }}>🕐{c.heure_debut}</span>}
        {c.titre}
      </div>
      <div style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 3 }}>
        <span style={{ width: 5, height: 5, borderRadius: '50%', background: STATUS_DOT[c.status], display: 'inline-block' }} />
        {c.client_name}
        {c.ville && <><span>·</span><MapPin size={8} />{c.ville}</>}
      </div>
    </div>
  )
}

function ChantierDetailModal({ chantier, onClose, onStatusChange }: {
  chantier: Chantier; onClose: () => void; onStatusChange: (id: number, status: string) => void
}) {
  const color = TYPE_COLORS[chantier.type] || '#64748b'
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="card" style={{ width: 420, padding: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 11, color, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>{chantier.type.replace('_', ' ')}</div>
            <h2 style={{ fontFamily: 'Syne', fontSize: 17, fontWeight: 700, margin: 0, lineHeight: 1.3 }}>{chantier.titre}</h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', marginLeft: 12 }}><X size={18} /></button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
          <div style={{ display: 'flex', gap: 10 }}>
            <div className="card" style={{ flex: 1, padding: '12px 14px', background: 'var(--surface)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 4 }}>CLIENT</div>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{chantier.client_name}</div>
            </div>
            {chantier.ville && (
              <div className="card" style={{ flex: 1, padding: '12px 14px', background: 'var(--surface)' }}>
                <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 4 }}>VILLE</div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{chantier.ville}</div>
              </div>
            )}
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            {chantier.heure_debut && (
              <div className="card" style={{ flex: 1, padding: '12px 14px', background: 'var(--surface)' }}>
                <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 4 }}>HEURE</div>
                <div style={{ fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Clock size={13} color={color} /> {chantier.heure_debut}
                </div>
              </div>
            )}
            {chantier.duree_heures && (
              <div className="card" style={{ flex: 1, padding: '12px 14px', background: 'var(--surface)' }}>
                <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 4 }}>DURÉE</div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{chantier.duree_heures}h</div>
              </div>
            )}
            <div className="card" style={{ flex: 1, padding: '12px 14px', background: 'var(--surface)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 4 }}>RÉCURRENCE</div>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{chantier.recurrence}</div>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>CHANGER LE STATUT</div>
          <div style={{ display: 'flex', gap: 8 }}>
            {['planifie', 'en_cours', 'termine', 'annule'].map(s => (
              <button key={s} onClick={() => { onStatusChange(chantier.id, s); onClose() }}
                style={{
                  flex: 1, padding: '7px 4px', borderRadius: 7, border: `1px solid ${chantier.status === s ? STATUS_DOT[s] : 'var(--border)'}`,
                  background: chantier.status === s ? `${STATUS_DOT[s]}20` : 'transparent',
                  color: chantier.status === s ? STATUS_DOT[s] : 'var(--text-muted)',
                  fontSize: 10, fontWeight: 600, cursor: 'pointer', textAlign: 'center',
                }}>
                {s === 'planifie' ? 'Planifié' : s === 'en_cours' ? 'En cours' : s === 'termine' ? 'Terminé' : 'Annulé'}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function PlanningPage() {
  const [chantiers, setChantiers] = useState<Chantier[]>([])
  const [loading, setLoading] = useState(true)
  const [weekStart, setWeekStart] = useState(() => getMonday(new Date()))
  const [selected, setSelected] = useState<Chantier | null>(null)
  const [view, setView] = useState<'semaine' | 'mois'>('semaine')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await fetch(`${API}/api/chantiers?limit=500`)
      const data = await r.json()
      setChantiers(data)
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const changeStatus = async (id: number, status: string) => {
    await fetch(`${API}/api/chantiers/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) })
    load()
  }

  // Semaine courante : lun → dim
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))

  const getChantiersForDay = (day: Date) =>
    chantiers.filter(c => {
      if (!c.date_debut) return false
      const start = new Date(c.date_debut)
      const end = c.date_fin ? new Date(c.date_fin) : start
      return day >= start && day <= end
    })

  // Vue mois
  const today = new Date()
  const [monthDate, setMonthDate] = useState(new Date(today.getFullYear(), today.getMonth(), 1))
  const daysInMonth = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).getDate()
  const firstDayOfMonth = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1).getDay()
  const startOffset = firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1

  const getChantiersForDate = (date: Date) =>
    chantiers.filter(c => {
      if (!c.date_debut) return false
      const start = new Date(c.date_debut)
      const end = c.date_fin ? new Date(c.date_fin) : start
      return date >= start && date <= end
    })

  const btnStyle = (active: boolean) => ({
    padding: '6px 14px', borderRadius: 7, border: '1px solid var(--border)',
    background: active ? 'var(--accent)' : 'transparent',
    color: active ? 'white' : 'var(--text-muted)',
    fontSize: 12, fontWeight: 600, cursor: 'pointer',
  })

  return (
    <div style={{ padding: '32px 36px' }}>
      {selected && <ChantierDetailModal chantier={selected} onClose={() => setSelected(null)} onStatusChange={changeStatus} />}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontFamily: 'Syne', fontSize: 28, fontWeight: 800, margin: 0 }}>Planning</h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button style={btnStyle(view === 'semaine')} onClick={() => setView('semaine')}>Semaine</button>
          <button style={btnStyle(view === 'mois')} onClick={() => setView('mois')}>Mois</button>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 80, gap: 10, color: 'var(--text-muted)' }}>
          <Loader2 size={18} className="animate-spin" /> Chargement...
        </div>
      ) : view === 'semaine' ? (
        <>
          {/* Navigation semaine */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
            <button onClick={() => setWeekStart(d => addDays(d, -7))} style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex' }}>
              <ChevronLeft size={16} />
            </button>
            <div style={{ fontFamily: 'Syne', fontSize: 15, fontWeight: 700 }}>
              {weekDays[0].toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} — {weekDays[6].toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })}
            </div>
            <button onClick={() => setWeekStart(d => addDays(d, 7))} style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex' }}>
              <ChevronRight size={16} />
            </button>
            <button onClick={() => setWeekStart(getMonday(new Date()))} style={{ marginLeft: 4, padding: '6px 12px', borderRadius: 7, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer' }}>
              Aujourd'hui
            </button>
          </div>

          {/* Grille semaine */}
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', borderBottom: '1px solid var(--border)' }}>
              {weekDays.map((day, i) => {
                const isToday = isSameDay(day, today)
                return (
                  <div key={i} style={{ padding: '10px 12px', borderRight: i < 6 ? '1px solid var(--border-soft)' : 'none', textAlign: 'center' }}>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 4 }}>{DAYS[i]}</div>
                    <div style={{
                      fontSize: 16, fontWeight: 700, fontFamily: 'Syne',
                      width: 30, height: 30, borderRadius: '50%', margin: '0 auto',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: isToday ? 'var(--accent)' : 'transparent',
                      color: isToday ? 'white' : 'var(--text)',
                    }}>
                      {day.getDate()}
                    </div>
                  </div>
                )
              })}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', minHeight: 400 }}>
              {weekDays.map((day, i) => {
                const items = getChantiersForDay(day)
                return (
                  <div key={i} style={{ padding: '10px 8px', borderRight: i < 6 ? '1px solid var(--border-soft)' : 'none', minHeight: 200 }}>
                    {items.map(c => <ChantierCard key={c.id} c={c} onClick={() => setSelected(c)} />)}
                    {items.length === 0 && (
                      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>—</span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </>
      ) : (
        <>
          {/* Navigation mois */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
            <button onClick={() => setMonthDate(d => new Date(d.getFullYear(), d.getMonth() - 1, 1))} style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex' }}>
              <ChevronLeft size={16} />
            </button>
            <div style={{ fontFamily: 'Syne', fontSize: 15, fontWeight: 700 }}>
              {MONTHS[monthDate.getMonth()]} {monthDate.getFullYear()}
            </div>
            <button onClick={() => setMonthDate(d => new Date(d.getFullYear(), d.getMonth() + 1, 1))} style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex' }}>
              <ChevronRight size={16} />
            </button>
            <button onClick={() => setMonthDate(new Date(today.getFullYear(), today.getMonth(), 1))} style={{ marginLeft: 4, padding: '6px 12px', borderRadius: 7, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer' }}>
              Ce mois
            </button>
          </div>

          <div className="card" style={{ overflow: 'hidden' }}>
            {/* En-têtes jours */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', borderBottom: '1px solid var(--border)' }}>
              {DAYS.map(d => (
                <div key={d} style={{ padding: '10px', textAlign: 'center', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{d}</div>
              ))}
            </div>
            {/* Grille mois */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)' }}>
              {/* Cases vides début */}
              {Array.from({ length: startOffset }, (_, i) => (
                <div key={`e${i}`} style={{ minHeight: 90, borderRight: '1px solid var(--border-soft)', borderBottom: '1px solid var(--border-soft)', background: 'var(--surface)' }} />
              ))}
              {/* Jours du mois */}
              {Array.from({ length: daysInMonth }, (_, i) => {
                const date = new Date(monthDate.getFullYear(), monthDate.getMonth(), i + 1)
                const col = (startOffset + i) % 7
                const isToday = isSameDay(date, today)
                const items = getChantiersForDate(date)
                return (
                  <div key={i} style={{
                    minHeight: 90, padding: '6px 6px',
                    borderRight: col < 6 ? '1px solid var(--border-soft)' : 'none',
                    borderBottom: '1px solid var(--border-soft)',
                    background: isToday ? 'var(--accent)08' : 'transparent',
                  }}>
                    <div style={{
                      fontSize: 12, fontWeight: 700, marginBottom: 4,
                      width: 22, height: 22, borderRadius: '50%',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: isToday ? 'var(--accent)' : 'transparent',
                      color: isToday ? 'white' : 'var(--text-muted)',
                    }}>
                      {i + 1}
                    </div>
                    {items.slice(0, 2).map(c => <ChantierCard key={c.id} c={c} onClick={() => setSelected(c)} />)}
                    {items.length > 2 && <div style={{ fontSize: 10, color: 'var(--text-dim)', paddingLeft: 4 }}>+{items.length - 2} autres</div>}
                  </div>
                )
              })}
              {/* Cases vides fin */}
              {Array.from({ length: (7 - ((startOffset + daysInMonth) % 7)) % 7 }, (_, i) => (
                <div key={`ef${i}`} style={{ minHeight: 90, borderRight: i < 6 ? '1px solid var(--border-soft)' : 'none', background: 'var(--surface)' }} />
              ))}
            </div>
          </div>
        </>
      )}

      {/* Légende */}
      <div style={{ display: 'flex', gap: 20, marginTop: 16, flexWrap: 'wrap' }}>
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-muted)' }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: color }} />
            {type === 'bureaux' ? 'Bureaux' : type === 'fin_chantier' ? 'Fin de chantier' : type === 'copropriete' ? 'Copropriété' : 'Autre'}
          </div>
        ))}
      </div>
    </div>
  )
}