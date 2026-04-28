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
               "scraping", "enrichment", "system", "error", "scheduler", "watchdog",
               "claude_tool", "claude_decision", "claude_briefing", "claude_optimization",
               "claude_escalation", "claude_conversation", "claude_learning"]


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


@router.get("/activity/claude/tools")
def get_claude_tools(days: int = 7, limit: int = 50):
    """Historique des tools Claude exécutés."""
    db = SessionLocal()
    try:
        since = datetime.now() - timedelta(days=days)
        tools = db.query(ActivityLog).filter(
            ActivityLog.event_type == "claude_tool",
            ActivityLog.created_at >= since
        ).order_by(ActivityLog.created_at.desc()).limit(limit).all()

        return {
            "total": len(tools),
            "tools": [{
                "tool_name": t.event_sub,
                "message": t.message,
                "status": t.status,
                "details": json.loads(t.details_json) if t.details_json else None,
                "created_at": t.created_at.isoformat() if t.created_at else None
            } for t in tools]
        }
    finally:
        db.close()


@router.get("/activity/claude/decisions")
def get_claude_decisions(days: int = 7, limit: int = 50):
    """Historique des décisions autonomes de Claude."""
    db = SessionLocal()
    try:
        since = datetime.now() - timedelta(days=days)
        decisions = db.query(ActivityLog).filter(
            ActivityLog.event_type == "claude_decision",
            ActivityLog.created_at >= since
        ).order_by(ActivityLog.created_at.desc()).limit(limit).all()

        return {
            "total": len(decisions),
            "decisions": [{
                "decision_type": d.event_sub,
                "message": d.message,
                "reasoning": d.ia_decision,
                "details": json.loads(d.details_json) if d.details_json else None,
                "created_at": d.created_at.isoformat() if d.created_at else None
            } for d in decisions]
        }
    finally:
        db.close()


@router.get("/activity/claude/escalations")
def get_claude_escalations(days: int = 7):
    """Historique des escalations à Mohand."""
    db = SessionLocal()
    try:
        since = datetime.now() - timedelta(days=days)
        escalations = db.query(ActivityLog).filter(
            ActivityLog.event_type == "claude_escalation",
            ActivityLog.created_at >= since
        ).order_by(ActivityLog.created_at.desc()).all()

        return {
            "total": len(escalations),
            "urgent": sum(1 for e in escalations if e.event_sub == "urgent"),
            "high": sum(1 for e in escalations if e.event_sub == "high"),
            "medium": sum(1 for e in escalations if e.event_sub == "medium"),
            "low": sum(1 for e in escalations if e.event_sub == "low"),
            "escalations": [{
                "priority": e.event_sub,
                "reason": e.message,
                "details": json.loads(e.details_json) if e.details_json else None,
                "created_at": e.created_at.isoformat() if e.created_at else None
            } for e in escalations]
        }
    finally:
        db.close()


@router.get("/activity/claude/stats")
def get_claude_stats(days: int = 7):
    """Statistiques globales Claude."""
    db = SessionLocal()
    try:
        since = datetime.now() - timedelta(days=days)

        # Compter par type d'événement
        tools_executed = db.query(ActivityLog).filter(
            ActivityLog.event_type == "claude_tool",
            ActivityLog.created_at >= since
        ).count()

        decisions_made = db.query(ActivityLog).filter(
            ActivityLog.event_type == "claude_decision",
            ActivityLog.created_at >= since
        ).count()

        escalations = db.query(ActivityLog).filter(
            ActivityLog.event_type == "claude_escalation",
            ActivityLog.created_at >= since
        ).count()

        optimizations = db.query(ActivityLog).filter(
            ActivityLog.event_type == "claude_optimization",
            ActivityLog.created_at >= since
        ).count()

        conversations = db.query(ActivityLog).filter(
            ActivityLog.event_type == "claude_conversation",
            ActivityLog.created_at >= since
        ).count()

        briefings = db.query(ActivityLog).filter(
            ActivityLog.event_type == "claude_briefing",
            ActivityLog.created_at >= since
        ).count()

        # Taux autonomie (décisions / (décisions + escalations))
        total_decisions = decisions_made + escalations
        autonomy_rate = round((decisions_made / total_decisions * 100), 1) if total_decisions > 0 else 0

        return {
            "period_days": days,
            "tools_executed": tools_executed,
            "autonomous_decisions": decisions_made,
            "escalations": escalations,
            "autonomy_rate_pct": autonomy_rate,
            "optimizations_applied": optimizations,
            "conversations": conversations,
            "briefings_sent": briefings
        }
    finally:
        db.close()

