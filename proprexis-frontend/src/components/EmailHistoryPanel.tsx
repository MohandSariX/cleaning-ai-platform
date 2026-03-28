'use client'
import { useEffect, useState } from 'react'
import { Mail, CheckCircle, XCircle, RefreshCw, Clock } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type EmailLog = {
  id: number
  email_type: string
  recipient: string
  subject: string
  status: string
  sent_at: string
}

export function EmailHistoryPanel({ prospectId }: { prospectId: number }) {
  const [logs, setLogs] = useState<EmailLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/api/prospects/${prospectId}/emails`)
      .then(r => r.json())
      .then(data => { setLogs(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [prospectId])

  if (loading) return null
  if (!logs.length) return (
    <div style={{ padding: '12px 0', color: 'var(--text-muted)', fontSize: 13 }}>
      Aucun email envoyé à ce prospect.
    </div>
  )

  const typeLabel: Record<string, string> = {
    prospection: 'Prospection',
    relance: 'Relance',
    qualification: 'Qualification',
    devis: 'Devis',
  }

  const typeColor: Record<string, string> = {
    prospection: '#3b82f6',
    relance: '#f97316',
    qualification: '#a855f7',
    devis: '#22c55e',
  }

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>
        Historique emails ({logs.length})
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {logs.map(log => {
          const color = typeColor[log.email_type] || '#64748b'
          const Icon = log.status === 'sent' ? CheckCircle : XCircle
          return (
            <div key={log.id} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 12px', borderRadius: 7,
              background: `${color}08`, border: `1px solid ${color}20`
            }}>
              <Icon size={13} color={log.status === 'sent' ? '#22c55e' : '#ef4444'} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>{log.subject || '(sans sujet)'}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>{log.recipient}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 11, padding: '2px 7px', borderRadius: 6, background: `${color}20`, color, fontWeight: 600 }}>
                  {typeLabel[log.email_type] || log.email_type}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>
                  {new Date(log.sent_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}