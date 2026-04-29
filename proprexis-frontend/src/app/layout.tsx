'use client'
import './globals.css'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ThemeToggle } from '@/components/ThemeToggle'
import {
  LayoutDashboard, Users, UserCheck,
  FileText, Briefcase, Calendar, CreditCard, Settings, Activity
} from 'lucide-react'
import clsx from 'clsx'

const nav = [
  { href: '/',            label: 'Dashboard',   icon: LayoutDashboard },
  { href: '/prospects',   label: 'Prospects',   icon: Users },
  { href: '/clients',     label: 'Clients',     icon: UserCheck },
  { href: '/devis',       label: 'Devis',       icon: FileText },
  { href: '/chantiers',   label: 'Chantiers',   icon: Briefcase },
  { href: '/planning',    label: 'Planning',    icon: Calendar },
  { href: '/facturation', label: 'Facturation', icon: CreditCard },
  { href: '/activite',    label: 'Activité',    icon: Activity },
  { href: '/parametres',  label: 'Paramètres',  icon: Settings },
]

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname()

  return (
    <html lang="fr">
      <body>
        <div className="flex h-screen overflow-hidden">

          {/* ── Sidebar ── */}
          <aside style={{
            width: 240,
            minWidth: 240,
            background: 'var(--sidebar-bg, var(--surface))',
            borderRight: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px 16px',
            gap: 4,
          }}>
            {/* Logo */}
            <div style={{ padding: '0 12px 24px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <div className="logo-text" style={{
                fontSize: 22,
                color: 'var(--sidebar-text, var(--text))',
                letterSpacing: '-0.5px',
              }}>
                Proprexis
              </div>
              <div style={{ fontSize: 11, color: 'var(--sidebar-text-muted, var(--text-muted))', marginTop: 4, fontWeight: 500 }}>
                CRM & Gestion
              </div>
            </div>

            {/* Nav */}
            <div style={{ paddingTop: 16 }}>
              {nav.map(({ href, label, icon: Icon }) => {
                const active = path === href || (href !== '/' && path?.startsWith(href))
                return (
                  <Link key={href} href={href} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '11px 14px',
                    marginBottom: 4,
                    borderRadius: 10,
                    fontSize: 14,
                    fontWeight: active ? 600 : 500,
                    color: active ? '#ffffff' : 'var(--sidebar-text-muted, var(--text-muted))',
                    background: active ? 'var(--accent, var(--border))' : 'transparent',
                    textDecoration: 'none',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={e => !active && (e.currentTarget.style.background = 'var(--sidebar-hover, var(--border-soft))')}
                  onMouseLeave={e => !active && (e.currentTarget.style.background = 'transparent')}>
                    <Icon size={18} strokeWidth={active ? 2.5 : 2} />
                    {label}
                  </Link>
                )
              })}
            </div>

            {/* Bottom */}
            <div style={{ marginTop: 'auto', padding: '12px', borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', flexDirection: 'column', gap: 12 }}>
              <ThemeToggle />
              <div style={{ fontSize: 10, color: 'var(--sidebar-text-muted, var(--text-dim))', opacity: 0.6 }}>
                Version 0.1.0 — Beta
              </div>
            </div>
          </aside>

          {/* ── Main ── */}
          <main style={{
            flex: 1,
            overflowY: 'auto',
            background: 'var(--bg)',
          }}>
            {children}
          </main>

        </div>
      </body>
    </html>
  )
}