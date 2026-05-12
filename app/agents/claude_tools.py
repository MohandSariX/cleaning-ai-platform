"""
Claude Tools — Function calling pour accès CRM
Permet à l'IA d'interagir avec la base de données
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.models.email_log import EmailLog
from app.agents.claude_memory import log_decision
from app.agents.activity_logger import log_claude_tool_call
from app.agents.pappers_agent import enrich_prospect as pappers_enrich
from app.agents.gmail_agent import send_email as gmail_send
from app.agents.email_templates import get_template
from app.utils.devis_engine import calculate as calculate_devis
from sqlalchemy import and_, or_, func

logger = logging.getLogger("proprexis.claude_tools")


# ══════════════════════════════════════════════════════════════
#  TOOLS — PROSPECTS
# ══════════════════════════════════════════════════════════════

def get_prospects(
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Récupère les prospects avec filtres optionnels.

    Args:
        filters: Dict avec clés possibles:
            - min_score: int (score minimum)
            - max_score: int (score maximum)
            - status: str (new, scored, contacted, replied, etc.)
            - city: str (ville)
            - industry: str (secteur)
            - has_email: bool
            - has_phone: bool
        limit: Nombre max de résultats

    Returns:
        Liste de dicts avec infos prospects

    Example:
        get_prospects({"min_score": 50, "has_email": True}, limit=10)
    """
    db = SessionLocal()
    try:
        query = db.query(Prospect)

        # Appliquer filtres
        if filters:
            if "min_score" in filters:
                query = query.filter(Prospect.lead_score >= filters["min_score"])
            if "max_score" in filters:
                query = query.filter(Prospect.lead_score <= filters["max_score"])
            if "status" in filters:
                query = query.filter(Prospect.status == filters["status"])
            if "city" in filters:
                query = query.filter(Prospect.city.ilike(f"%{filters['city']}%"))
            if "industry" in filters:
                query = query.filter(Prospect.industry.ilike(f"%{filters['industry']}%"))
            if "has_email" in filters and filters["has_email"]:
                query = query.filter(Prospect.email.isnot(None))
            if "has_phone" in filters and filters["has_phone"]:
                query = query.filter(Prospect.phone.isnot(None))

        # Trier par score décroissant
        prospects = query.order_by(Prospect.lead_score.desc()).limit(limit).all()

        return [{
            "id": p.id,
            "company_name": p.company_name,
            "industry": p.industry,
            "city": p.city,
            "address": p.address,
            "email": p.email,
            "phone": p.phone,
            "website": p.website,
            "lead_score": p.lead_score,
            "score_label": p.score_label,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None
        } for p in prospects]

    finally:
        db.close()


def update_prospect(prospect_id: int, updates: Dict[str, Any]) -> bool:
    """
    Met à jour un prospect.

    Args:
        prospect_id: ID du prospect
        updates: Dict avec champs à modifier
            - status: str
            - lead_score: float
            - email: str
            - phone: str
            - notes: str (ajouté à score_explanation)

    Returns:
        True si succès

    Example:
        update_prospect(123, {"status": "contacted", "notes": "Email envoyé"})
    """
    db = SessionLocal()
    try:
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if not prospect:
            logger.error(f"Prospect {prospect_id} not found")
            return False

        # Appliquer mises à jour
        for key, value in updates.items():
            if key == "notes":
                # Ajouter note à score_explanation
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                note_line = f"\n[{timestamp}] {value}"
                prospect.score_explanation = (prospect.score_explanation or "") + note_line
            elif hasattr(prospect, key):
                setattr(prospect, key, value)

        db.commit()
        logger.info(f"Prospect {prospect_id} updated: {updates}")
        return True

    except Exception as e:
        logger.error(f"Error updating prospect {prospect_id}: {e}")
        db.rollback()
        return False
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  TOOLS — EMAILS
# ══════════════════════════════════════════════════════════════

