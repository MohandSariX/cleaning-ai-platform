from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.chantier import Chantier
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


@router.get("/chantiers")
def list_chantiers(
    db: Session = Depends(get_db),
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
):
    q = db.query(Chantier).options(joinedload(Chantier.client))
    if client_id:
        q = q.filter(Chantier.client_id == client_id)
    if status:
        q = q.filter(Chantier.status == status)
    if type:
        q = q.filter(Chantier.type == type)
    if search:
        q = q.join(Client).filter(Client.company_name.ilike(f"%{search}%"))
    q = q.order_by(Chantier.date_debut.desc().nullslast(), Chantier.created_at.desc())
    return [_chantier_to_dict(c) for c in q.all()]


@router.get("/chantiers/stats/summary")
def chantiers_stats(db: Session = Depends(get_db)):
    total      = db.query(Chantier).count()
    planifies  = db.query(Chantier).filter(Chantier.status == "planifie").count()
    en_cours   = db.query(Chantier).filter(Chantier.status == "en_cours").count()
    termines   = db.query(Chantier).filter(Chantier.status == "termine").count()
    surface    = db.query(func.sum(Chantier.surface_m2)).filter(Chantier.status != "annule").scalar() or 0
    return {
        "total": total,
        "planifies": planifies,
        "en_cours": en_cours,
        "termines": termines,
        "surface_totale": round(float(surface), 0),
    }


@router.get("/chantiers/{chantier_id}")
def get_chantier(chantier_id: int, db: Session = Depends(get_db)):
    c = db.query(Chantier).options(joinedload(Chantier.client)).filter(Chantier.id == chantier_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Chantier introuvable")
    return _chantier_to_dict(c)


@router.post("/chantiers")
def create_chantier(data: dict, db: Session = Depends(get_db)):
    allowed = ["client_id", "devis_id", "titre", "type", "adresse", "ville",
               "surface_m2", "date_debut", "date_fin", "heure_debut",
               "duree_heures", "status", "recurrence", "notes"]
    chantier = Chantier(**{k: v for k, v in data.items() if k in allowed and v is not None})
    db.add(chantier)
    db.commit()
    db.refresh(chantier)
    return _chantier_to_dict(chantier)


@router.patch("/chantiers/{chantier_id}")
def update_chantier(chantier_id: int, data: dict, db: Session = Depends(get_db)):
    c = db.query(Chantier).filter(Chantier.id == chantier_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Chantier introuvable")
    allowed = ["titre", "type", "adresse", "ville", "surface_m2",
               "date_debut", "date_fin", "heure_debut", "duree_heures",
               "status", "recurrence", "notes"]
    for key, val in data.items():
        if key in allowed:
            setattr(c, key, val)
    db.commit()
    return _chantier_to_dict(c)


def _chantier_to_dict(c: Chantier):
    return {
        "id": c.id,
        "client_id": c.client_id,
        "client_nom": c.client.company_name if c.client else None,
        "devis_id": c.devis_id,
        "titre": c.titre,
        "type": c.type,
        "adresse": c.adresse,
        "ville": c.ville,
        "surface_m2": c.surface_m2,
        "date_debut": c.date_debut.isoformat() if c.date_debut else None,
        "date_fin": c.date_fin.isoformat() if c.date_fin else None,
        "heure_debut": c.heure_debut,
        "duree_heures": c.duree_heures,
        "statut": c.status,
        "recurrence": c.recurrence,
        "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }