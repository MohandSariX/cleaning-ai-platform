"""API Email Finder"""
from fastapi import APIRouter
from app.agents.email_finder import find_email_for_prospect, find_emails_batch
import threading

router = APIRouter()


@router.post("/email-finder/prospect/{prospect_id}")
def find_email(prospect_id: int):
    """Cherche l'email d'un prospect spécifique."""
    return find_email_for_prospect(prospect_id)


@router.post("/email-finder/batch")
def find_emails_batch_now(limit: int = 20):
    """Lance la recherche d'emails en batch (arrière-plan)."""
    t = threading.Thread(target=find_emails_batch, args=(limit,), daemon=True)
    t.start()
    return {"status": "started", "message": f"Recherche emails pour {limit} prospects lancée"}


@router.post("/email-finder/batch-sync")
def find_emails_batch_sync(limit: int = 10):
    """Recherche emails en mode synchrone (pour tests)."""
    return find_emails_batch(limit)