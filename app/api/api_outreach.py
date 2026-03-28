"""
API Outreach — endpoints pour le panneau d'envoi automatique.
"""
from fastapi import APIRouter
from app.agents.email_outreach_agent import get_outreach_stats, run_outreach_batch, run_relances
import threading

router = APIRouter()


@router.get("/outreach/stats")
def outreach_stats():
    """Stats d'envoi pour le dashboard."""
    return get_outreach_stats()


@router.post("/outreach/send-now")
def send_now():
    """Envoi normal — respecte la fenêtre 9h-18h et le quota journalier."""
    t = threading.Thread(target=run_outreach_batch, daemon=True)
    t.start()
    return {"status": "started", "message": "Envoi en cours..."}


@router.post("/outreach/send-test")
def send_test():
    """Mode test uniquement — bypass fenêtre horaire, pour développement."""
    from app.core.database import SessionLocal
    from app.agents.email_outreach_agent import get_prospects_a_contacter, send_one_prospection_email
    db = SessionLocal()
    try:
        prospects = get_prospects_a_contacter(db, limit=1)
        if not prospects:
            return {"status": "empty", "message": "Aucun prospect éligible en attente"}
        prospect = prospects[0]
        success = send_one_prospection_email(prospect, db)
        return {
            "status": "sent" if success else "failed",
            "prospect": prospect.company_name,
            "email": prospect.email,
        }
    finally:
        db.close()


@router.post("/outreach/run-relances")
def run_relances_now():
    """Force les relances maintenant."""
    t = threading.Thread(target=run_relances, daemon=True)
    t.start()
    return {"status": "started", "message": "Relances en cours..."}