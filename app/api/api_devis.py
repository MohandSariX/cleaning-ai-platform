from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, extract
from app.core.database import SessionLocal
from app.models.devis import Devis
from app.models.client import Client
from typing import Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

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


# ── Analytics avancés ────────────────────────────────────────

@router.get("/devis/analytics/overview")
def devis_analytics_overview(
    db: Session = Depends(get_db),
    days: int = 30
):
    """Analytics globaux des devis sur N derniers jours."""
    cutoff_date = datetime.now() - timedelta(days=days)

    # Devis de la période
    devis_period = db.query(Devis).filter(Devis.created_at >= cutoff_date).all()

    # Stats globales
    total = len(devis_period)
    envoyes = len([d for d in devis_period if d.status == "envoye"])
    acceptes = len([d for d in devis_period if d.status == "accepte"])
    refuses = len([d for d in devis_period if d.status == "refuse"])

    # CA
    ca_total = sum([d.montant_ht for d in devis_period if d.montant_ht])
    ca_accepte = sum([d.montant_ht for d in devis_period if d.status == "accepte" and d.montant_ht])
    ca_pipeline = sum([d.montant_ht for d in devis_period if d.status == "envoye" and d.montant_ht])

    # Taux
    taux_envoi = round(envoyes / total * 100, 1) if total > 0 else 0
    taux_acceptation = round(acceptes / envoyes * 100, 1) if envoyes > 0 else 0
    taux_refus = round(refuses / envoyes * 100, 1) if envoyes > 0 else 0

    # Montant moyen
    montant_moyen = round(ca_total / total, 2) if total > 0 else 0
    montant_moyen_accepte = round(ca_accepte / acceptes, 2) if acceptes > 0 else 0

    return {
        "period_days": days,
        "total": total,
        "envoyes": envoyes,
        "acceptes": acceptes,
        "refuses": refuses,
        "ca_total": round(ca_total, 2),
        "ca_accepte": round(ca_accepte, 2),
        "ca_pipeline": round(ca_pipeline, 2),
        "taux_envoi": taux_envoi,
        "taux_acceptation": taux_acceptation,
        "taux_refus": taux_refus,
        "montant_moyen": montant_moyen,
        "montant_moyen_accepte": montant_moyen_accepte,
    }


@router.get("/devis/analytics/by-type")
def devis_analytics_by_type(db: Session = Depends(get_db), days: int = 90):
    """Analytics par type de prestation."""
    cutoff_date = datetime.now() - timedelta(days=days)

    devis_period = db.query(Devis).filter(Devis.created_at >= cutoff_date).all()

    # Grouper par type
    by_type = defaultdict(lambda: {
        "total": 0, "envoyes": 0, "acceptes": 0, "refuses": 0,
        "ca_total": 0, "ca_accepte": 0
    })

    for d in devis_period:
        service_type = d.service_type or "non_specifie"
        by_type[service_type]["total"] += 1
        if d.status == "envoye":
            by_type[service_type]["envoyes"] += 1
        if d.status == "accepte":
            by_type[service_type]["acceptes"] += 1
            by_type[service_type]["ca_accepte"] += d.montant_ht or 0
        if d.status == "refuse":
            by_type[service_type]["refuses"] += 1
        by_type[service_type]["ca_total"] += d.montant_ht or 0

    # Calculer taux pour chaque type
    result = []
    for service_type, stats in by_type.items():
        taux_acceptation = round(stats["acceptes"] / stats["envoyes"] * 100, 1) if stats["envoyes"] > 0 else 0
        result.append({
            "service_type": service_type,
            "total": stats["total"],
            "envoyes": stats["envoyes"],
            "acceptes": stats["acceptes"],
            "refuses": stats["refuses"],
            "ca_total": round(stats["ca_total"], 2),
            "ca_accepte": round(stats["ca_accepte"], 2),
            "taux_acceptation": taux_acceptation,
            "montant_moyen": round(stats["ca_total"] / stats["total"], 2) if stats["total"] > 0 else 0,
        })

    # Trier par CA accepté décroissant
    result.sort(key=lambda x: x["ca_accepte"], reverse=True)

    return result


