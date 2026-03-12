from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from typing import Optional

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/prospects")
def list_prospects(
    db: Session = Depends(get_db),
    city: Optional[str] = None,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    has_email: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = 500
):
    q = db.query(Prospect)
    if city:
        q = q.filter(Prospect.city == city)
    if status:
        q = q.filter(Prospect.status == status)
    if min_score is not None:
        q = q.filter(Prospect.lead_score >= min_score)
    if has_email is True:
        q = q.filter(Prospect.email.isnot(None))
    if has_email is False:
        q = q.filter(Prospect.email.is_(None))
    if search:
        q = q.filter(Prospect.company_name.ilike(f"%{search}%"))
    q = q.order_by(Prospect.lead_score.desc())
    return [_prospect_to_dict(p) for p in q.limit(limit).all()]


@router.get("/prospects/{prospect_id}")
def get_prospect(prospect_id: int, db: Session = Depends(get_db)):
    p = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not p:
        return {"error": "Not found"}
    return _prospect_to_dict(p)


@router.patch("/prospects/{prospect_id}")
def update_prospect(prospect_id: int, data: dict, db: Session = Depends(get_db)):
    p = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not p:
        return {"error": "Not found"}
    for key, val in data.items():
        if key in ["status", "email", "phone"]:
            setattr(p, key, val)
    db.commit()
    return _prospect_to_dict(p)


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total      = db.query(Prospect).count()
    with_email = db.query(Prospect).filter(Prospect.email.isnot(None)).count()
    with_phone = db.query(Prospect).filter(Prospect.phone.isnot(None)).count()
    with_web   = db.query(Prospect).filter(Prospect.website.isnot(None)).count()
    haute      = db.query(Prospect).filter(Prospect.lead_score >= 75).count()
    moyenne    = db.query(Prospect).filter(Prospect.lead_score >= 50, Prospect.lead_score < 75).count()
    faible     = db.query(Prospect).filter(Prospect.lead_score >= 25, Prospect.lead_score < 50).count()
    nulle      = db.query(Prospect).filter(Prospect.lead_score < 25).count()
    avg_score  = db.query(func.avg(Prospect.lead_score)).scalar() or 0
    villes     = (db.query(Prospect.city, func.count(Prospect.id))
                    .group_by(Prospect.city)
                    .order_by(func.count(Prospect.id).desc())
                    .all())
    return {
        "total": total,
        "with_email": with_email,
        "with_phone": with_phone,
        "with_web": with_web,
        "email_rate": round(with_email / total * 100) if total else 0,
        "avg_score": round(float(avg_score), 1),
        "score_distribution": {"haute": haute, "moyenne": moyenne, "faible": faible, "nulle": nulle},
        "by_city": [{"city": c or "Inconnue", "count": n} for c, n in villes]
    }


@router.get("/cities")
def get_cities(db: Session = Depends(get_db)):
    cities = db.query(Prospect.city).distinct().filter(Prospect.city.isnot(None)).all()
    return sorted([c[0] for c in cities])


def _prospect_to_dict(p):
    return {
        "id": p.id,
        "company_name": p.company_name,
        "industry": p.industry,
        "city": p.city,
        "address": p.address,
        "website": p.website,
        "email": p.email,
        "phone": p.phone,
        "lead_score": p.lead_score,
        "score_label": p.score_label,
        "score_explanation": p.score_explanation,
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }