"""
Claude Autonomy — Logique de décision autonome et escalation
Définit ce que Claude peut faire seule vs ce qui nécessite validation Mohand
"""
import logging
from typing import Dict, Any, Tuple
from app.agents.claude_memory import retrieve, log_decision
from app.agents.telegram_notifier import send_message

logger = logging.getLogger("proprexis.claude_autonomy")


# ══════════════════════════════════════════════════════════════
#  RÈGLES D'AUTONOMIE
# ══════════════════════════════════════════════════════════════

AUTONOMY_RULES = {
    "email_prospection": {
        "autonomous": True,
        "daily_limit": 50,  # Quota quotidien
        "conditions": ["prospect has email", "status in [new, scored]"]
    },
    "enrich_prospect": {
        "autonomous": True,
        "daily_budget": 50,  # Budget quotidien en €
        "cost_per_call": 0.50,  # Coût par appel Pappers
        "conditions": ["prospect score >= 40"]
    },
    "generate_devis": {
        "autonomous": True,
        "max_amount": 10000,  # Montant max sans validation (€)
        "conditions": ["prospect replied", "all info collected"]
    },
    "negotiate_price": {
        "autonomous": True,
        "max_discount_percent": 15,  # Remise max sans validation
        "conditions": ["devis already sent", "client requesting discount"]
    },
    "create_chantier": {
        "autonomous": True,
        "conditions": ["devis signed", "payment confirmed or scheduled"]
    },
    "send_invoice": {
        "autonomous": True,
        "conditions": ["chantier completed", "client validated"]
    }
}


# ══════════════════════════════════════════════════════════════
#  RÈGLES D'ESCALATION
# ══════════════════════════════════════════════════════════════

ESCALATION_RULES = {
    "devis_montant_eleve": {
        "condition": lambda amount: amount > 15000,
        "reason": "Devis >15k€ nécessite validation Mohand",
        "priority": "high"
    },
    "negociation_importante": {
        "condition": lambda discount: discount > 15,
        "reason": "Remise >15% nécessite validation Mohand",
        "priority": "medium"
    },
    "budget_depasse": {
        "condition": lambda spent, limit: spent > limit,
        "reason": "Budget quotidien dépassé",
        "priority": "low"
    },
    "question_hors_perimetre": {
        "condition": lambda topic: topic in ["juridique", "rh", "comptable", "litige"],
        "reason": "Question hors périmètre technique",
        "priority": "high"
    },
    "client_mecontent": {
        "condition": lambda sentiment: sentiment == "negative",
        "reason": "Client mécontent détecté — intervention humaine requise",
        "priority": "urgent"
    },
    "situation_ambigue": {
        "condition": lambda confidence: confidence < 0.7,
        "reason": "Situation ambiguë — préfère escalader par prudence",
        "priority": "medium"
    }
}


# ══════════════════════════════════════════════════════════════
#  FONCTIONS DE DÉCISION
# ══════════════════════════════════════════════════════════════

