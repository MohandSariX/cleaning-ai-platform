"""
Claude Memory Manager — Gestionnaire de mémoire persistante pour Claude l'associée IA
Permet de stocker/récupérer patterns, stratégies, apprentissages
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ai_memory import AIMemory, AIDecision, ConversationHistory

logger = logging.getLogger("proprexis.claude_memory")


# ══════════════════════════════════════════════════════════════
#  AI MEMORY — Mémoire long terme
# ══════════════════════════════════════════════════════════════

def store(key: str, value: str, context: str = "general", meta_data: dict = None) -> bool:
    """
    Stocke une information dans la mémoire de Claude.

    Args:
        key: Identifiant unique (ex: "best_email_time_syndic_94")
        value: Valeur à stocker (ex: "10:00-11:00")
        context: Catégorie (prospection, commercial, strategy, learning)
        meta_data: Métadonnées additionnelles (taux succès, dates, etc.)

    Returns:
        True si succès, False sinon
    """
    db: Session = SessionLocal()
    try:
        # Vérifier si existe déjà
        existing = db.query(AIMemory).filter(AIMemory.key == key).first()

        if existing:
            # Mettre à jour
            existing.value = value
            existing.context = context
            existing.meta_data = meta_data or {}
            existing.updated_at = datetime.now()
            logger.info(f"Mémoire mise à jour : {key}")
        else:
            # Créer nouveau
            memory = AIMemory(
                key=key,
                value=value,
                context=context,
                meta_data=meta_data or {}
            )
            db.add(memory)
            logger.info(f"Mémoire créée : {key}")

        db.commit()
        return True
    except Exception as e:
        logger.error(f"Erreur store mémoire : {e}")
        db.rollback()
        return False
    finally:
        db.close()


def retrieve(key: str) -> Optional[Dict[str, Any]]:
    """
    Récupère une information de la mémoire.

    Args:
        key: Identifiant à récupérer

    Returns:
        Dict avec {value, context, meta_data, updated_at} ou None
    """
    db: Session = SessionLocal()
    try:
        memory = db.query(AIMemory).filter(AIMemory.key == key).first()
        if memory:
            return {
                "value": memory.value,
                "context": memory.context,
                "meta_data": memory.meta_data,
                "updated_at": memory.updated_at.isoformat() if memory.updated_at else None
            }
        return None
    except Exception as e:
        logger.error(f"Erreur retrieve mémoire : {e}")
        return None
    finally:
        db.close()


def search(context: str = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Recherche dans la mémoire par contexte.

    Args:
        context: Filtrer par contexte (None = tous)
        limit: Nombre max de résultats

    Returns:
        Liste de dicts {key, value, context, meta_data}
    """
    db: Session = SessionLocal()
    try:
        query = db.query(AIMemory)

        if context:
            query = query.filter(AIMemory.context == context)

        memories = query.order_by(AIMemory.updated_at.desc()).limit(limit).all()

        return [{
            "key": m.key,
            "value": m.value,
            "context": m.context,
            "meta_data": m.meta_data,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None
        } for m in memories]
    except Exception as e:
        logger.error(f"Erreur search mémoire : {e}")
        return []
    finally:
        db.close()


def delete(key: str) -> bool:
    """Supprime une entrée de la mémoire."""
    db: Session = SessionLocal()
    try:
        memory = db.query(AIMemory).filter(AIMemory.key == key).first()
        if memory:
            db.delete(memory)
            db.commit()
            logger.info(f"Mémoire supprimée : {key}")
            return True
        return False
    except Exception as e:
        logger.error(f"Erreur delete mémoire : {e}")
        db.rollback()
        return False
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  AI DECISIONS — Journal des décisions
# ══════════════════════════════════════════════════════════════

def log_decision(
    decision_type: str,
    decision_data: dict,
    reasoning: str,
    escalated: bool = False
) -> int:
    """
    Enregistre une décision prise par Claude.

    Args:
        decision_type: Type (email_sent, devis_generated, etc.)
        decision_data: Données complètes de la décision
        reasoning: Explication du raisonnement
        escalated: Si escaladé à Mohand

    Returns:
        ID de la décision créée
    """
    db: Session = SessionLocal()
    try:
        decision = AIDecision(
            decision_type=decision_type,
            decision_data=decision_data,
            reasoning=reasoning,
            escalated_to_human=escalated
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)
        logger.info(f"Décision loggée : {decision_type} (ID: {decision.id})")
        return decision.id
    except Exception as e:
        logger.error(f"Erreur log_decision : {e}")
        db.rollback()
        return -1
    finally:
        db.close()


