'use client'
import { useEffect, useState } from 'react'
import { fetchProspect, updateProspect } from '@/lib/api'
import { useParams } from 'next/navigation'
import { ArrowLeft, Mail, Phone, Globe, MapPin, Building2, Star, Loader2, Check, Copy, Edit2 } from 'lucide-react'
import Link from 'next/link'

type Prospect = {
  id: number; company_name: string; city: string; address: string
  website: string | null; email: string | null; phone: string | null
  lead_score: number; score_label: string; score_explanation: string
  status: string; industry: string; created_at: string
}

const STATUSES = [
  { value: 'new',             label: 'Nouveau',    color: '#3b82f6' },
  { value: 'scored',          label: 'Scoré',      color: '#8b5cf6' },
  { value: 'email_generated', label: 'Email prêt', color: '#06b6d4' },
  { value: 'contacted',       label: 'Contacté',   color: '#f97316' },
  { value: 'replied',         label: 'Répondu',    color: '#eab308' },
  { value: 'signed',          label: 'Signé ✓',    color: '#22c55e' },
  { value: 'lost',            label: 'Perdu',      color: '#64748b' },
]

// ── Détection du type d'entreprise ──────────────────────────
function detectType(p: Prospect): string {
  const text = `${p.company_name} ${p.industry}`.toLowerCase()
  if (/promo|construct|btp|batiment|maçon|chantier|rénovation|rénov|travaux|artisan/.test(text)) return 'chantier'
  if (/immo|immobilier|agence|foncier|syndic|copropri|gestionnaire/.test(text)) return 'immo'
  if (/architect|cabinet|bureau d.étude|ingénierie|design/.test(text)) return 'archi'
  if (/hôtel|hotel|résidence|appart|airbnb|location/.test(text)) return 'hotel'
  if (/restau|brasserie|café|bar |traiteur|snack|fast/.test(text)) return 'restau'
  if (/clinique|médic|cabinet|dentiste|kiné|santé|pharmacie/.test(text)) return 'sante'
  if (/école|lycée|collège|université|formation|crèche/.test(text)) return 'education'
  if (/commerce|magasin|boutique|retail|enseigne/.test(text)) return 'commerce'
  return 'bureau' // défaut
}

