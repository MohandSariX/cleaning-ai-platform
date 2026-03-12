from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.devis import Devis
from app.models.client import Client
from typing import Optional
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/devis")
def list_devis(
    db: Session = Depends(get_db),
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    q = db.query(Devis).options(joinedload(Devis.client))
    if client_id:
        q = q.filter(Devis.client_id == client_id)
    if status:
        q = q.filter(Devis.status == status)
    if search:
        q = q.join(Client).filter(Client.company_name.ilike(f"%{search}%"))
    q = q.order_by(Devis.created_at.desc())
    return [_devis_to_dict(d) for d in q.all()]


@router.get("/devis/stats/summary")
def devis_stats(db: Session = Depends(get_db)):
    total       = db.query(Devis).count()
    envoyes     = db.query(Devis).filter(Devis.status == "envoye").count()
    acceptes    = db.query(Devis).filter(Devis.status == "accepte").count()
    refuses     = db.query(Devis).filter(Devis.status == "refuse").count()
    ca_pipeline = db.query(func.sum(Devis.montant_ht)).filter(Devis.status.in_(["envoye", "accepte"])).scalar() or 0
    ca_signe    = db.query(func.sum(Devis.montant_ht)).filter(Devis.status == "accepte").scalar() or 0
    taux_conv   = round(acceptes / (acceptes + refuses) * 100) if (acceptes + refuses) > 0 else 0
    return {
        "total": total, "envoyes": envoyes, "acceptes": acceptes, "refuses": refuses,
        "ca_pipeline": round(float(ca_pipeline), 2),
        "ca_signe": round(float(ca_signe), 2),
        "taux_conversion": taux_conv,
    }


@router.get("/devis/{devis_id}")
def get_devis(devis_id: int, db: Session = Depends(get_db)):
    d = db.query(Devis).options(joinedload(Devis.client)).filter(Devis.id == devis_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    return _devis_to_dict(d)


@router.post("/devis")
def create_devis(data: dict, db: Session = Depends(get_db)):
    # Auto-numérotation : DEV-2024-001
    year  = datetime.now().year
    count = db.query(Devis).count() + 1
    numero = f"DEV-{year}-{count:03d}"

    allowed = ["client_id", "service_type", "description", "surface_m2",
               "frequence", "montant_ht", "tva_pct", "status", "notes"]
    devis = Devis(numero=numero, **{k: v for k, v in data.items() if k in allowed})
    db.add(devis)
    db.commit()
    db.refresh(devis)
    return _devis_to_dict(devis)


@router.patch("/devis/{devis_id}")
def update_devis(devis_id: int, data: dict, db: Session = Depends(get_db)):
    d = db.query(Devis).filter(Devis.id == devis_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    allowed = ["service_type", "description", "surface_m2", "frequence",
               "montant_ht", "tva_pct", "status", "notes"]
    for key, val in data.items():
        if key in allowed:
            setattr(d, key, val)
    if data.get("status") == "envoye" and not d.sent_at:
        d.sent_at = datetime.now()
    if data.get("status") in ("accepte", "refuse") and not d.responded_at:
        d.responded_at = datetime.now()
    db.commit()
    return _devis_to_dict(d)


def _devis_to_dict(d: Devis):
    tva    = d.tva_pct or 20.0
    ttc    = round(d.montant_ht * (1 + tva / 100), 2) if d.montant_ht else 0
    return {
        "id": d.id,
        "numero": d.numero,
        "client_id": d.client_id,
        "client_name": d.client.company_name if d.client else None,
        "service_type": d.service_type,
        "description": d.description,
        "surface_m2": d.surface_m2,
        "frequence": d.frequence,
        "montant_ht": d.montant_ht,
        "tva_pct": tva,
        "montant_ttc": ttc,
        "status": d.status,
        "notes": d.notes,
        "created_at":    d.created_at.isoformat()    if d.created_at    else None,
        "sent_at":       d.sent_at.isoformat()       if d.sent_at       else None,
        "responded_at":  d.responded_at.isoformat()  if d.responded_at  else None,
    }


# ── Export PDF ──────────────────────────────────────────────

from fastapi.responses import StreamingResponse
from app.utils.pdf_generator import generate_devis_pdf
from io import BytesIO

@router.get("/devis/{devis_id}/pdf")
def download_devis_pdf(devis_id: int, db: Session = Depends(get_db)):
    d = db.query(Devis).options(joinedload(Devis.client)).filter(Devis.id == devis_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Devis introuvable")

    devis_data = _devis_to_dict(d)
    client_data = {
        "company_name": d.client.company_name if d.client else "",
        "contact_name": d.client.contact_name if d.client else "",
        "address": d.client.address if d.client else "",
        "city": d.client.city if d.client else "",
        "email": d.client.email if d.client else "",
        "phone": d.client.phone if d.client else "",
    }

    pdf_bytes = generate_devis_pdf(devis_data, client_data)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={d.numero}.pdf"}
    )