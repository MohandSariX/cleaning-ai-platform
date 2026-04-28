"""
API Claude — Interface Telegram conversationnelle + IA Assistant
Utilise Groq API (gratuit) avec Mixtral-8x7B
Réutilise le bot existant (telegram_notifier.py) en MODE BIDIRECTIONNEL
"""
import os
import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from groq import Groq
from app.agents.telegram_notifier import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, send_message
from app.agents.claude_memory import store_message, get_conversation_history, get_full_context, retrieve
from app.agents import claude_assistant

logger = logging.getLogger("proprexis.claude_api")

router = APIRouter()

# Client Groq API (gratuit !)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("⚠️ GROQ_API_KEY manquante dans .env")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Modèle à utiliser (gratuit, très rapide)
# Options: "mixtral-8x7b-32768", "llama3-70b-8192", "llama3-8b-8192"
GROQ_MODEL = "llama-3.3-70b-versatile"


# ══════════════════════════════════════════════════════════════
#  TELEGRAM WEBHOOK — Réception messages Mohand
# ══════════════════════════════════════════════════════════════

@router.post("/claude/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Webhook Telegram — Reçoit les messages de Mohand et répond via l'IA.

    À configurer sur Telegram :
    curl -X POST https://api.telegram.org/bot{TOKEN}/setWebhook \
         -H "Content-Type: application/json" \
         -d '{"url": "https://ton-domaine.com/api/claude/telegram/webhook"}'
    """
    try:
        data = await request.json()
        logger.info(f"Webhook Telegram reçu : {data}")

        # Extraire le message
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        from_user = message.get("from", {}).get("first_name", "Mohand")

        # Vérifier que c'est bien Mohand (sécurité)
        if str(chat_id) != TELEGRAM_CHAT_ID:
            logger.warning(f"Message d'un chat_id inconnu : {chat_id}")
            return {"status": "ignored"}

        if not text:
            return {"status": "no_text"}

        # Commandes spéciales
        if text.startswith("/"):
            response_text = handle_command(text)
        else:
            # Conversation normale → IA
            response_text = await handle_conversation(text, from_user)

        # Répondre via Telegram
        send_message(response_text)

        # Logger la conversation
        store_message("mohand", text)
        store_message("claude", response_text)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Erreur webhook Telegram : {e}")
        return {"status": "error", "message": str(e)}


def handle_command(command: str) -> str:
    """
    Gère les commandes Telegram slash.

    Commandes disponibles :
    - /status : État du CRM
    - /brief : Briefing quotidien
    - /help : Liste des commandes
    """
    command_lower = command.lower().strip()

    if command_lower == "/status":
        return generate_status_report()

    elif command_lower == "/brief":
        from app.agents.claude_assistant import generate_daily_briefing
        return generate_daily_briefing()

    elif command_lower == "/help":
        return """🤖 *Commandes disponibles*

/status — État du CRM en temps réel
/brief — Briefing quotidien
/help — Cette aide

Tu peux aussi me parler naturellement :
"Claude, combien de prospects cette semaine ?"
"Quel est le statut du devis Syndic ABC ?"
"Envoie 20 emails aux meilleurs prospects"
"""

    else:
        return f"Commande inconnue : {command}\nTape /help pour voir les commandes disponibles."


async def handle_conversation(text: str, from_user: str = "Mohand") -> str:
    """
    Gère une conversation naturelle avec l'IA (Groq/Mixtral).

    Args:
        text: Message de Mohand
        from_user: Nom de l'utilisateur

    Returns:
        Réponse de l'IA
    """
    if not groq_client:
        return "⚠️ Groq API pas configurée (GROQ_API_KEY manquante dans .env)."

    try:
        # Récupérer contexte CRM + mémoire
        crm_context = get_crm_summary()
        memory_context = get_full_context()
        conversation_history = get_conversation_history(limit=20)

        # Construire l'historique pour l'IA
        messages = [
            {"role": "system", "content": build_system_prompt(memory_context, crm_context)}
        ]

        # Ajouter historique conversation
        for msg in conversation_history[-10:]:  # 10 derniers messages
            role = "user" if msg["from"] == "mohand" else "assistant"
            messages.append({"role": role, "content": msg["text"]})

        # Ajouter le message actuel
        messages.append({"role": "user", "content": text})

        # Appeler Groq (format OpenAI-compatible)
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=2048,
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Erreur conversation Groq : {e}")
        return f"❌ Erreur : {str(e)}"


def build_system_prompt(memory_context: str, crm_context: str) -> str:
    """
    Construit le prompt système pour l'IA avec tout le contexte.
    """
    return f"""Tu es Claude, l'associée IA de Proprexis.

# TON RÔLE
Tu es responsable de la prospection et du commercial pour Proprexis, une entreprise de nettoyage professionnel en Île-de-France.

Mohand (le fondateur) réalise les chantiers. Toi tu gères tout le reste :
- Prospection automatique
- Qualification des leads
- Génération de devis
- Suivi commercial
- Relances
- Optimisation continue

# TES RESPONSABILITÉS

✅ **TU PEUX décider seule** :
- Envoyer des emails de prospection (quota quotidien)
- Qualifier les prospects qui répondent
- Générer des devis standards (<10k€)
- Enrichir des prospects (budget <50€/jour)
- Ajuster les campagnes selon performances
- Relancer les factures impayées
- Créer des chantiers depuis devis signés

⚠️ **TU DOIS escalader à Mohand** si :
- Devis >15k€
- Négociation >15% de réduction
- Question hors périmètre (juridique, RH, litige)
- Dépense >100€
- Situation ambiguë

# TON STYLE DE COMMUNICATION

- **Concis et direct** : pas de blabla, va à l'essentiel
- **Proactif** : propose des actions, pas juste des constats
- **Data-driven** : chiffres et KPIs
- **Transparent** : explique tes décisions
- **Humble** : escalade si doute

Format tes réponses avec :
- 📊 📧 💰 ⚠️ 🎯 💡 (emojis pertinents)
- **Gras** pour les chiffres importants
- Structure claire (sections si besoin)

# CONTEXTE CRM ACTUEL

{crm_context}

# TA MÉMOIRE

{memory_context}

# INSTRUCTIONS

Réponds à Mohand de manière naturelle et utile. Si tu prends une décision autonome, explique pourquoi. Si tu dois escalader, dis-le clairement.
"""


def get_crm_summary() -> str:
    """Génère un résumé du CRM actuel pour le contexte de l'IA."""
    from app.core.database import SessionLocal
    from app.models.prospect import Prospect
    from sqlalchemy import func

    db = SessionLocal()
    try:
        # Stats prospects
        total_prospects = db.query(Prospect).count()
        with_email = db.query(Prospect).filter(Prospect.email.isnot(None)).count()
        avg_score = db.query(func.avg(Prospect.lead_score)).scalar() or 0
        high_score = db.query(Prospect).filter(Prospect.lead_score >= 70).count()
        contacted = db.query(Prospect).filter(Prospect.status == "contacted").count()

        email_pct = (with_email/total_prospects*100) if total_prospects > 0 else 0

        return f"""## PROSPECTS
- Total : {total_prospects}
- Avec email : {with_email} ({email_pct:.0f}%)
- Score moyen : {avg_score:.1f}/100
- Score ≥70 : {high_score}
- Contactés : {contacted}

## QUOTA EMAIL
- Quota quotidien : {retrieve('email_quota_daily')['value'] if retrieve('email_quota_daily') else '50'}/jour
"""
    finally:
        db.close()


def generate_status_report() -> str:
    """Génère un rapport de statut rapide."""
    crm = get_crm_summary()
    return f"""📊 *STATUS CRM PROPREXIS*

{crm}

🤖 *Agents actifs* : 9 jobs scheduler
✅ *Dernier scraping* : Consulte /api/scheduler/status

Pour plus de détails, demande-moi naturellement :
"Claude, montre-moi les meilleurs prospects"
"""


# ══════════════════════════════════════════════════════════════
#  ENDPOINTS MANUELS — Pour tester sans Telegram
# ══════════════════════════════════════════════════════════════

class AskRequest(BaseModel):
    question: str


@router.post("/claude/ask")
def ask_claude(req: AskRequest):
    """
    Endpoint pour poser une question à Claude directement (sans Telegram).
    Utile pour tests.
    """
    try:
        import asyncio
        response = asyncio.run(handle_conversation(req.question))
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/claude/status")
def claude_status():
    """Statut de Claude (API configurée, mémoire, etc.)."""
    return {
        "api_configured": GROQ_API_KEY is not None,
        "api_provider": "Groq (gratuit)",
        "model": GROQ_MODEL,
        "telegram_configured": True,
        "telegram_chat_id": TELEGRAM_CHAT_ID,
        "memory_entries": len(get_full_context().split("\n")),
        "conversation_history": len(get_conversation_history())
    }


@router.post("/claude/memory/init")
def init_memory():
    """Initialise la mémoire avec valeurs par défaut."""
    from app.agents.claude_memory import initialize_default_memories
    initialize_default_memories()
    return {"status": "initialized"}


# ══════════════════════════════════════════════════════════════
#  TELEGRAM MESSAGE HANDLER — Pour webhook ET polling
# ══════════════════════════════════════════════════════════════

def handle_telegram_message(text: str, from_user: str = "Mohand") -> str:
    """
    Traite un message Telegram (appelé par webhook OU polling).

    Args:
        text: Texte du message
        from_user: Nom de l'utilisateur

    Returns:
        Réponse à envoyer (déjà envoyée via send_message)
    """
    try:
        # Commandes spéciales
        if text.startswith("/"):
            response_text = handle_command(text)
        else:
            # Conversation normale → IA
            import asyncio
            response_text = asyncio.run(handle_conversation(text, from_user))

        # Envoyer la réponse via Telegram
        send_message(response_text)

        # Logger la conversation
        store_message("mohand", text)
        store_message("claude", response_text)

        return response_text

    except Exception as e:
        logger.error(f"Erreur handle_telegram_message : {e}")
        error_msg = f"❌ Erreur : {str(e)}"
        send_message(error_msg)
        return error_msg
