"""
API Activity — endpoints pour le journal d'activité.
"""
from fastapi import APIRouter, Query
from app.core.database import SessionLocal
from app.models.activity_log import ActivityLog
from app.agents.activity_logger import get_daily_summary
from datetime import date, datetime, timedelta
import json

router = APIRouter()

EVENT_TYPES = ["email_sent", "email_received", "qualification", "devis_sent",
               "scraping", "enrichment", "system", "error", "scheduler", "watchdog"]


@router.get("/activity/logs")
def get_logs(
    limit: int = 50,
    offset: int = 0,
    event_type: str = None,
    status: str = None,
    prospect_id: int = None,
    days: int = 7,
):
    """Retourne les logs d'activité filtrés."""
    db = SessionLocal()
    try:
        query = db.query(ActivityLog)

        # Filtres
        if event_type:
            query = query.filter(ActivityLog.event_type == event_type)
        if status:
            query = query.filter(ActivityLog.status == status)
        if prospect_id:
            query = query.filter(ActivityLog.prospect_id == prospect_id)
        if days:
            since = datetime.now() - timedelta(days=days)
            query = query.filter(ActivityLog.created_at >= since)

        total = query.count()
        logs = query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "logs": [{
                "id": l.id,
                "event_type": l.event_type,
                "event_sub": l.event_sub,
                "message": l.message,
                "status": l.status,
                "prospect_id": l.prospect_id,
                "prospect_name": l.prospect.company_name if l.prospect else None,
                "metric_value": l.metric_value,
                "ia_decision": l.ia_decision,
                "details": json.loads(l.details_json) if l.details_json else None,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            } for l in logs]
        }
    finally:
        db.close()


@router.get("/activity/summary")
def get_summary(days: int = 7):
    """Résumé des N derniers jours."""
    summaries = []
    for i in range(days):
        d = date.today() - timedelta(days=i)
        summaries.append(get_daily_summary(d))
    return summaries


@router.get("/activity/summary/today")
def get_today_summary():
    """Résumé d'aujourd'hui."""
    return get_daily_summary(date.today())


@router.get("/activity/health")
def get_system_health():
    """Santé du système — dernière exécution de chaque job."""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        health = {}
        jobs = ["scraping", "enrichment", "email_sent", "email_received",
                "qualification", "scheduler", "system"]

        for job in jobs:
            last = db.query(ActivityLog).filter(
                ActivityLog.event_type == job
            ).order_by(ActivityLog.created_at.desc()).first()

            health[job] = {
                "last_run": last.created_at.isoformat() if last else None,
                "last_status": last.status if last else None,
                "last_message": last.message if last else None,
            }

        # Stats erreurs dernières 24h
        since = datetime.now() - timedelta(hours=24)
        errors_24h = db.query(ActivityLog).filter(
            ActivityLog.status == "error",
            ActivityLog.created_at >= since,
        ).count()

        health["errors_last_24h"] = errors_24h

        return health
    finally:
        db.close()


@router.get("/activity/stats")
def get_stats():
    """Stats globales pour les métriques dashboard."""
    db = SessionLocal()
    try:
        since_week = datetime.now() - timedelta(days=7)
        logs_week = db.query(ActivityLog).filter(
            ActivityLog.created_at >= since_week
        ).all()

        emails_sent = sum(1 for l in logs_week if l.event_type == "email_sent")
        emails_received = sum(1 for l in logs_week if l.event_type == "email_received")
        devis_envoyes = sum(1 for l in logs_week if l.event_type == "devis_sent")
        ca_pipeline = sum(l.metric_value or 0 for l in logs_week if l.event_type == "devis_sent")
        nouveaux = sum(l.metric_value or 0 for l in logs_week if l.event_type == "scraping")
        signatures = sum(1 for l in logs_week if l.event_type == "qualification" and l.event_sub == "signed")

        taux_reponse = round((emails_received / emails_sent * 100), 1) if emails_sent > 0 else 0

        return {
            "periode": "7 derniers jours",
            "emails_envoyes": emails_sent,
            "emails_recus": emails_received,
            "taux_reponse_pct": taux_reponse,
            "devis_envoyes": devis_envoyes,
            "ca_pipeline": round(ca_pipeline, 2),
            "nouveaux_prospects": int(nouveaux),
            "signatures": signatures,
        }
    finally:
        db.close()