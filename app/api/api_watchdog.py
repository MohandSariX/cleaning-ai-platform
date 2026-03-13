"""
API Watchdog — endpoints pour le rapport quotidien.
"""
from fastapi import APIRouter
from app.agents.watchdog import rapport_status, run_watchdog
import threading

router = APIRouter()


@router.get("/watchdog/rapport")
def get_rapport():
    """Retourne le rapport de surveillance complet."""
    return rapport_status


@router.post("/watchdog/refresh")
def refresh_rapport():
    """Force un recalcul immédiat du rapport."""
    t = threading.Thread(target=run_watchdog, daemon=True)
    t.start()
    return {"status": "started", "message": "Rapport en cours de recalcul"}


@router.post("/watchdog/test-telegram")
def test_telegram():
    """Envoie un message de test sur Telegram."""
    from app.agents.telegram_notifier import send_message
    ok = send_message(
        "✅ *Proprexis CRM connecté !*\n\n"
        "Ton assistant de prospection est opérationnel.\n\n"
        "Tu recevras ici :\n"
        "🔴 Alertes factures en retard\n"
        "🟠 Prospects à relancer\n"
        "🔵 Rappels chantiers\n"
        "🟢 Nouveaux prospects la nuit\n"
        "🌅 Rapport matinal à 7h00"
    )
    if ok:
        return {"status": "ok", "message": "Message envoyé sur Telegram !"}
    return {"status": "error", "message": "Erreur envoi Telegram — vérifie le token et chat_id"}


@router.post("/watchdog/check-inbox")
def check_inbox_now():
    """Force une vérification immédiate de la boîte Gmail."""
    from app.agents.gmail_agent import check_inbox
    t = threading.Thread(target=check_inbox, daemon=True)
    t.start()
    return {"status": "started", "message": "Vérification Gmail lancée"}


@router.post("/watchdog/test-gmail")
def test_gmail():
    """Teste la connexion Gmail."""
    try:
        from app.agents.gmail_agent import get_gmail_service
        service = get_gmail_service()
        profile = service.users().getProfile(userId='me').execute()
        return {"status": "ok", "email": profile['emailAddress'], "messages": profile['messagesTotal']}
    except Exception as e:
        return {"status": "error", "message": str(e)}