// ── Templates par type ───────────────────────────────────────
const TEMPLATES: Record<string, {
  label: string; emoji: string
  intro: (p: Prospect) => { subject: string; body: string }
  relance: (p: Prospect) => { subject: string; body: string }
}> = {
  chantier: {
    label: 'BTP / Chantier', emoji: '🔨',
    intro: (p) => ({
      subject: `Nettoyage fin de chantier — ${p.company_name}`,
      body: `Bonjour,

Je me permets de vous contacter en tant qu'entreprise du bâtiment${p.city ? ` à ${p.city}` : ''}.

Proprexis est spécialisée dans le nettoyage de fin de chantier : évacuation des gravats, dégraissage des sols, nettoyage des vitres, remise en état avant livraison.

Nous intervenons rapidement après vos travaux pour que vous puissiez livrer un chantier impeccable à vos clients.

Seriez-vous intéressé par un devis gratuit pour votre prochain chantier ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
    relance: (p) => ({
      subject: `Relance — Nettoyage fin de chantier Proprexis`,
      body: `Bonjour,

Je reviens vers vous suite à mon précédent message. Si vous avez des chantiers à livrer prochainement${p.city ? ` à ${p.city}` : ''}, nous pouvons intervenir rapidement pour le nettoyage final.

N'hésitez pas à me contacter pour un devis express.

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
  },

  immo: {
    label: 'Immobilier / Syndic', emoji: '🏘',
    intro: (p) => ({
      subject: `Entretien des parties communes — ${p.company_name}`,
      body: `Bonjour,

Je me permets de vous contacter au sujet de l'entretien de vos biens immobiliers${p.city ? ` à ${p.city}` : ''}.

Proprexis propose des contrats d'entretien réguliers pour les parties communes d'immeubles, halls d'entrée, couloirs, caves et parkings, ainsi que des remises en état entre deux locations.

Nos tarifs sont adaptés aux gestionnaires de copropriétés et agences immobilières.

Puis-je vous proposer un devis personnalisé ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
    relance: (p) => ({
      subject: `Relance — Entretien copropriétés / Proprexis`,
      body: `Bonjour,

Je reviens vers vous concernant l'entretien de vos biens${p.city ? ` à ${p.city}` : ''}. Nous proposons des formules flexibles adaptées à votre parc immobilier.

Disponible pour un échange rapide cette semaine ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
  },

  archi: {
    label: 'Architecture / BE', emoji: '📐',
    intro: (p) => ({
      subject: `Nettoyage fin de chantier & livraison — ${p.company_name}`,
      body: `Bonjour,

En tant que cabinet d'architecture${p.city ? ` à ${p.city}` : ''}, vous savez à quel point la présentation lors de la livraison est importante pour vos clients.

Proprexis intervient en fin de chantier pour un nettoyage complet : vitrages, sols, sanitaires, dépoussiérage — pour que vos réalisations soient livrées dans un état impeccable.

Nous nous adaptons à vos plannings de livraison, même en urgence.

Je reste disponible pour un devis gratuit.

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
    relance: (p) => ({
      subject: `Relance — Nettoyage livraison chantier / Proprexis`,
      body: `Bonjour,

Je me permets de revenir vers vous. Si vous avez des livraisons prévues prochainement, nous pouvons intervenir rapidement pour le nettoyage final.

N'hésitez pas à me contacter.

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
  },

  hotel: {
    label: 'Hôtel / Résidence', emoji: '🏨',
    intro: (p) => ({
      subject: `Service de nettoyage professionnel — ${p.company_name}`,
      body: `Bonjour,

Je me permets de vous contacter concernant l'entretien de votre établissement${p.city ? ` à ${p.city}` : ''}.

Proprexis propose des prestations de nettoyage adaptées aux hôtels et résidences : remise en état des chambres, nettoyage des parties communes, entretien des espaces extérieurs.

Nous intervenons avec discrétion et en dehors des heures de fréquentation pour ne pas perturber votre activité.

Seriez-vous intéressé par un devis sur mesure ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
    relance: (p) => ({
      subject: `Relance — Nettoyage hôtellerie / Proprexis`,
      body: `Bonjour,

Je reviens vers vous suite à mon précédent message. Nous travaillons avec plusieurs établissements${p.city ? ` à ${p.city}` : ''} et pouvons nous adapter à vos contraintes horaires.

Un devis gratuit vous intéresse ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
  },

  restau: {
    label: 'Restauration', emoji: '🍽',
    intro: (p) => ({
      subject: `Nettoyage professionnel cuisine & salle — ${p.company_name}`,
      body: `Bonjour,

Je me permets de vous contacter au sujet de l'entretien de votre établissement${p.city ? ` à ${p.city}` : ''}.

Proprexis propose des prestations de nettoyage professionnel pour les restaurants : dégraissage cuisine, nettoyage hotte et extracteur, remise en état de salle, intervention tôt le matin ou en coupure.

Nos prestations sont conformes aux normes HACCP et peuvent être réalisées sans perturber votre service.

Je reste disponible pour un devis gratuit.

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
    relance: (p) => ({
      subject: `Relance — Nettoyage restaurant / Proprexis`,
      body: `Bonjour,

Je reviens vers vous concernant l'entretien de votre établissement${p.city ? ` à ${p.city}` : ''}. Nous intervenons tôt le matin ou en coupure pour ne pas gêner votre activité.

Intéressé par un devis ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
  },

  sante: {
    label: 'Santé / Cabinet', emoji: '🏥',
    intro: (p) => ({
      subject: `Nettoyage & désinfection locaux médicaux — ${p.company_name}`,
      body: `Bonjour,

Je me permets de vous contacter concernant l'entretien de vos locaux${p.city ? ` à ${p.city}` : ''}.

Proprexis propose des prestations de nettoyage et désinfection adaptées aux cabinets médicaux et paramédicaux : désinfection des surfaces, nettoyage des salles d'attente et sanitaires, intervention en dehors des heures de consultation.

La propreté et l'hygiène de vos locaux sont essentielles pour vos patients.

Seriez-vous disponible pour un devis gratuit ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
    relance: (p) => ({
      subject: `Relance — Nettoyage locaux médicaux / Proprexis`,
      body: `Bonjour,

Je reviens vers vous suite à mon précédent message concernant l'entretien de vos locaux${p.city ? ` à ${p.city}` : ''}.

Nous intervenons en dehors de vos heures d'ouverture pour ne pas perturber vos consultations.

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
  },

  commerce: {
    label: 'Commerce / Magasin', emoji: '🛍',
    intro: (p) => ({
      subject: `Entretien de votre commerce — ${p.company_name}`,
      body: `Bonjour,

Je me permets de vous contacter au sujet de l'entretien de votre point de vente${p.city ? ` à ${p.city}` : ''}.

Proprexis assure le nettoyage de commerces et magasins : sols, vitrines, réserves, sanitaires — en dehors de vos heures d'ouverture pour ne pas déranger votre clientèle.

Un local propre, c'est une meilleure image pour vos clients.

Seriez-vous intéressé par un devis adapté à votre superficie ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
    relance: (p) => ({
      subject: `Relance — Nettoyage commerce / Proprexis`,
      body: `Bonjour,

Je reviens vers vous concernant l'entretien de votre commerce${p.city ? ` à ${p.city}` : ''}. Nous intervenons avant ou après votre ouverture selon vos préférences.

Un devis gratuit vous intéresse ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
  },

  bureau: {
    label: 'Bureaux / Entreprise', emoji: '🏢',
    intro: (p) => ({
      subject: `Nettoyage de vos bureaux — ${p.company_name}`,
      body: `Bonjour,

Je me permets de vous contacter au sujet de l'entretien de vos locaux professionnels${p.city ? ` à ${p.city}` : ''}.

Proprexis assure le nettoyage de bureaux et espaces de travail : postes de travail, sols, sanitaires, espaces communs — en formule ponctuelle ou contrat régulier selon vos besoins.

Nous intervenons tôt le matin ou en soirée pour ne pas perturber votre activité.

Seriez-vous disponible pour un devis gratuit et sans engagement ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
    relance: (p) => ({
      subject: `Relance — Nettoyage bureaux / Proprexis`,
      body: `Bonjour,

Je reviens vers vous suite à mon précédent message concernant l'entretien de vos locaux${p.city ? ` à ${p.city}` : ''}.

Si vous souhaitez un devis rapide, je suis disponible cette semaine.

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
  },

  education: {
    label: 'Éducation / Formation', emoji: '🎓',
    intro: (p) => ({
      subject: `Nettoyage établissement scolaire — ${p.company_name}`,
      body: `Bonjour,

Je me permets de vous contacter concernant l'entretien de votre établissement${p.city ? ` à ${p.city}` : ''}.

Proprexis propose des prestations de nettoyage adaptées aux établissements scolaires et de formation : salles de classe, couloirs, sanitaires, réfectoires — intervenant en dehors des heures de cours.

Un environnement propre contribue au bien-être des élèves et du personnel.

Je reste disponible pour un devis personnalisé.

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
    relance: (p) => ({
      subject: `Relance — Nettoyage établissement / Proprexis`,
      body: `Bonjour,

Je reviens vers vous concernant l'entretien de votre établissement${p.city ? ` à ${p.city}` : ''}. Nous intervenons pendant les vacances scolaires ou en dehors des heures de cours.

Intéressé par un devis ?

Cordialement,
Mohand Sari — Proprexis
contact@proprexis.fr | 06 XX XX XX XX`,
    }),
  },
}

function EmailPanel({ prospect, onStatusChange }: { prospect: Prospect; onStatusChange: (s: string) => void }) {
  const detectedType = detectType(prospect)
  const template = TEMPLATES[detectedType]

  const [mode, setMode] = useState<'intro' | 'relance'>('intro')
  const [subject, setSubject] = useState(() => template[mode === 'intro' ? 'intro' : 'relance'](prospect).subject)
  const [body, setBody] = useState(() => template[mode === 'intro' ? 'intro' : 'relance'](prospect).body)
  const [copied, setCopied] = useState<'subject' | 'body' | null>(null)

  const switchMode = (m: 'intro' | 'relance') => {
    setMode(m)
    const t = template[m === 'intro' ? 'intro' : 'relance'](prospect)
    setSubject(t.subject)
    setBody(t.body)
  }

  const copy = async (text: string, type: 'subject' | 'body') => {
    await navigator.clipboard.writeText(text)
    setCopied(type)
    setTimeout(() => setCopied(null), 2000)
  }

  const openInMail = () => {
    window.open(`mailto:${prospect.email || ''}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`)
    onStatusChange('contacted')
  }

  const taStyle = {
    width: '100%', background: 'var(--card)', border: '1px solid var(--border)',
    borderRadius: 8, padding: '10px 12px', color: 'var(--text)', fontSize: 13,
    lineHeight: 1.7, outline: 'none', resize: 'vertical' as const,
    fontFamily: 'DM Sans, sans-serif', boxSizing: 'border-box' as const,
  }

  return (
    <div className="card" style={{ padding: 24, gridColumn: '1 / -1' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <h3 style={{ fontFamily: 'Syne', fontSize: 14, fontWeight: 700, margin: 0, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'flex', alignItems: 'center', gap: 8 }}>
          <Mail size={14} /> Préparer un email
        </h3>
        <div style={{ display: 'flex', gap: 6 }}>
          {(['intro', 'relance'] as const).map(m => (
            <button key={m} onClick={() => switchMode(m)} style={{
              padding: '4px 12px', borderRadius: 6, border: '1px solid var(--border)',
              background: mode === m ? 'var(--accent)' : 'transparent',
              color: mode === m ? 'white' : 'var(--text-muted)',
              fontSize: 12, fontWeight: 600, cursor: 'pointer',
            }}>
              {m === 'intro' ? '1er contact' : 'Relance'}
            </button>
          ))}
        </div>
      </div>

      {/* Badge type détecté */}
      <div style={{ marginBottom: 14 }}>
        <span style={{ fontSize: 11, color: 'var(--text-dim)', background: 'var(--surface)', padding: '3px 10px', borderRadius: 20, border: '1px solid var(--border)' }}>
          {template.emoji} Template détecté : <strong style={{ color: 'var(--text-muted)' }}>{template.label}</strong>
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Objet</label>
            <button onClick={() => copy(subject, 'subject')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}>
              {copied === 'subject' ? <><Check size={11} color="#22c55e" /> Copié</> : <><Copy size={11} /> Copier</>}
            </button>
          </div>
          <input value={subject} onChange={e => setSubject(e.target.value)} style={{ ...taStyle, resize: 'none' as const }} />
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              <Edit2 size={10} style={{ display: 'inline', marginRight: 4 }} /> Message (modifiable)
            </label>
            <button onClick={() => copy(body, 'body')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}>
              {copied === 'body' ? <><Check size={11} color="#22c55e" /> Copié</> : <><Copy size={11} /> Copier</>}
            </button>
          </div>
          <textarea value={body} onChange={e => setBody(e.target.value)} rows={12} style={taStyle} />
        </div>

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button onClick={() => switchMode(mode)} style={{ padding: '8px 14px', borderRadius: 7, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer' }}>
            Réinitialiser
          </button>
          {prospect.email
            ? <button onClick={openInMail} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 18px', borderRadius: 7, border: 'none', background: 'var(--accent)', color: 'white', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                <Mail size={13} /> Ouvrir dans Mail
              </button>
            : <span style={{ fontSize: 12, color: 'var(--text-muted)', padding: '8px 0' }}>Pas d'email — copie le message manuellement</span>
          }
        </div>
      </div>
    </div>
  )
}

export default function ProspectPage() {
  const { id } = useParams()
  const [prospect, setProspect] = useState<Prospect | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetchProspect(Number(id)).then(setProspect).finally(() => setLoading(false))
  }, [id])

  const handleStatusChange = async (newStatus: string) => {
    if (!prospect) return
    setSaving(true)
    const updated = await updateProspect(prospect.id, { status: newStatus })
    setProspect(updated); setSaving(false); setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 10, color: 'var(--text-muted)' }}><Loader2 size={18} className="animate-spin" /> Chargement...</div>
  if (!prospect) return <div style={{ padding: 32, color: 'var(--text-muted)' }}>Prospect introuvable.</div>

  const scoreColor = prospect.score_label?.includes('haute') ? '#22c55e'
    : prospect.score_label?.includes('moyenne') ? '#eab308'
    : prospect.score_label?.includes('faible') ? '#f97316' : '#64748b'

  return (
    <div style={{ padding: '32px 36px', maxWidth: 900 }}>
      <Link href="/prospects" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-muted)', textDecoration: 'none', marginBottom: 24 }}>
        <ArrowLeft size={14} /> Retour aux prospects
      </Link>

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontFamily: 'Syne', fontSize: 26, fontWeight: 800, margin: 0 }}>{prospect.company_name}</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
            <span style={{ padding: '3px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700, background: `${scoreColor}18`, color: scoreColor, border: `1px solid ${scoreColor}30` }}>{prospect.score_label}</span>
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Score : <strong style={{ color: 'var(--text)' }}>{prospect.lead_score}/100</strong></span>
          </div>
        </div>
        <div style={{ width: 72, height: 72, borderRadius: '50%', background: `conic-gradient(${scoreColor} ${prospect.lead_score * 3.6}deg, var(--border) 0deg)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--card)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Syne', fontWeight: 800, fontSize: 16, color: scoreColor }}>{prospect.lead_score}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 14, fontWeight: 700, margin: '0 0 16px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Coordonnées</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {prospect.email && <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><Mail size={15} color="var(--accent)" /><a href={`mailto:${prospect.email}`} style={{ color: 'var(--accent)', fontSize: 13, textDecoration: 'none' }}>{prospect.email}</a></div>}
            {prospect.phone && <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><Phone size={15} color="var(--text-muted)" /><span style={{ fontSize: 13 }}>{prospect.phone}</span></div>}
            {prospect.website && <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><Globe size={15} color="var(--text-muted)" /><a href={`https://${prospect.website.replace(/^https?:\/\//, '')}`} target="_blank" rel="noreferrer" style={{ fontSize: 13, color: 'var(--text-muted)', textDecoration: 'none' }}>{prospect.website}</a></div>}
            {prospect.address && <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}><MapPin size={15} color="var(--text-muted)" style={{ marginTop: 2 }} /><span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{prospect.address}</span></div>}
            {prospect.city && <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><Building2 size={15} color="var(--text-muted)" /><span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{prospect.city}</span></div>}
          </div>
        </div>

        <div className="card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 14, fontWeight: 700, margin: '0 0 16px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Statut pipeline
            {saving && <Loader2 size={13} className="animate-spin" style={{ marginLeft: 8, display: 'inline' }} />}
            {saved && <Check size={13} color="#22c55e" style={{ marginLeft: 8, display: 'inline' }} />}
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {STATUSES.map(s => (
              <button key={s.value} onClick={() => handleStatusChange(s.value)} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 8, border: 'none', cursor: 'pointer', background: prospect.status === s.value ? `${s.color}18` : 'transparent', color: prospect.status === s.value ? s.color : 'var(--text-muted)', fontSize: 13, fontWeight: prospect.status === s.value ? 600 : 400, textAlign: 'left' }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: prospect.status === s.value ? s.color : 'var(--border)', flexShrink: 0 }} />
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <EmailPanel prospect={prospect} onStatusChange={handleStatusChange} />

        <div className="card" style={{ padding: 24, gridColumn: '1 / -1' }}>
          <h3 style={{ fontFamily: 'Syne', fontSize: 14, fontWeight: 700, margin: '0 0 16px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            <Star size={14} style={{ display: 'inline', marginRight: 6 }} /> Détail du scoring
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {(prospect.score_explanation?.split('\n') || []).map((line, i) => (
              <div key={i} style={{ fontSize: 13, color: i === 0 ? 'var(--text)' : 'var(--text-muted)', fontWeight: i === 0 ? 600 : 400, padding: i === 0 ? '0 0 8px' : 0, borderBottom: i === 0 ? '1px solid var(--border-soft)' : 'none' }}>{line}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}