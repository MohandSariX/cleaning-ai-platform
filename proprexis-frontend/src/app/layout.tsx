'use client'
import './globals.css'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard, Users, UserCheck,
  FileText, Briefcase, Calendar, CreditCard, Settings
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
            width: 220,
            minWidth: 220,
            background: 'var(--surface)',
            borderRight: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px 12px',
            gap: 4,
          }}>
            {/* Logo */}
            <div style={{ padding: '0 12px 24px' }}>
              <div style={{
                fontFamily: 'Syne, sans-serif',
                fontWeight: 800,
                fontSize: 20,
                color: 'var(--text)',
                letterSpacing: '-0.5px',
              }}>
                Proprexis
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                CRM & Gestion
              </div>
            </div>

            {/* Nav */}
            {nav.map(({ href, label, icon: Icon }) => {
              const active = path === href
              return (
                <Link key={href} href={href} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '9px 12px',
                  borderRadius: 8,
                  fontSize: 13,
                  fontWeight: active ? 600 : 400,
                  color: active ? 'var(--text)' : 'var(--text-muted)',
                  background: active ? 'var(--border)' : 'transparent',
                  textDecoration: 'none',
                  transition: 'all 0.15s',
                }}>
                  <Icon size={16} strokeWidth={active ? 2.5 : 1.8} />
                  {label}
                </Link>
              )
            })}

            {/* Bottom */}
            <div style={{ marginTop: 'auto', padding: '12px', borderTop: '1px solid var(--border-soft)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>
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
