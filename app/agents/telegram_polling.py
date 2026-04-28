"""
Telegram Polling — Écoute les messages Telegram en temps réel (dev local)
Alternative au webhook qui nécessite HTTPS + domaine public
"""
import requests
import logging
import time
import threading
from app.agents.telegram_notifier import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger("proprexis.telegram_polling")

# État du polling
polling_active = False
polling_thread = None
last_update_id = 0


def get_updates(offset: int = 0, timeout: int = 30) -> list:
    """
    Récupère les nouveaux messages Telegram via long polling.

    Args:
        offset: ID du dernier update traité + 1
        timeout: Durée du long polling (secondes)

    Returns:
        Liste des updates reçus
    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {
            "offset": offset,
            "timeout": timeout,
            "allowed_updates": ["message"]  # Seulement les messages
        }

        response = requests.get(url, params=params, timeout=timeout + 5)
        data = response.json()

        if data.get("ok"):
            return data.get("result", [])
        else:
            logger.error(f"Erreur getUpdates : {data}")
            return []

    except Exception as e:
        logger.error(f"Exception getUpdates : {e}")
        return []


def process_update(update: dict):
    """
    Traite un update Telegram (message reçu).

    Args:
        update: Dict avec structure Telegram update
    """
    global last_update_id

    try:
        update_id = update.get("update_id")
        message = update.get("message", {})

        if not message:
            return

        # Extraire infos du message
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "")
        from_user = message.get("from", {}).get("first_name", "Mohand")

        # SÉCURITÉ : Vérifier que c'est bien Mohand
        if chat_id != TELEGRAM_CHAT_ID:
            logger.warning(f"⚠️ Message reçu d'un chat_id inconnu : {chat_id} (ignoré)")
            return

        if not text:
            return

        logger.info(f"📨 Message reçu de {from_user} : {text}")

        # Traiter le message via l'API Claude
        from app.api.api_claude import handle_telegram_message
        response = handle_telegram_message(text, from_user)

        logger.info(f"✅ Réponse envoyée : {response[:100]}...")

        # Mettre à jour last_update_id
        last_update_id = max(last_update_id, update_id)

    except Exception as e:
        logger.error(f"Erreur process_update : {e}")


def polling_loop():
    """
    Boucle principale du polling — tourne en arrière-plan.
    Appelle getUpdates en continu et traite chaque message.
    """
    global polling_active, last_update_id

    logger.info("🚀 Telegram polling démarré")

    while polling_active:
        try:
            # Récupérer les nouveaux messages
            updates = get_updates(offset=last_update_id + 1, timeout=30)

            # Traiter chaque update
            for update in updates:
                process_update(update)

            # Petit délai si pas de long polling (sécurité)
            if not updates:
                time.sleep(1)

        except Exception as e:
            logger.error(f"Erreur polling_loop : {e}")
            time.sleep(5)  # Pause avant retry

    logger.info("⏹ Telegram polling arrêté")


def start_polling():
    """
    Démarre le polling Telegram en arrière-plan (thread daemon).
    À appeler au démarrage de FastAPI (lifespan).
    """
    global polling_active, polling_thread

    if polling_active:
        logger.warning("⚠️ Polling déjà actif")
        return

    polling_active = True
    polling_thread = threading.Thread(target=polling_loop, daemon=True)
    polling_thread.start()

    logger.info("✅ Telegram polling thread démarré")


def stop_polling():
    """
    Arrête proprement le polling Telegram.
    À appeler à l'arrêt de FastAPI (lifespan).
    """
    global polling_active

    if not polling_active:
        return

    logger.info("⏹ Arrêt du polling...")
    polling_active = False

    # Attendre fin du thread (max 5s)
    if polling_thread:
        polling_thread.join(timeout=5)

    logger.info("✅ Polling arrêté")


def get_polling_status() -> dict:
    """Retourne le statut du polling pour debug."""
    return {
        "active": polling_active,
        "last_update_id": last_update_id,
        "thread_alive": polling_thread.is_alive() if polling_thread else False
    }