@router.get("/devis/analytics/by-montant")
def devis_analytics_by_montant(db: Session = Depends(get_db), days: int = 90):
    """Analytics par tranche de montant."""
    cutoff_date = datetime.now() - timedelta(days=days)

    devis_period = db.query(Devis).filter(Devis.created_at >= cutoff_date).all()

    # Tranches de montant
    tranches = [
        {"label": "< 1k€", "min": 0, "max": 1000},
        {"label": "1k-3k€", "min": 1000, "max": 3000},
        {"label": "3k-5k€", "min": 3000, "max": 5000},
        {"label": "5k-10k€", "min": 5000, "max": 10000},
        {"label": "> 10k€", "min": 10000, "max": float('inf')},
    ]

    result = []
    for tranche in tranches:
        devis_tranche = [
            d for d in devis_period
            if d.montant_ht and tranche["min"] <= d.montant_ht < tranche["max"]
        ]

        total = len(devis_tranche)
        envoyes = len([d for d in devis_tranche if d.status == "envoye"])
        acceptes = len([d for d in devis_tranche if d.status == "accepte"])

        taux_acceptation = round(acceptes / envoyes * 100, 1) if envoyes > 0 else 0

        result.append({
            "tranche": tranche["label"],
            "total": total,
            "envoyes": envoyes,
            "acceptes": acceptes,
            "taux_acceptation": taux_acceptation,
        })

    return result


@router.get("/devis/analytics/evolution")
def devis_analytics_evolution(db: Session = Depends(get_db), days: int = 30):
    """Évolution quotidienne des devis."""
    cutoff_date = datetime.now() - timedelta(days=days)

    devis_period = db.query(Devis).filter(Devis.created_at >= cutoff_date).all()

    # Grouper par jour
    by_day = defaultdict(lambda: {"created": 0, "envoyes": 0, "acceptes": 0, "ca": 0})

    for d in devis_period:
        day = d.created_at.date().isoformat()
        by_day[day]["created"] += 1
        if d.sent_at and d.sent_at >= cutoff_date:
            day_sent = d.sent_at.date().isoformat()
            by_day[day_sent]["envoyes"] += 1
        if d.status == "accepte" and d.responded_at and d.responded_at >= cutoff_date:
            day_accepted = d.responded_at.date().isoformat()
            by_day[day_accepted]["acceptes"] += 1
            by_day[day_accepted]["ca"] += d.montant_ht or 0

    # Convertir en liste triée
    result = []
    for day in sorted(by_day.keys()):
        result.append({
            "date": day,
            "created": by_day[day]["created"],
            "envoyes": by_day[day]["envoyes"],
            "acceptes": by_day[day]["acceptes"],
            "ca": round(by_day[day]["ca"], 2),
        })

    return result


@router.get("/devis/analytics/top-clients")
def devis_analytics_top_clients(db: Session = Depends(get_db), limit: int = 10):
    """Top clients par CA devis acceptés."""
    # Tous les devis acceptés
    accepted_devis = db.query(Devis).filter(Devis.status == "accepte").all()

    # Grouper par client
    by_client = defaultdict(lambda: {"ca": 0, "count": 0, "company_name": ""})

    for d in accepted_devis:
        if d.client:
            by_client[d.client_id]["ca"] += d.montant_ht or 0
            by_client[d.client_id]["count"] += 1
            by_client[d.client_id]["company_name"] = d.client.company_name or f"Client {d.client_id}"

    # Convertir et trier
    result = [
        {
            "client_id": client_id,
            "company_name": stats["company_name"],
            "devis_count": stats["count"],
            "ca_total": round(stats["ca"], 2),
        }
        for client_id, stats in by_client.items()
    ]

    result.sort(key=lambda x: x["ca_total"], reverse=True)

    return result[:limit]


# ── Signature électronique ──────────────────────────────────

@router.post("/devis/{devis_id}/sign")
def sign_devis(devis_id: int, data: dict, db: Session = Depends(get_db)):
    """Signe un devis avec signature électronique.

    Body: {
        "signature_data": "data:image/png;base64,...",
        "signed_by": "Jean Dupont"
    }
    """
    d = db.query(Devis).filter(Devis.id == devis_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Devis introuvable")

    d.signature_data = data.get("signature_data")
    d.signed_by = data.get("signed_by")
    d.signed_at = datetime.now()
    d.status = "accepte"
    d.responded_at = datetime.now()

    db.commit()

    return {
        "status": "signed",
        "devis_id": d.id,
        "signed_at": d.signed_at.isoformat(),
        "signed_by": d.signed_by
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