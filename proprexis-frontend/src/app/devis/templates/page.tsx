'use client'
import { useEffect, useState } from 'react'
import { FileText, Plus, Edit2, Trash2, Check, X, Loader2 } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type DevisTemplate = {
  id: number
  name: string
  category: string | null
  type_prestation: string | null
  description: string | null
  template_json: any
  variables_required: string[]
  is_default: boolean
  active: boolean
  created_at: string
}

export default function DevisTemplatesPage() {
  const [templates, setTemplates] = useState<DevisTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    type_prestation: '',
    description: '',
    template_json: '{}',
    variables_required: '',
    is_default: false
  })

  const loadTemplates = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/devis-templates/?active_only=false`)
      setTemplates(await res.json())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTemplates()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const payload = {
      name: formData.name,
      category: formData.category || null,
      type_prestation: formData.type_prestation || null,
      description: formData.description || null,
      template_json: JSON.parse(formData.template_json),
      variables_required: formData.variables_required
        .split(',')
        .map(v => v.trim())
        .filter(v => v),
      is_default: formData.is_default,
      active: true
    }

    const url = editingId
      ? `${API}/api/devis-templates/${editingId}`
      : `${API}/api/devis-templates/`

    const method = editingId ? 'PATCH' : 'POST'

    await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    setShowForm(false)
    setEditingId(null)
    setFormData({
      name: '',
      category: '',
      type_prestation: '',
      description: '',
      template_json: '{}',
      variables_required: '',
      is_default: false
    })
    loadTemplates()
  }

  const handleEdit = (template: DevisTemplate) => {
    setEditingId(template.id)
    setFormData({
      name: template.name,
      category: template.category || '',
      type_prestation: template.type_prestation || '',
      description: template.description || '',
      template_json: JSON.stringify(template.template_json, null, 2),
      variables_required: template.variables_required.join(', '),
      is_default: template.is_default
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Supprimer ce template ?')) return

    await fetch(`${API}/api/devis-templates/${id}`, { method: 'DELETE' })
    loadTemplates()
  }

  if (loading) {
    return (
      <div style={{ padding: '32px 36px', display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)' }}>
        <Loader2 size={18} className="animate-spin" /> Chargement templates...
      </div>
    )
  }

  return (
    <div style={{ padding: '32px 36px', maxWidth: 1400 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Templates de devis</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 6, fontSize: 13 }}>
            Gérer les templates personnalisables
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '10px 18px',
            borderRadius: 8,
            border: 'none',
            background: '#f5a623',
            color: '#fff',
            fontSize: 13,
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          <Plus size={16} />
          Nouveau template
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="card" style={{ padding: '24px', marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20 }}>
            {editingId ? 'Modifier template' : 'Nouveau template'}
          </h2>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-muted)' }}>
                  Nom *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: 8,
                    border: '1px solid var(--border)',
                    background: 'var(--surface)',
                    color: 'var(--text)',
                    fontSize: 13
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-muted)' }}>
                  Catégorie
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: 8,
                    border: '1px solid var(--border)',
                    background: 'var(--surface)',
                    color: 'var(--text)',
                    fontSize: 13
                  }}
                >
                  <option value="">-- Sélectionner --</option>
                  <option value="BTP">BTP</option>
                  <option value="Immobilier">Immobilier</option>
                  <option value="Bureaux">Bureaux</option>
                  <option value="Hotels">Hôtels</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-muted)' }}>
                  Type prestation
                </label>
                <select
                  value={formData.type_prestation}
                  onChange={(e) => setFormData({ ...formData, type_prestation: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: 8,
                    border: '1px solid var(--border)',
                    background: 'var(--surface)',
                    color: 'var(--text)',
                    fontSize: 13
                  }}
                >
                  <option value="">-- Sélectionner --</option>
                  <option value="bureaux">Bureaux</option>
                  <option value="fin_chantier">Fin de chantier</option>
                  <option value="copropriete">Copropriété</option>
                  <option value="vitrerie">Vitrerie</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-muted)' }}>
                  Variables requises (séparées par virgule)
                </label>
                <input
                  type="text"
                  placeholder="superficie_m2, frequence, description"
                  value={formData.variables_required}
                  onChange={(e) => setFormData({ ...formData, variables_required: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: 8,
                    border: '1px solid var(--border)',
                    background: 'var(--surface)',
                    color: 'var(--text)',
                    fontSize: 13
                  }}
                />
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-muted)' }}>
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 8,
                  border: '1px solid var(--border)',
                  background: 'var(--surface)',
                  color: 'var(--text)',
                  fontSize: 13,
                  fontFamily: 'inherit',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-muted)' }}>
                Template JSON *
              </label>
              <textarea
                required
                value={formData.template_json}
                onChange={(e) => setFormData({ ...formData, template_json: e.target.value })}
                rows={8}
                placeholder='{"sections": [{"title": "Prestation", "content": "{{description}}"}]}'
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 8,
                  border: '1px solid var(--border)',
                  background: 'var(--surface)',
                  color: 'var(--text)',
                  fontSize: 12,
                  fontFamily: 'monospace',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.is_default}
                  onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                />
                <span style={{ fontSize: 13, fontWeight: 600 }}>
                  Template par défaut pour cette catégorie/type
                </span>
              </label>
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button
                type="submit"
                style={{
                  padding: '10px 20px',
                  borderRadius: 8,
                  border: 'none',
                  background: '#22c55e',
                  color: '#fff',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6
                }}
              >
                <Check size={16} />
                {editingId ? 'Mettre à jour' : 'Créer'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false)
                  setEditingId(null)
                }}
                style={{
                  padding: '10px 20px',
                  borderRadius: 8,
                  border: '1px solid var(--border)',
                  background: 'transparent',
                  color: 'var(--text)',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6
                }}
              >
                <X size={16} />
                Annuler
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Liste templates */}
      {templates.length === 0 ? (
        <div className="card" style={{ padding: '60px 20px', textAlign: 'center' }}>
          <FileText size={48} color="var(--text-muted)" style={{ margin: '0 auto 16px' }} />
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>
            Aucun template
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Créez votre premier template de devis
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
          {templates.map(template => (
            <div
              key={template.id}
              className="card"
              style={{
                padding: '20px',
                opacity: template.active ? 1 : 0.5
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', marginBottom: 4 }}>
                    {template.name}
                    {template.is_default && (
                      <span style={{
                        marginLeft: 8,
                        padding: '2px 8px',
                        borderRadius: 4,
                        background: '#f5a62320',
                        color: '#f5a623',
                        fontSize: 10,
                        fontWeight: 600
                      }}>
                        DÉFAUT
                      </span>
                    )}
                  </div>
                  {template.category && (
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {template.category} {template.type_prestation && `• ${template.type_prestation}`}
                    </div>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => handleEdit(template)}
                    style={{
                      padding: 6,
                      borderRadius: 6,
                      border: 'none',
                      background: 'var(--surface)',
                      color: 'var(--text-muted)',
                      cursor: 'pointer'
                    }}
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    onClick={() => handleDelete(template.id)}
                    style={{
                      padding: 6,
                      borderRadius: 6,
                      border: 'none',
                      background: 'var(--surface)',
                      color: '#ef4444',
                      cursor: 'pointer'
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {template.description && (
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.5 }}>
                  {template.description}
                </p>
              )}

              {template.variables_required.length > 0 && (
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  Variables: {template.variables_required.join(', ')}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
