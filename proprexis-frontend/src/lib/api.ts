const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchStats() {
  const res = await fetch(`${API}/api/stats`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch stats')
  return res.json()
}

export async function fetchProspects(params?: {
  city?: string
  status?: string
  min_score?: number
  has_email?: boolean
  search?: string
  limit?: number
}) {
  const url = new URL(`${API}/api/prospects`)
  if (params?.city)      url.searchParams.set('city', params.city)
  if (params?.status)    url.searchParams.set('status', params.status)
  if (params?.min_score) url.searchParams.set('min_score', String(params.min_score))
  if (params?.has_email !== undefined) url.searchParams.set('has_email', String(params.has_email))
  if (params?.search)    url.searchParams.set('search', params.search)
  if (params?.limit)     url.searchParams.set('limit', String(params.limit))

  const res = await fetch(url.toString(), { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch prospects')
  return res.json()
}

export async function fetchProspect(id: number) {
  const res = await fetch(`${API}/api/prospects/${id}`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch prospect')
  return res.json()
}

export async function fetchCities() {
  const res = await fetch(`${API}/api/cities`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch cities')
  return res.json()
}

export async function updateProspect(id: number, data: Record<string, unknown>) {
  const res = await fetch(`${API}/api/prospects/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to update prospect')
  return res.json()
}

// ── Clients ─────────────────────────────────────────────────

export async function fetchClients(params?: { status?: string; search?: string }) {
  const url = new URL(`${API}/api/clients`)
  if (params?.status) url.searchParams.set('status', params.status)
  if (params?.search) url.searchParams.set('search', params.search)
  const res = await fetch(url.toString(), { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch clients')
  return res.json()
}

export async function fetchClient(id: number) {
  const res = await fetch(`${API}/api/clients/${id}`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch client')
  return res.json()
}

export async function createClient(data: Record<string, unknown>) {
  const res = await fetch(`${API}/api/clients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to create client')
  return res.json()
}

export async function updateClient(id: number, data: Record<string, unknown>) {
  const res = await fetch(`${API}/api/clients/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to update client')
  return res.json()
}

export async function fetchClientsStats() {
  const res = await fetch(`${API}/api/clients/stats/summary`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch clients stats')
  return res.json()
}