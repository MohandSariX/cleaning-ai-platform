from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.facture import Facture
from app.models.client import Client
from typing import Optional
from datetime import datetime, date

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/factures")
def list_factures(
    db: Session = Depends(get_db),
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    q = db.query(Facture).options(joinedload(Facture.client))
    if client_id:
        q = q.filter(Facture.client_id == client_id)
    if status:
        q = q.filter(Facture.status == status)
    if search:
        q = q.join(Client).filter(Client.company_name.ilike(f"%{search}%"))
    q = q.order_by(Facture.created_at.desc())
    return [_facture_to_dict(f) for f in q.all()]


@router.get("/factures/stats/summary")
def factures_stats(db: Session = Depends(get_db)):
    total      = db.query(Facture).count()
    payees     = db.query(Facture).filter(Facture.status == "payee").count()
    en_attente = db.query(Facture).filter(Facture.status == "envoyee").count()
    en_retard  = db.query(Facture).filter(Facture.status == "en_retard").count()

    ca_encaisse  = db.query(func.sum(Facture.montant_ht)).filter(Facture.status == "payee").scalar() or 0
    ca_en_attente = db.query(func.sum(Facture.montant_ht)).filter(Facture.status.in_(["envoyee", "en_retard"])).scalar() or 0

    return {
        "total": total,
        "payees": payees,
        "en_attente": en_attente,
        "en_retard": en_retard,
        "ca_encaisse": round(float(ca_encaisse), 2),
        "ca_en_attente": round(float(ca_en_attente), 2),
    }


@router.get("/factures/{facture_id}")
def get_facture(facture_id: int, db: Session = Depends(get_db)):
    f = db.query(Facture).options(joinedload(Facture.client)).filter(Facture.id == facture_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    return _facture_to_dict(f)


@router.post("/factures")
def create_facture(data: dict, db: Session = Depends(get_db)):
    year  = datetime.now().year
    count = db.query(Facture).count() + 1
    numero = f"FAC-{year}-{count:03d}"

    allowed = ["client_id", "chantier_id", "montant_ht", "tva_pct",
               "description", "notes", "date_emission", "date_echeance", "status"]
    facture = Facture(numero=numero, **{k: v for k, v in data.items() if k in allowed and v is not None})
    db.add(facture)
    db.commit()
    db.refresh(facture)
    return _facture_to_dict(facture)


@router.patch("/factures/{facture_id}")
def update_facture(facture_id: int, data: dict, db: Session = Depends(get_db)):
    f = db.query(Facture).filter(Facture.id == facture_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    allowed = ["montant_ht", "tva_pct", "description", "notes",
               "date_emission", "date_echeance", "date_paiement", "status"]
    for key, val in data.items():
        if key in allowed:
            setattr(f, key, val)
    if data.get("status") == "payee" and not f.date_paiement:
        f.date_paiement = date.today()
    db.commit()
    return _facture_to_dict(f)


def _facture_to_dict(f: Facture):
    tva = f.tva_pct or 20.0
    ttc = round(f.montant_ht * (1 + tva / 100), 2) if f.montant_ht else 0
    return {
        "id": f.id,
        "numero": f.numero,
        "client_id": f.client_id,
        "client_name": f.client.company_name if f.client else None,
        "chantier_id": f.chantier_id,
        "montant_ht": f.montant_ht,
        "tva_pct": tva,
        "montant_ttc": ttc,
        "description": f.description,
        "notes": f.notes,
        "status": f.status,
        "date_emission": f.date_emission.isoformat() if f.date_emission else None,
        "date_echeance": f.date_echeance.isoformat() if f.date_echeance else None,
        "date_paiement": f.date_paiement.isoformat() if f.date_paiement else None,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


# ── Export PDF ──────────────────────────────────────────────

from fastapi.responses import StreamingResponse
from app.utils.pdf_facture import generate_facture_pdf
from io import BytesIO as BytesIO2

@router.get("/factures/{facture_id}/pdf")
def download_facture_pdf(facture_id: int, db: Session = Depends(get_db)):
    f = db.query(Facture).options(joinedload(Facture.client)).filter(Facture.id == facture_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    facture_data = _facture_to_dict(f)
    client_data = {
        "company_name": f.client.company_name if f.client else "",
        "contact_name": f.client.contact_name if f.client else "",
        "address": f.client.address if f.client else "",
        "city": f.client.city if f.client else "",
        "email": f.client.email if f.client else "",
        "phone": f.client.phone if f.client else "",
    }

    pdf_bytes = generate_facture_pdf(facture_data, client_data)

    return StreamingResponse(
        BytesIO2(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={f.numero}.pdf"}
    )