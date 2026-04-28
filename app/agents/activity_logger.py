"""
Activity Logger — Interface centralisée pour logger toutes les actions des agents.
Utilisé par tous les agents : gmail, qualification, scraping, pappers, scheduler...
"""
import json
import logging
from datetime import datetime, date
from app.core.database import SessionLocal
from app.models.activity_log import ActivityLog

logger = logging.getLogger("proprexis.activity")


def log(
    event_type: str,
    message: str,
    event_sub: str = None,
    status: str = "info",
    prospect_id: int = None,
    client_id: int = None,
    details: dict = None,
    metric_value: float = None,
    ia_decision: str = None,
):
    """
    Log une activité dans la base de données.
    Appelé depuis tous les agents.
    """
    db = SessionLocal()
    try:
        entry = ActivityLog(
            event_type=event_type,
            event_sub=event_sub,
            message=message,
            status=status,
            prospect_id=prospect_id,
            client_id=client_id,
            details_json=json.dumps(details, ensure_ascii=False) if details else None,
            metric_value=metric_value,
            ia_decision=ia_decision,
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.error(f"Erreur activity_logger : {e}")
    finally:
        db.close()


def log_email_sent(prospect_id: int, prospect_name: str, city: str,
                   email_type: str, subject: str, score: int = None):
    """Email de prospection ou relance envoyé."""
    emoji = "📧" if email_type == "prospection" else "🔄"
    log(
        event_type="email_sent",
        event_sub=email_type,
        message=f"{emoji} Email {email_type} envoyé à {prospect_name} ({city})",
        status="success",
        prospect_id=prospect_id,
        metric_value=score,
        details={"subject": subject, "type": email_type},
    )


def log_email_received(prospect_id: int, prospect_name: str, intention: str,
                       message_preview: str, ia_reason: str = None):
    """Email reçu d'un prospect."""
    emojis = {
        "interesse": "😊", "demande_devis": "📋", "question": "❓",
        "pas_interesse": "👎", "signature": "🎉", "negociation": "💬",
        "accuse": "📭", "incertain": "🤔"
    }
    emoji = emojis.get(intention, "📬")
    log(
        event_type="email_received",
        event_sub=intention,
        message=f"{emoji} Réponse reçue de {prospect_name} — {intention}",
        status="info",
        prospect_id=prospect_id,
        details={"intention": intention, "preview": message_preview[:200]},
        ia_decision=ia_reason,
    )


def log_qualification(prospect_id: int, prospect_name: str, action: str,
                      infos: dict = None, ia_decision: str = None):
    """Action de qualification IA."""
    labels = {
        "qualification_sent": "🤖 Questions posées",
        "devis_sent": "📄 Devis généré et envoyé",
        "signed": "🎉 Devis accepté",
        "lost": "❌ Prospect perdu",
        "human_required": "🙋 Intervention humaine requise",
        "acknowledgement_ignored": "📭 Accusé de réception ignoré",
    }
    msg = labels.get(action, f"🤖 {action}")
    status = "success" if action in ("devis_sent", "signed") else \
             "warning" if action == "human_required" else "info"
    log(
        event_type="qualification",
        event_sub=action,
        message=f"{msg} — {prospect_name}",
        status=status,
        prospect_id=prospect_id,
        details={"action": action, "infos_collectees": infos},
        ia_decision=ia_decision,
    )


def log_devis(prospect_id: int, client_name: str, numero: str,
              montant_ttc: float, type_prestation: str):
    """Devis généré et envoyé."""
    log(
        event_type="devis_sent",
        message=f"📄 Devis {numero} envoyé à {client_name} — {montant_ttc:,.0f}€ TTC",
        status="success",
        prospect_id=prospect_id,
        metric_value=montant_ttc,
        details={"numero": numero, "type": type_prestation, "montant_ttc": montant_ttc},
    )


def log_scraping(dept: str, dept_name: str, nb_prospects: int,
                 nb_queries: int, duration_min: float = None):
    """Scraping nightly terminé."""
    log(
        event_type="scraping",
        message=f"🌙 Scraping terminé — Dept {dept} ({dept_name}) — {nb_prospects} nouveaux prospects",
        status="success",
        metric_value=nb_prospects,
        details={
            "dept": dept,
            "dept_name": dept_name,
            "nb_prospects": nb_prospects,
            "nb_queries": nb_queries,
            "duration_min": duration_min,
        },
    )


def log_enrichment(nb_enriched: int, nb_not_found: int):
    """Enrichissement Pappers terminé."""
    log(
        event_type="enrichment",
        message=f"📊 Enrichissement Pappers — {nb_enriched} enrichis, {nb_not_found} introuvables",
        status="success" if nb_enriched > 0 else "info",
        metric_value=nb_enriched,
        details={"enriched": nb_enriched, "not_found": nb_not_found},
    )


def log_system(message: str, status: str = "info", details: dict = None):
    """Événement système (token refresh, démarrage, erreur...)."""
    log(
        event_type="system",
        message=message,
        status=status,
        details=details,
    )


def log_error(source: str, error: str, details: dict = None):
    """Erreur d'un agent."""
    log(
        event_type="error",
        message=f"❌ Erreur {source} : {error[:200]}",
        status="error",
        details={"source": source, "error": error, **(details or {})},
    )


def log_scheduler_job(job_name: str, status: str = "success", details: dict = None):
    """Exécution d'un job schedulé."""
    emojis = {"success": "✅", "error": "❌", "skipped": "⏭️"}
    log(
        event_type="scheduler",
        event_sub=job_name,
        message=f"{emojis.get(status, '▶️')} Job {job_name} — {status}",
        status=status,
        details=details,
    )


def get_daily_summary(target_date: date = None) -> dict:
    """
    Génère le résumé de la journée.
    """
    if not target_date:
        target_date = date.today()

    db = SessionLocal()
    try:
        from sqlalchemy import func as sqlfunc
        from app.models.activity_log import ActivityLog as AL

        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        logs = db.query(AL).filter(
            AL.created_at >= start,
            AL.created_at <= end,
        ).all()

        emails_sent = sum(1 for l in logs if l.event_type == "email_sent")
        emails_received = sum(1 for l in logs if l.event_type == "email_received")
        devis_sent = sum(1 for l in logs if l.event_type == "devis_sent")
        devis_montant = sum(l.metric_value or 0 for l in logs if l.event_type == "devis_sent")
        scraping = sum(l.metric_value or 0 for l in logs if l.event_type == "scraping")
        enriched = sum(l.metric_value or 0 for l in logs if l.event_type == "enrichment")
        errors = sum(1 for l in logs if l.status == "error")
        signed = sum(1 for l in logs if l.event_type == "qualification" and l.event_sub == "signed")

        return {
            "date": str(target_date),
            "emails_envoyes": emails_sent,
            "emails_recus": emails_received,
            "devis_envoyes": devis_sent,
            "devis_montant_total": round(devis_montant, 2),
            "nouveaux_prospects": int(scraping),
            "prospects_enrichis": int(enriched),
            "signatures": signed,
            "erreurs": errors,
            "total_actions": len(logs),
        }
    finally:
        db.close()

# ══════════════════════════════════════════════════════════════
#  CLAUDE IA — Nouveaux logs Phase 3
# ══════════════════════════════════════════════════════════════

def log_claude_tool_call(tool_name: str, arguments: dict, result: any,
                         success: bool = True, execution_time_ms: float = None):
    """Tool Claude exécuté (function calling)."""
    emoji = "🔧" if success else "❌"
    status = "success" if success else "error"
    log(
        event_type="claude_tool",
        event_sub=tool_name,
        message=f"{emoji} Tool '{tool_name}' exécuté",
        status=status,
        details={
            "tool": tool_name,
            "arguments": arguments,
            "result": str(result)[:500],  # Limiter taille
            "execution_time_ms": execution_time_ms
        },
        ia_decision=f"Tool {tool_name} called with {len(arguments)} args"
    )


def log_claude_decision(decision_type: str, action_taken: str,
                        reasoning: str, autonomous: bool,
                        escalated: bool = False, details: dict = None):
    """Décision autonome de Claude."""
    if escalated:
        emoji = "⚠️"
        status = "warning"
    elif autonomous:
        emoji = "🤖"
        status = "success"
    else:
        emoji = "🙋"
        status = "info"

    log(
        event_type="claude_decision",
        event_sub=decision_type,
        message=f"{emoji} {decision_type} — {action_taken}",
        status=status,
        details={
            "decision_type": decision_type,
            "action": action_taken,
            "autonomous": autonomous,
            "escalated": escalated,
            **(details or {})
        },
        ia_decision=reasoning
    )


def log_claude_briefing(briefing_type: str, recipient: str = "Mohand",
                        content_preview: str = None):
    """Briefing Claude envoyé."""
    emoji = "🌅" if briefing_type == "daily" else "📊"
    log(
        event_type="claude_briefing",
        event_sub=briefing_type,
        message=f"{emoji} Briefing {briefing_type} envoyé à {recipient}",
        status="success",
        details={
            "type": briefing_type,
            "recipient": recipient,
            "preview": content_preview[:200] if content_preview else None
        }
    )


def log_claude_optimization(optimization_type: str, action: str,
                            metrics_before: dict = None, metrics_after: dict = None):
    """Optimisation automatique de Claude."""
    log(
        event_type="claude_optimization",
        event_sub=optimization_type,
        message=f"🔧 Optimization: {action}",
        status="success",
        details={
            "type": optimization_type,
            "action": action,
            "before": metrics_before,
            "after": metrics_after
        },
        ia_decision=f"Auto-optimization: {action}"
    )


def log_claude_escalation(reason: str, context: dict, priority: str,
                          decision_id: int = None):
    """Escalation à humain."""
    emojis = {"urgent": "🚨", "high": "🔴", "medium": "🟠", "low": "🟡"}
    emoji = emojis.get(priority, "⚠️")

    log(
        event_type="claude_escalation",
        event_sub=priority,
        message=f"{emoji} Escalation {priority}: {reason}",
        status="warning",
        details={
            "reason": reason,
            "priority": priority,
            "context": context,
            "decision_id": decision_id
        },
        ia_decision=f"Escalated: {reason}"
    )


def log_claude_conversation(message_from: str, message_preview: str,
                             response_preview: str = None):
    """Conversation Telegram avec Claude."""
    emoji = "💬"
    log(
        event_type="claude_conversation",
        event_sub="telegram",
        message=f"{emoji} Conversation: {message_from}",
        status="info",
        details={
            "from": message_from,
            "message": message_preview[:200],
            "response": response_preview[:200] if response_preview else None
        }
    )


def log_claude_learning(learning_type: str, pattern: str, confidence: float,
                        sample_size: int = None):
    """Claude a appris un nouveau pattern."""
    log(
        event_type="claude_learning",
        event_sub=learning_type,
        message=f"🧠 Learning: {pattern}",
        status="success",
        metric_value=confidence,
        details={
            "type": learning_type,
            "pattern": pattern,
            "confidence": confidence,
            "sample_size": sample_size
        },
        ia_decision=f"Pattern learned: {pattern}"
    )