def update_decision_outcome(decision_id: int, outcome: str, feedback: str = None) -> bool:
    """
    Met à jour le résultat d'une décision.

    Args:
        decision_id: ID de la décision
        outcome: Résultat (success, failed, cancelled)
        feedback: Retour humain optionnel

    Returns:
        True si succès
    """
    db: Session = SessionLocal()
    try:
        decision = db.query(AIDecision).filter(AIDecision.id == decision_id).first()
        if decision:
            decision.outcome = outcome
            if feedback:
                decision.human_feedback = feedback
            db.commit()
            logger.info(f"Décision {decision_id} → {outcome}")
            return True
        return False
    except Exception as e:
        logger.error(f"Erreur update_decision_outcome : {e}")
        db.rollback()
        return False
    finally:
        db.close()


def get_recent_decisions(decision_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Récupère les décisions récentes (pour analyse/rapport)."""
    db: Session = SessionLocal()
    try:
        query = db.query(AIDecision)

        if decision_type:
            query = query.filter(AIDecision.decision_type == decision_type)

        decisions = query.order_by(AIDecision.created_at.desc()).limit(limit).all()

        return [{
            "id": d.id,
            "type": d.decision_type,
            "data": d.decision_data,
            "reasoning": d.reasoning,
            "outcome": d.outcome,
            "escalated": d.escalated_to_human,
            "feedback": d.human_feedback,
            "created_at": d.created_at.isoformat() if d.created_at else None
        } for d in decisions]
    except Exception as e:
        logger.error(f"Erreur get_recent_decisions : {e}")
        return []
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  CONVERSATION HISTORY — Historique Telegram
# ══════════════════════════════════════════════════════════════

def store_message(message_from: str, message_text: str, context: dict = None) -> bool:
    """
    Stocke un message de la conversation Telegram.

    Args:
        message_from: "mohand" ou "claude"
        message_text: Contenu du message
        context: Contexte CRM au moment du message

    Returns:
        True si succès
    """
    db: Session = SessionLocal()
    try:
        conv = ConversationHistory(
            message_from=message_from,
            message_text=message_text,
            context=context or {}
        )
        db.add(conv)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Erreur store_message : {e}")
        db.rollback()
        return False
    finally:
        db.close()


def get_conversation_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Récupère l'historique récent des conversations."""
    db: Session = SessionLocal()
    try:
        messages = db.query(ConversationHistory)\
            .order_by(ConversationHistory.created_at.desc())\
            .limit(limit).all()

        return [{
            "from": m.message_from,
            "text": m.message_text,
            "context": m.context,
            "timestamp": m.created_at.isoformat() if m.created_at else None
        } for m in reversed(messages)]  # Inverser pour avoir chronologique
    except Exception as e:
        logger.error(f"Erreur get_conversation_history : {e}")
        return []
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  HELPERS — Initialisation et utilitaires
# ══════════════════════════════════════════════════════════════

def initialize_default_memories():
    """
    Initialise la mémoire avec des valeurs par défaut au premier lancement.
    À appeler une seule fois au démarrage de Claude.
    """
    defaults = [
        {
            "key": "role",
            "value": "Associée IA de Proprexis, responsable prospection et commercial",
            "context": "identity"
        },
        {
            "key": "owner_name",
            "value": "Mohand",
            "context": "identity"
        },
        {
            "key": "company_name",
            "value": "Proprexis",
            "context": "identity"
        },
        {
            "key": "company_location",
            "value": "Champigny-sur-Marne, IDF",
            "context": "identity"
        },
        {
            "key": "email_quota_daily",
            "value": "50",
            "context": "prospection",
            "meta_data": {"source": "gmail", "adjustable": True}
        },
        {
            "key": "devis_auto_limit",
            "value": "10000",
            "context": "commercial",
            "meta_data": {"currency": "EUR", "description": "Montant max devis sans validation"}
        },
        {
            "key": "negotiation_max_discount",
            "value": "15",
            "context": "commercial",
            "meta_data": {"unit": "percent", "description": "Réduction max sans escalation"}
        },
    ]

    for mem in defaults:
        store(mem["key"], mem["value"], mem.get("context", "general"), mem.get("meta_data"))

    logger.info("✅ Mémoire initialisée avec valeurs par défaut")


def get_full_context() -> str:
    """
    Génère un contexte complet pour Claude depuis la mémoire.
    À utiliser dans les prompts système.

    Returns:
        String formaté avec toute la mémoire pertinente
    """
    memories = search(limit=200)

    if not memories:
        return "Aucune mémoire disponible."

    # Organiser par contexte
    by_context = {}
    for mem in memories:
        ctx = mem["context"]
        if ctx not in by_context:
            by_context[ctx] = []
        by_context[ctx].append(mem)

    # Formater
    lines = ["# MÉMOIRE CLAUDE\n"]

    for context, mems in sorted(by_context.items()):
        lines.append(f"\n## {context.upper()}")
        for m in mems:
            lines.append(f"- {m['key']}: {m['value']}")
            if m.get('meta_data'):
                lines.append(f"  Meta: {m['meta_data']}")

    return "\n".join(lines)
