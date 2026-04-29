"""
API Dashboard — Statistiques et métriques pour monitoring
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.models.email_log import EmailLog
from app.models.devis import Devis
from app.models.activity_log import ActivityLog


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Retourne les statistiques du jour pour le dashboard.

    Returns:
        - emails_sent_today: Nombre d'emails envoyés aujourd'hui
        - devis_generated_today: Nombre de devis générés aujourd'hui
        - devis_total_today: Montant total des devis du jour
        - replies_today: Nombre de réponses reçues aujourd'hui
        - pipeline: Répartition des prospects par statut
        - top_prospects: Top 10 prospects avec score >80
        - recent_activities: 20 dernières activités
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Emails envoyés aujourd'hui
    emails_today = db.query(func.count(EmailLog.id)).filter(
        EmailLog.sent_at >= today,
        EmailLog.status == "sent"
    ).scalar() or 0

    # Devis générés aujourd'hui
    devis_today = db.query(Devis).filter(Devis.created_at >= today).all()
    devis_count = len(devis_today)
    devis_total = sum(d.montant_ttc or 0 for d in devis_today)

    # Réponses reçues aujourd'hui (prospects qui sont passés à "replied" aujourd'hui)
    replies_today = db.query(func.count(Prospect.id)).filter(
        and_(
            Prospect.status == "replied",
            Prospect.updated_at >= today
        )
    ).scalar() or 0

    # Pipeline : répartition par statut
    pipeline = db.query(
        Prospect.status,
        func.count(Prospect.id).label('count')
    ).group_by(Prospect.status).all()

    pipeline_dict = {status: count for status, count in pipeline}

    # Top prospects (score > 80)
    top_prospects = db.query(Prospect).filter(
        Prospect.lead_score >= 80,
        Prospect.status.in_(["new", "scored", "contacted"])
    ).order_by(Prospect.lead_score.desc()).limit(10).all()

    # Activités récentes
    recent_activities = db.query(ActivityLog).order_by(
        ActivityLog.created_at.desc()
    ).limit(20).all()

    return {
        "today": {
            "emails_sent": emails_today,
            "devis_generated": devis_count,
            "devis_total_ht": round(devis_total / 1.20, 2) if devis_total else 0,
            "devis_total_ttc": round(devis_total, 2),
            "replies_received": replies_today,
        },
        "pipeline": {
            "new": pipeline_dict.get("new", 0),
            "scored": pipeline_dict.get("scored", 0),
            "contacted": pipeline_dict.get("contacted", 0),
            "replied": pipeline_dict.get("replied", 0),
            "qualified": pipeline_dict.get("qualified", 0),
            "quoted": pipeline_dict.get("quoted", 0),
            "won": pipeline_dict.get("won", 0),
            "lost": pipeline_dict.get("lost", 0),
        },
        "top_prospects": [
            {
                "id": p.id,
                "company_name": p.company_name,
                "city": p.city,
                "lead_score": p.lead_score,
                "score_label": p.score_label,
                "source": "Permis" if "Permis" in (p.score_explanation or "") else
                         "DVF" if "DVF" in (p.score_explanation or "") else
                         "Pages Jaunes"
            }
            for p in top_prospects
        ],
        "recent_activities": [
            {
                "id": a.id,
                "timestamp": a.created_at.isoformat() if a.created_at else None,
                "event_type": a.event_type,
                "message": a.message,
                "status": a.status
            }
            for a in recent_activities
        ]
    }


@router.get("/claude-summary")
def get_claude_summary(db: Session = Depends(get_db)):
    """
    Résumé de l'activité de Claude (format briefing).
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)

    # Activités hier
    activities_yesterday = db.query(ActivityLog).filter(
        and_(
            ActivityLog.created_at >= yesterday,
            ActivityLog.created_at < today
        )
    ).all()

    # Activités aujourd'hui
    activities_today = db.query(ActivityLog).filter(
        ActivityLog.created_at >= today
    ).all()

    # Compter par type d'événement
    def count_by_event(activities, event_type):
        return len([a for a in activities if a.event_type == event_type])

    yesterday_summary = {
        "emails_sent": count_by_event(activities_yesterday, "email_sent"),
        "prospects_enriched": count_by_event(activities_yesterday, "enrichment"),
        "devis_generated": count_by_event(activities_yesterday, "devis_sent"),
        "replies_received": count_by_event(activities_yesterday, "email_received"),
    }

    today_summary = {
        "emails_sent": count_by_event(activities_today, "email_sent"),
        "prospects_enriched": count_by_event(activities_today, "enrichment"),
        "devis_generated": count_by_event(activities_today, "devis_sent"),
        "replies_received": count_by_event(activities_today, "email_received"),
    }

    return {
        "yesterday": yesterday_summary,
        "today": today_summary,
        "alerts": []  # TODO: Implémenter alertes (budget dépassé, quota emails, etc.)
    }


@router.get("/pipeline-chart")
def get_pipeline_chart(db: Session = Depends(get_db)):
    """
    Données pour graphique pipeline (évolution sur 7 jours).
    """
    days = []
    for i in range(6, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        # Compter les prospects créés ce jour
        new_count = db.query(func.count(Prospect.id)).filter(
            and_(
                Prospect.created_at >= day_start,
                Prospect.created_at < day_end
            )
        ).scalar() or 0

        # Compter les prospects contactés ce jour
        contacted_count = db.query(func.count(Prospect.id)).filter(
            and_(
                Prospect.status == "contacted",
                Prospect.updated_at >= day_start,
                Prospect.updated_at < day_end
            )
        ).scalar() or 0

        # Compter les réponses reçues ce jour
        replied_count = db.query(func.count(Prospect.id)).filter(
            and_(
                Prospect.status == "replied",
                Prospect.updated_at >= day_start,
                Prospect.updated_at < day_end
            )
        ).scalar() or 0

        days.append({
            "date": day_start.strftime("%d/%m"),
            "new": new_count,
            "contacted": contacted_count,
            "replied": replied_count,
        })

    return {"days": days}
