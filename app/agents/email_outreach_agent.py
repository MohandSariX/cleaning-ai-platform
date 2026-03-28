"""
Agent d'envoi automatique des emails de prospection.
- Max 50 emails/jour
- Espacés de 10 minutes
- Anti-doublon strict
- Suivi complet en base
- Fenêtre 9h-18h uniquement
"""

import logging
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.models.email_log import EmailLog
from app.agents.email_templates import get_template, render_template
from app.agents.gmail_agent import send_prospection_email
from app.agents.telegram_notifier import send_message as tg

logger = logging.getLogger("proprexis.outreach")

MAX_EMAILS_PAR_JOUR = 50
HEURE_DEBUT = 9
HEURE_FIN = 18


def can_send_now() -> bool:
    """Vérifie qu'on est dans la fenêtre d'envoi 9h-18h."""
    now = datetime.now()
    return HEURE_DEBUT <= now.hour < HEURE_FIN


def get_emails_envoyes_aujourd_hui(db: Session) -> int:
    """Compte les emails envoyés aujourd'hui."""
    today = date.today()
    return db.query(EmailLog).filter(
        func.date(EmailLog.sent_at) == today,
        EmailLog.email_type == "prospection"
    ).count()


def get_prospects_a_contacter(db: Session, limit: int) -> list:
    """
    Retourne les prospects éligibles à la prospection :
    - Score >= 50
    - Statut 'scored'
    - Email présent
    - Jamais contactés (pas dans email_log)
    - Triés par score décroissant
    """
    # Sous-requête : emails déjà envoyés
    from sqlalchemy import select
    deja_contactes = select(EmailLog.prospect_id).where(
        EmailLog.email_type == "prospection"
    )

    prospects = db.query(Prospect).filter(
        Prospect.status == "scored",
        Prospect.email != None,
        Prospect.email != "",
        Prospect.lead_score >= 50,
        ~Prospect.id.in_(deja_contactes)
    ).order_by(Prospect.lead_score.desc()).limit(limit).all()

    return prospects


def send_one_prospection_email(prospect: Prospect, db: Session) -> bool:
    """
    Envoie un email de prospection à un prospect.
    Enregistre le résultat dans email_log.
    """
    try:
        template = get_template(prospect.industry, relance=False)
        objet, corps = render_template(template, prospect)

        success = send_prospection_email(
            to=prospect.email,
            subject=objet,
            body=corps
        )

        # Enregistrer dans email_log
        log = EmailLog(
            prospect_id=prospect.id,
            email_type="prospection",
            recipient=prospect.email,
            subject=objet,
            status="sent" if success else "failed",
            sent_at=datetime.now(),
        )
        db.add(log)

        if success:
            prospect.status = "email_generated"
            prospect.last_contacted = datetime.now()
            logger.info(f"✅ Email envoyé à {prospect.company_name} ({prospect.email})")
        else:
            logger.warning(f"❌ Échec envoi à {prospect.company_name}")

        db.commit()
        return success

    except Exception as e:
        logger.error(f"Erreur envoi {prospect.company_name} : {e}")
        db.rollback()
        return False


def run_outreach_batch():
    """
    Envoie le prochain email de la file.
    Appelé toutes les 10 minutes par le scheduler entre 9h et 18h.
    """
    if not can_send_now():
        return

    db = SessionLocal()
    try:
        # Vérifier quota journalier
        envoyes = get_emails_envoyes_aujourd_hui(db)
        if envoyes >= MAX_EMAILS_PAR_JOUR:
            logger.info(f"📭 Quota journalier atteint ({envoyes}/{MAX_EMAILS_PAR_JOUR})")
            return

        # Prendre 1 seul prospect (envoi espacé de 10 min)
        prospects = get_prospects_a_contacter(db, limit=1)
        if not prospects:
            logger.info("📭 Aucun prospect éligible en attente")
            return

        prospect = prospects[0]
        success = send_one_prospection_email(prospect, db)

        if success:
            restants = MAX_EMAILS_PAR_JOUR - envoyes - 1
            logger.info(f"📧 {envoyes + 1}/{MAX_EMAILS_PAR_JOUR} emails envoyés aujourd'hui — {restants} restants")

    except Exception as e:
        logger.error(f"Erreur batch outreach : {e}")
    finally:
        db.close()


def run_relances():
    """
    Envoie des relances aux prospects contactés il y a 3 jours sans réponse.
    Appelé une fois par jour à 10h.
    """
    db = SessionLocal()
    try:
        seuil = datetime.now() - timedelta(days=3)

        # Prospects contactés il y a 3 jours, statut toujours "email_generated"
        a_relancer = db.query(Prospect).filter(
            Prospect.status == "email_generated",
            Prospect.last_contacted != None,
            Prospect.last_contacted <= seuil,
            Prospect.email != None,
        ).order_by(Prospect.lead_score.desc()).limit(10).all()

        if not a_relancer:
            return

        envoyes = 0
        for prospect in a_relancer:
            # Vérifier pas déjà relancé
            relance_existante = db.query(EmailLog).filter(
                EmailLog.prospect_id == prospect.id,
                EmailLog.email_type == "relance"
            ).first()
            if relance_existante:
                continue

            template = get_template(prospect.industry, relance=True)
            objet, corps = render_template(template, prospect)

            success = send_prospection_email(
                to=prospect.email,
                subject=objet,
                body=corps
            )

            log = EmailLog(
                prospect_id=prospect.id,
                email_type="relance",
                recipient=prospect.email,
                subject=objet,
                status="sent" if success else "failed",
                sent_at=datetime.now(),
            )
            db.add(log)

            if success:
                prospect.last_contacted = datetime.now()
                envoyes += 1

        db.commit()

        if envoyes > 0:
            logger.info(f"📧 {envoyes} relance(s) envoyée(s)")
            tg(f"📧 *{envoyes} relance(s) envoyée(s)* aux prospects contactés il y a 3 jours")

    except Exception as e:
        logger.error(f"Erreur relances : {e}")
    finally:
        db.close()


def get_outreach_stats() -> dict:
    """Retourne les stats d'envoi pour le dashboard."""
    db = SessionLocal()
    try:
        today = date.today()
        envoyes_today = get_emails_envoyes_aujourd_hui(db)

        total_envoyes = db.query(EmailLog).filter(
            EmailLog.email_type == "prospection",
            EmailLog.status == "sent"
        ).count()

        total_relances = db.query(EmailLog).filter(
            EmailLog.email_type == "relance",
            EmailLog.status == "sent"
        ).count()

        en_attente = db.query(Prospect).filter(
            Prospect.status == "scored",
            Prospect.email != None,
            Prospect.lead_score >= 50,
        ).count()

        return {
            "envoyes_aujourd_hui": envoyes_today,
            "quota_journalier": MAX_EMAILS_PAR_JOUR,
            "total_envoyes": total_envoyes,
            "total_relances": total_relances,
            "en_attente": en_attente,
            "prochaine_envoi": "Dans 10 min" if can_send_now() and envoyes_today < MAX_EMAILS_PAR_JOUR else "Hors fenêtre (9h-18h)",
        }
    finally:
        db.close()