'use client'
import { useEffect, useState } from 'react'
import { Sun, Moon } from 'lucide-react'

export function ThemeToggle() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')

  useEffect(() => {
    const saved = localStorage.getItem('proprexis-theme') as 'dark' | 'light' | null
    if (saved) {
      setTheme(saved)
      document.documentElement.setAttribute('data-theme', saved)
    }
  }, [])

  const toggle = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    localStorage.setItem('proprexis-theme', next)
    document.documentElement.setAttribute('data-theme', next)
  }

  return (
    <button
      onClick={toggle}
      title={theme === 'dark' ? 'Passer en mode jour' : 'Passer en mode nuit'}
      style={{
        display: 'flex', alignItems: 'center', gap: 6,
        padding: '6px 10px', borderRadius: 8,
        border: '1px solid var(--border)',
        background: 'var(--surface)',
        color: 'var(--text-muted)',
        cursor: 'pointer', fontSize: 12,
        transition: 'all 0.15s',
      }}
    >
      {theme === 'dark'
        ? <><Sun size={14} color="#eab308" /> <span>Jour</span></>
        : <><Moon size={14} color="#3b82f6" /> <span>Nuit</span></>
      }
    </button>
  )
}