def can_act_autonomously(
    action: str,
    context: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Détermine si Claude peut agir de manière autonome.

    Args:
        action: Type d'action (email_prospection, generate_devis, etc.)
        context: Contexte de la décision (montants, compteurs, etc.)

    Returns:
        (can_act: bool, reason: str)

    Example:
        can_act, reason = can_act_autonomously("generate_devis", {"amount": 12000})
    """
    if action not in AUTONOMY_RULES:
        return False, f"Action '{action}' inconnue"

    rule = AUTONOMY_RULES[action]

    # Vérifier si action est autonome par défaut
    if not rule.get("autonomous", False):
        return False, "Action nécessite validation par défaut"

    # Vérifier limites spécifiques
    if action == "email_prospection":
        daily_sent = context.get("daily_sent", 0)
        limit = rule["daily_limit"]
        if daily_sent >= limit:
            return False, f"Quota quotidien atteint ({daily_sent}/{limit})"

    elif action == "enrich_prospect":
        daily_spent = context.get("daily_spent", 0)
        budget = rule["daily_budget"]
        if daily_spent >= budget:
            return False, f"Budget quotidien dépassé ({daily_spent}€/{budget}€)"

    elif action == "generate_devis":
        amount = context.get("amount", 0)
        max_amount = rule["max_amount"]
        if amount > max_amount:
            return False, f"Devis {amount}€ > {max_amount}€ max autonome"

    elif action == "negotiate_price":
        discount_percent = context.get("discount_percent", 0)
        max_discount = rule["max_discount_percent"]
        if discount_percent > max_discount:
            return False, f"Remise {discount_percent}% > {max_discount}% max autonome"

    return True, "Action autonome autorisée"


def should_escalate(
    situation: str,
    context: Dict[str, Any]
) -> Tuple[bool, str, str]:
    """
    Détermine si la situation nécessite escalation à Mohand.

    Args:
        situation: Type de situation
        context: Contexte (montants, sentiment, topic, etc.)

    Returns:
        (should_escalate: bool, reason: str, priority: str)

    Example:
        escalate, reason, priority = should_escalate("devis_montant_eleve", {"amount": 18000})
    """
    if situation not in ESCALATION_RULES:
        # Par défaut, escalader si situation inconnue (principe de précaution)
        return True, "Situation inconnue — escalation par précaution", "medium"

    rule = ESCALATION_RULES[situation]
    condition = rule["condition"]

    # Évaluer condition
    try:
        if situation == "devis_montant_eleve":
            triggered = condition(context.get("amount", 0))
        elif situation == "negociation_importante":
            triggered = condition(context.get("discount_percent", 0))
        elif situation == "budget_depasse":
            triggered = condition(context.get("spent", 0), context.get("limit", 100))
        elif situation == "question_hors_perimetre":
            triggered = condition(context.get("topic", ""))
        elif situation == "client_mecontent":
            triggered = condition(context.get("sentiment", "neutral"))
        elif situation == "situation_ambigue":
            triggered = condition(context.get("confidence", 1.0))
        else:
            triggered = False

        if triggered:
            return True, rule["reason"], rule["priority"]
        else:
            return False, "Pas d'escalation nécessaire", "none"

    except Exception as e:
        logger.error(f"Error evaluating escalation rule {situation}: {e}")
        return True, f"Erreur évaluation — escalation par sécurité: {e}", "high"


def request_human_validation(
    action: str,
    context: Dict[str, Any],
    reason: str,
    priority: str = "medium"
) -> int:
    """
    Demande validation à Mohand via Telegram.

    Args:
        action: Action à valider
        context: Contexte de la décision
        reason: Raison de l'escalation
        priority: Urgence (urgent, high, medium, low)

    Returns:
        decision_id: ID de la décision créée (pour tracking)

    Example:
        decision_id = request_human_validation(
            "generate_devis",
            {"prospect_id": 123, "amount": 18000},
            "Devis >15k€",
            "high"
        )
    """
    # Logger la décision
    decision_id = log_decision(
        decision_type=action,
        decision_data=context,
        reasoning=reason,
        escalated=True
    )

    # Formater message Telegram
    priority_emoji = {
        "urgent": "🚨",
        "high": "🔴",
        "medium": "🟠",
        "low": "🟡"
    }

    emoji = priority_emoji.get(priority, "ℹ️")

    message = f"""{emoji} *VALIDATION REQUISE*

*Action* : {action}
*Raison* : {reason}
*Priorité* : {priority.upper()}

*Contexte* :
"""

    for key, value in context.items():
        if key == "amount":
            message += f"  • Montant : *{value:,.0f}€*\n"
        elif key == "prospect_id":
            message += f"  • Prospect ID : {value}\n"
        elif key == "discount_percent":
            message += f"  • Remise demandée : *{value}%*\n"
        else:
            message += f"  • {key} : {value}\n"

    message += f"""
*Décision #{decision_id}*

Réponds :
• ✅ "valide #{decision_id}" pour approuver
• ❌ "refuse #{decision_id}" pour refuser
• 💬 Ou pose des questions
"""

    send_message(message)
    logger.info(f"Human validation requested: {action} (decision #{decision_id})")

    return decision_id


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def get_daily_counters() -> Dict[str, Any]:
    """
    Récupère les compteurs quotidiens (emails envoyés, budget dépensé, etc.)

    Returns:
        Dict avec compteurs du jour
    """
    from datetime import datetime
    from app.core.database import SessionLocal
    from app.models.email_log import EmailLog
    from app.models.ai_memory import AIDecision

    db = SessionLocal()
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0)

        # Emails envoyés aujourd'hui
        emails_sent = db.query(EmailLog).filter(
            EmailLog.sent_at >= today,
            EmailLog.email_type == "prospection"
        ).count()

        # Budget dépensé aujourd'hui (enrichissements)
        enrichments = db.query(AIDecision).filter(
            AIDecision.created_at >= today,
            AIDecision.decision_type == "prospect_enriched"
        ).count()

        budget_spent = enrichments * 0.50  # 0.50€ par enrichissement

        return {
            "emails_sent": emails_sent,
            "budget_spent": budget_spent,
            "date": today.isoformat()
        }

    finally:
        db.close()


def get_autonomy_status() -> Dict[str, Any]:
    """
    Retourne le statut d'autonomie de Claude (quotas, limites, etc.)

    Returns:
        Dict avec status complet
    """
    counters = get_daily_counters()

    email_quota = int(retrieve('email_quota_daily')['value']) if retrieve('email_quota_daily') else 50
    enrichment_budget = AUTONOMY_RULES["enrich_prospect"]["daily_budget"]

    return {
        "emails": {
            "sent_today": counters["emails_sent"],
            "quota_daily": email_quota,
            "remaining": max(0, email_quota - counters["emails_sent"]),
            "percentage_used": (counters["emails_sent"] / email_quota * 100) if email_quota > 0 else 0
        },
        "enrichment": {
            "spent_today": counters["budget_spent"],
            "budget_daily": enrichment_budget,
            "remaining": max(0, enrichment_budget - counters["budget_spent"]),
            "percentage_used": (counters["budget_spent"] / enrichment_budget * 100) if enrichment_budget > 0 else 0
        },
        "limits": {
            "devis_max_autonomous": AUTONOMY_RULES["generate_devis"]["max_amount"],
            "discount_max_autonomous": AUTONOMY_RULES["negotiate_price"]["max_discount_percent"]
        }
    }
