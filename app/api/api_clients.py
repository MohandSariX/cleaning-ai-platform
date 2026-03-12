from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.client import Client
from app.models.chantier import Chantier
from app.models.facture import Facture
from app.models.devis import Devis
from typing import Optional

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/clients")
def list_clients(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    q = db.query(Client)
    if status:
        q = q.filter(Client.status == status)
    if search:
        q = q.filter(Client.company_name.ilike(f"%{search}%"))
    q = q.order_by(Client.created_at.desc())
    return [_client_to_dict(c) for c in q.all()]


@router.get("/clients/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return _client_to_dict(c, full=True)


@router.post("/clients")
def create_client(data: dict, db: Session = Depends(get_db)):
    client = Client(**{k: v for k, v in data.items() if hasattr(Client, k)})
    db.add(client)
    db.commit()
    db.refresh(client)
    return _client_to_dict(client)


@router.patch("/clients/{client_id}")
def update_client(client_id: int, data: dict, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable")
    allowed = ["company_name", "contact_name", "email", "phone",
               "address", "city", "website", "siret",
               "service_type", "status", "notes"]
    for key, val in data.items():
        if key in allowed:
            setattr(c, key, val)
    db.commit()
    return _client_to_dict(c)


@router.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable")
    db.delete(c)
    db.commit()
    return {"deleted": True}


@router.get("/clients/stats/summary")
def clients_stats(db: Session = Depends(get_db)):
    total   = db.query(Client).count()
    actifs  = db.query(Client).filter(Client.status == "actif").count()
    ca_total = db.query(func.sum(Facture.montant_ht))\
                 .filter(Facture.status == "payee").scalar() or 0
    devis_en_attente = db.query(Devis).filter(Devis.status == "envoye").count()
    chantiers_actifs = db.query(Chantier).filter(Chantier.status == "en_cours").count()
    return {
        "total": total,
        "actifs": actifs,
        "ca_total_ht": round(float(ca_total), 2),
        "devis_en_attente": devis_en_attente,
        "chantiers_actifs": chantiers_actifs,
    }


def _client_to_dict(c: Client, full: bool = False):
    base = {
        "id": c.id,
        "prospect_id": c.prospect_id,
        "company_name": c.company_name,
        "contact_name": c.contact_name,
        "email": c.email,
        "phone": c.phone,
        "address": c.address,
        "city": c.city,
        "website": c.website,
        "siret": c.siret,
        "service_type": c.service_type,
        "status": c.status,
        "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "signed_at": c.signed_at.isoformat() if c.signed_at else None,
    }
    if full:
        base["nb_chantiers"] = len(c.chantiers)
        base["nb_devis"]     = len(c.devis)
        base["nb_factures"]  = len(c.factures)
        base["ca_total"]     = sum(f.montant_ht for f in c.factures if f.status == "payee")
    return base