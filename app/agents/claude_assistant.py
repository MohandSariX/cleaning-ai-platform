"""
Claude Assistant — Agent principal de Claude l'associée IA
Génération de briefings, rapports, prise de décisions autonomes
"""
import logging
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.agents.claude_memory import retrieve
from sqlalchemy import func

logger = logging.getLogger("proprexis.claude_assistant")


def generate_daily_briefing() -> str:
    """
    Génère le briefing quotidien pour Mohand.
    Appelé automatiquement chaque matin à 8h par le scheduler.

    Returns:
        Message formaté Markdown pour Telegram
    """
    db = SessionLocal()
    try:
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        # Stats globales
        total_prospects = db.query(Prospect).count()
        avg_score = db.query(func.avg(Prospect.lead_score)).scalar() or 0

        # Prospects ajoutés hier
        new_yesterday = db.query(Prospect).filter(
            Prospect.created_at >= yesterday
        ).count()

        # Top prospects
        top_prospects = db.query(Prospect).filter(
            Prospect.email.isnot(None),
            Prospect.lead_score >= 60
        ).order_by(Prospect.lead_score.desc()).limit(5).all()

        # Construire le briefing
        lines = [
            f"🌅 *BRIEFING DU {today.strftime('%d %B %Y').upper()}*\n",
            f"📊 *CRM*",
            f"  • Total prospects : *{total_prospects}*",
            f"  • Nouveaux hier : {new_yesterday}",
            f"  • Score moyen : {avg_score:.1f}/100\n",
        ]

        if top_prospects:
            lines.append("🏆 *TOP 5 PROSPECTS*")
            for i, p in enumerate(top_prospects, 1):
                lines.append(f"  {i}. *{p.company_name}* — {p.city} ({p.lead_score:.0f}/100)")
            lines.append("")

        lines.append("🎯 *PLAN DU JOUR*")
        lines.append("  1. Enrichissement Pappers (automatique 6h)")
        lines.append("  2. Email Finder (automatique 7h)")
        lines.append("  3. Prospection emails (automatique toutes les 10min)")
        lines.append("")

        lines.append("💡 *BESOIN D'ACTION*")
        lines.append("  • Ajouter crédits Anthropic API pour activer Claude")
        lines.append("  • Lancer 1er cycle d'enrichissement complet")

        return "\n".join(lines)

    finally:
        db.close()


def generate_weekly_report() -> str:
    """
    Génère le rapport hebdomadaire.
    Appelé automatiquement chaque lundi à 9h.

    Returns:
        Message formaté Markdown pour Telegram
    """
    db = SessionLocal()
    try:
        today = datetime.now()
        week_ago = today - timedelta(days=7)

        # Stats de la semaine
        new_this_week = db.query(Prospect).filter(
            Prospect.created_at >= week_ago
        ).count()

        avg_score = db.query(func.avg(Prospect.lead_score)).scalar() or 0

        lines = [
            f"📊 *RAPPORT HEBDO — Semaine du {week_ago.strftime('%d/%m')} au {today.strftime('%d/%m')}*\n",
            f"🎯 *PROSPECTION*",
            f"  • Nouveaux prospects : *{new_this_week}*",
            f"  • Score moyen : {avg_score:.1f}/100\n",
            f"💡 *RECOMMANDATIONS*",
            f"  • Activer prospection email une fois enrichissement terminé",
            f"  • Configurer SendGrid pour augmenter quota emails",
        ]

        return "\n".join(lines)

    finally:
        db.close()
