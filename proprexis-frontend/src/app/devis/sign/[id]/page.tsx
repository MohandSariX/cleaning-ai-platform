'use client'
import { useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Check, X, Loader2 } from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function SignDevisPage() {
  const params = useParams()
  const router = useRouter()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [signedBy, setSignedBy] = useState('')
  const [loading, setLoading] = useState(false)
  const [devis, setDevis] = useState<any>(null)

  useEffect(() => {
    // Charger les infos du devis
    fetch(`${API}/api/devis/${params.id}`)
      .then(res => res.json())
      .then(setDevis)
  }, [params.id])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Fond blanc
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    const startDrawing = (e: MouseEvent | TouchEvent) => {
      setIsDrawing(true)
      const coords = getCoordinates(e)
      ctx.beginPath()
      ctx.moveTo(coords.x, coords.y)
    }

    const draw = (e: MouseEvent | TouchEvent) => {
      if (!isDrawing) return
      const coords = getCoordinates(e)
      ctx.lineTo(coords.x, coords.y)
      ctx.strokeStyle = '#000'
      ctx.lineWidth = 2
      ctx.lineCap = 'round'
      ctx.stroke()
    }

    const stopDrawing = () => {
      setIsDrawing(false)
      ctx.closePath()
    }

    const getCoordinates = (e: MouseEvent | TouchEvent) => {
      const rect = canvas.getBoundingClientRect()
      if (e instanceof MouseEvent) {
        return {
          x: e.clientX - rect.left,
          y: e.clientY - rect.top
        }
      } else {
        return {
          x: e.touches[0].clientX - rect.left,
          y: e.touches[0].clientY - rect.top
        }
      }
    }

    canvas.addEventListener('mousedown', startDrawing)
    canvas.addEventListener('mousemove', draw)
    canvas.addEventListener('mouseup', stopDrawing)
    canvas.addEventListener('mouseleave', stopDrawing)

    canvas.addEventListener('touchstart', startDrawing)
    canvas.addEventListener('touchmove', draw)
    canvas.addEventListener('touchend', stopDrawing)

    return () => {
      canvas.removeEventListener('mousedown', startDrawing)
      canvas.removeEventListener('mousemove', draw)
      canvas.removeEventListener('mouseup', stopDrawing)
      canvas.removeEventListener('mouseleave', stopDrawing)
      canvas.removeEventListener('touchstart', startDrawing)
      canvas.removeEventListener('touchmove', draw)
      canvas.removeEventListener('touchend', stopDrawing)
    }
  }, [isDrawing])

  const clearSignature = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
  }

  const handleSign = async () => {
    if (!signedBy.trim()) {
      alert('Veuillez entrer votre nom')
      return
    }

    const canvas = canvasRef.current
    if (!canvas) return

    const signatureData = canvas.toDataURL('image/png')

    setLoading(true)
    try {
      await fetch(`${API}/api/devis/${params.id}/sign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signature_data: signatureData,
          signed_by: signedBy
        })
      })

      alert('Devis signé avec succès!')
      router.push('/devis')
    } catch (error) {
      alert('Erreur lors de la signature')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '32px 36px', maxWidth: 800, margin: '0 auto' }}>
      <div className="card" style={{ padding: '32px' }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
          Signature électronique
        </h1>
        {devis && (
          <p style={{ color: 'var(--text-muted)', marginBottom: 28, fontSize: 14 }}>
            Devis {devis.numero} — {devis.client_name}
          </p>
        )}

        <div style={{ marginBottom: 24 }}>
          <label style={{
            display: 'block',
            fontSize: 13,
            fontWeight: 600,
            marginBottom: 8,
            color: 'var(--text-muted)'
          }}>
            Nom du signataire *
          </label>
          <input
            type="text"
            value={signedBy}
            onChange={(e) => setSignedBy(e.target.value)}
            placeholder="Jean Dupont"
            style={{
              width: '100%',
              padding: '12px',
              borderRadius: 8,
              border: '1px solid var(--border)',
              background: 'var(--surface)',
              color: 'var(--text)',
              fontSize: 14
            }}
          />
        </div>

        <div style={{ marginBottom: 24 }}>
          <label style={{
            display: 'block',
            fontSize: 13,
            fontWeight: 600,
            marginBottom: 8,
            color: 'var(--text-muted)'
          }}>
            Signature *
          </label>
          <div style={{
            border: '2px dashed var(--border)',
            borderRadius: 12,
            padding: 4,
            background: '#fff'
          }}>
            <canvas
              ref={canvasRef}
              width={700}
              height={200}
              style={{
                display: 'block',
                cursor: 'crosshair',
                touchAction: 'none'
              }}
            />
          </div>
          <button
            onClick={clearSignature}
            style={{
              marginTop: 12,
              padding: '8px 16px',
              borderRadius: 8,
              border: '1px solid var(--border)',
              background: 'transparent',
              color: 'var(--text-muted)',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Effacer
          </button>
        </div>

        <div style={{
          padding: '16px',
          background: 'var(--surface)',
          borderRadius: 8,
          marginBottom: 24,
          fontSize: 12,
          color: 'var(--text-muted)',
          lineHeight: 1.6
        }}>
          En signant ce document, vous acceptez les conditions générales de vente et vous engagez à payer le montant indiqué selon les modalités convenues.
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={handleSign}
            disabled={loading || !signedBy.trim()}
            style={{
              flex: 1,
              padding: '14px',
              borderRadius: 8,
              border: 'none',
              background: loading || !signedBy.trim() ? '#ccc' : '#22c55e',
              color: '#fff',
              fontSize: 14,
              fontWeight: 600,
              cursor: loading || !signedBy.trim() ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8
            }}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Signature en cours...
              </>
            ) : (
              <>
                <Check size={16} />
                Signer le devis
              </>
            )}
          </button>
          <button
            onClick={() => router.back()}
            style={{
              padding: '14px 24px',
              borderRadius: 8,
              border: '1px solid var(--border)',
              background: 'transparent',
              color: 'var(--text)',
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            <X size={16} />
            Annuler
          </button>
        </div>
      </div>
    </div>
  )
}