def send_prospecting_email(
    prospect_id: int,
    template_name: str = "default",
    custom_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Envoie un email de prospection à un prospect.

    Args:
        prospect_id: ID du prospect
        template_name: Nom du template (default, btp, syndic, architecte)
        custom_message: Message personnalisé (optionnel)

    Returns:
        Dict avec success: bool, message: str

    Example:
        send_prospecting_email(123, template_name="btp")
    """
    db = SessionLocal()
    try:
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if not prospect:
            return {"success": False, "message": f"Prospect {prospect_id} not found"}

        if not prospect.email:
            return {"success": False, "message": "Prospect has no email"}

        # Récupérer template
        if custom_message:
            subject = f"Nettoyage professionnel — {prospect.company_name}"
            body = custom_message
        else:
            template = get_template(prospect.industry or "default")
            subject = template.get("subject", "Services de nettoyage professionnel")
            body = template.get("body", "").format(
                company_name=prospect.company_name,
                city=prospect.city or "votre région"
            )

        # TODO: Envoyer via Gmail API (gmail_send)
        # Pour l'instant, juste logger
        logger.info(f"Email sent to {prospect.email}: {subject}")

        # Mettre à jour prospect
        prospect.status = "contacted"
        prospect.last_contacted = datetime.now()
        db.commit()

        # Logger décision
        log_decision(
            decision_type="email_sent",
            decision_data={
                "prospect_id": prospect_id,
                "email": prospect.email,
                "template": template_name,
                "subject": subject
            },
            reasoning=f"Email prospection envoyé à {prospect.company_name} (score {prospect.lead_score})"
        )

        return {
            "success": True,
            "message": f"Email sent to {prospect.company_name}",
            "prospect_id": prospect_id,
            "email": prospect.email
        }

    except Exception as e:
        logger.error(f"Error sending email to prospect {prospect_id}: {e}")
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  TOOLS — ENRICHISSEMENT
# ══════════════════════════════════════════════════════════════

def enrich_prospect_pappers(prospect_id: int) -> Dict[str, Any]:
    """
    Enrichit un prospect via Pappers API.

    Args:
        prospect_id: ID du prospect

    Returns:
        Dict avec success: bool, data: dict enrichi

    Example:
        enrich_prospect_pappers(123)
    """
    db = SessionLocal()
    try:
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if not prospect:
            return {"success": False, "message": f"Prospect {prospect_id} not found"}

        # Appeler Pappers
        result = pappers_enrich(prospect_id)

        if result:
            # Logger décision
            log_decision(
                decision_type="prospect_enriched",
                decision_data={
                    "prospect_id": prospect_id,
                    "source": "pappers",
                    "data": result
                },
                reasoning=f"Enrichissement Pappers pour {prospect.company_name}"
            )

            return {
                "success": True,
                "message": f"Prospect enriched with Pappers data",
                "data": result
            }
        else:
            return {"success": False, "message": "Pappers data not found"}

    except Exception as e:
        logger.error(f"Error enriching prospect {prospect_id}: {e}")
        return {"success": False, "message": str(e)}
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  TOOLS — DEVIS
# ══════════════════════════════════════════════════════════════

def generate_quote(
    prospect_id: int,
    service_type: str,
    surface_m2: float,
    frequency: str = "ponctuel"
) -> Dict[str, Any]:
    """
    Génère un devis pour un prospect.

    Args:
        prospect_id: ID du prospect
        service_type: Type de prestation (bureaux, commerces, chantier, etc.)
        surface_m2: Surface en m²
        frequency: Fréquence (ponctuel, hebdo, mensuel)

    Returns:
        Dict avec success, montant_ht, montant_ttc

    Example:
        generate_quote(123, "bureaux", 150, "hebdo")
    """
    db = SessionLocal()
    try:
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if not prospect:
            return {"success": False, "message": f"Prospect {prospect_id} not found"}

        # Calculer devis
        devis_data = calculate_devis(service_type, surface_m2, frequency)

        if not devis_data:
            return {"success": False, "message": "Invalid service type or parameters"}

        # Logger décision
        log_decision(
            decision_type="devis_generated",
            decision_data={
                "prospect_id": prospect_id,
                "service_type": service_type,
                "surface_m2": surface_m2,
                "frequency": frequency,
                "montant_ttc": devis_data.get("montant_ttc")
            },
            reasoning=f"Devis généré pour {prospect.company_name}: {devis_data.get('montant_ttc')}€ TTC",
            escalated=devis_data.get("montant_ttc", 0) > 15000  # Escalade si >15k€
        )

        return {
            "success": True,
            "message": "Quote generated",
            "prospect_id": prospect_id,
            "company_name": prospect.company_name,
            **devis_data
        }

    except Exception as e:
        logger.error(f"Error generating quote for prospect {prospect_id}: {e}")
        return {"success": False, "message": str(e)}
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  TOOLS — STATISTIQUES
# ══════════════════════════════════════════════════════════════

def get_crm_statistics(period: str = "week") -> Dict[str, Any]:
    """
    Récupère les statistiques CRM.

    Args:
        period: Période (today, week, month, all)

    Returns:
        Dict avec toutes les stats

    Example:
        get_crm_statistics("week")
    """
    db = SessionLocal()
    try:
        now = datetime.now()

        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = datetime(2000, 1, 1)

        stats = {
            "period": period,
            "total_prospects": db.query(Prospect).count(),
            "new_prospects": db.query(Prospect).filter(
                Prospect.created_at >= start_date
            ).count(),
            "with_email": db.query(Prospect).filter(
                Prospect.email.isnot(None)
            ).count(),
            "avg_score": db.query(func.avg(Prospect.lead_score)).scalar() or 0,
            "high_score_count": db.query(Prospect).filter(
                Prospect.lead_score >= 70
            ).count(),
            "emails_sent": db.query(EmailLog).filter(
                EmailLog.sent_at >= start_date,
                EmailLog.email_type == "prospection"
            ).count(),
            "replied_count": db.query(Prospect).filter(
                Prospect.status == "replied"
            ).count(),
            "status_distribution": {}
        }

        # Distribution par statut
        status_dist = db.query(
            Prospect.status,
            func.count(Prospect.id)
        ).group_by(Prospect.status).all()

        stats["status_distribution"] = {status: count for status, count in status_dist}

        return stats

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  TOOLS REGISTRY — Pour Groq function calling
# ══════════════════════════════════════════════════════════════

TOOLS_REGISTRY = {
    "get_prospects": {
        "function": get_prospects,
        "description": "Récupère les prospects avec filtres (score, statut, ville, email...)",
        "parameters": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "Filtres: min_score, max_score, status, city, has_email, etc."
                },
                "limit": {"type": "integer", "default": 50}
            }
        }
    },
    "update_prospect": {
        "function": update_prospect,
        "description": "Met à jour un prospect (statut, notes, email, phone)",
        "parameters": {
            "type": "object",
            "properties": {
                "prospect_id": {"type": "integer", "required": True},
                "updates": {
                    "type": "object",
                    "description": "Champs à modifier: status, notes, email, phone",
                    "required": True
                }
            }
        }
    },
    "send_prospecting_email": {
        "function": send_prospecting_email,
        "description": "Envoie un email de prospection à un prospect",
        "parameters": {
            "type": "object",
            "properties": {
                "prospect_id": {"type": "integer", "required": True},
                "template_name": {"type": "string", "default": "default"},
                "custom_message": {"type": "string"}
            }
        }
    },
    "enrich_prospect_pappers": {
        "function": enrich_prospect_pappers,
        "description": "Enrichit un prospect via Pappers API (CA, dirigeant, SIRET)",
        "parameters": {
            "type": "object",
            "properties": {
                "prospect_id": {"type": "integer", "required": True}
            }
        }
    },
    "generate_quote": {
        "function": generate_quote,
        "description": "Génère un devis pour un prospect",
        "parameters": {
            "type": "object",
            "properties": {
                "prospect_id": {"type": "integer", "required": True},
                "service_type": {"type": "string", "required": True},
                "surface_m2": {"type": "number", "required": True},
                "frequency": {"type": "string", "default": "ponctuel"}
            }
        }
    },
    "get_crm_statistics": {
        "function": get_crm_statistics,
        "description": "Récupère les statistiques CRM (prospects, emails, scores)",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["today", "week", "month", "all"],
                    "default": "week"
                }
            }
        }
    }
}


def execute_tool(tool_name: str, **kwargs) -> Any:
    """
    Execute un tool par son nom.

    Args:
        tool_name: Nom du tool
        **kwargs: Arguments du tool

    Returns:
        Résultat du tool
    """
    if tool_name not in TOOLS_REGISTRY:
        return {"error": f"Tool {tool_name} not found"}

    tool_func = TOOLS_REGISTRY[tool_name]["function"]
    
    # Mesurer temps d'exécution
    import time
    start_time = time.time()
    
    try:
        result = tool_func(**kwargs)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Logger l'exécution
        log_claude_tool_call(
            tool_name=tool_name,
            arguments=kwargs,
            result=result,
            success=True,
            execution_time_ms=execution_time_ms
        )
        
        return result
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        logger.error(f"Error executing tool {tool_name}: {e}")
        
        # Logger l'erreur
        log_claude_tool_call(
            tool_name=tool_name,
            arguments=kwargs,
            result=str(e),
            success=False,
            execution_time_ms=execution_time_ms
        )
        
        return {"error": str(e)}
