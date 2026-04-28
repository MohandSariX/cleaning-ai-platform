"""
Claude Assistant — Agent principal de Claude l'associée IA
Génération de briefings, rapports, prise de décisions autonomes
"""
import logging
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.models.email_log import EmailLog
from app.agents.claude_memory import retrieve
from sqlalchemy import func, and_

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
        week_ago = today - timedelta(days=7)

        # ═══════════════════════════════════════════════════════
        #  STATS GLOBALES
        # ═══════════════════════════════════════════════════════

        total_prospects = db.query(Prospect).count()
        with_email = db.query(Prospect).filter(Prospect.email.isnot(None)).count()
        with_phone = db.query(Prospect).filter(Prospect.phone.isnot(None)).count()
        avg_score = db.query(func.avg(Prospect.lead_score)).scalar() or 0

        # Prospects ajoutés hier
        new_yesterday = db.query(Prospect).filter(
            Prospect.created_at >= yesterday
        ).count()

        # Prospects ajoutés cette semaine
        new_this_week = db.query(Prospect).filter(
            Prospect.created_at >= week_ago
        ).count()

        # ═══════════════════════════════════════════════════════
        #  TOP PROSPECTS
        # ═══════════════════════════════════════════════════════

        top_prospects = db.query(Prospect).filter(
            Prospect.email.isnot(None),
            Prospect.lead_score >= 50,
            Prospect.status.in_(["new", "scored"])
        ).order_by(Prospect.lead_score.desc()).limit(5).all()

        # ═══════════════════════════════════════════════════════
        #  PROSPECTION (EMAILS)
        # ═══════════════════════════════════════════════════════

        # Emails envoyés hier
        emails_sent_yesterday = db.query(EmailLog).filter(
            EmailLog.sent_at >= yesterday,
            EmailLog.email_type == "prospection"
        ).count()

        # Emails envoyés cette semaine
        emails_sent_week = db.query(EmailLog).filter(
            EmailLog.sent_at >= week_ago,
            EmailLog.email_type == "prospection"
        ).count()

        # Prospects contactés non répondus (> 3 jours)
        three_days_ago = today - timedelta(days=3)
        to_followup = db.query(Prospect).filter(
            Prospect.status == "contacted",
            Prospect.last_contacted.isnot(None),
            Prospect.last_contacted < three_days_ago
        ).count()

        # Prospects répondu
        replied = db.query(Prospect).filter(Prospect.status == "replied").count()

        # ═══════════════════════════════════════════════════════
        #  DISTRIBUTION SCORES
        # ═══════════════════════════════════════════════════════

        high_score = db.query(Prospect).filter(Prospect.lead_score >= 70).count()
        medium_score = db.query(Prospect).filter(
            and_(Prospect.lead_score >= 50, Prospect.lead_score < 70)
        ).count()
        low_score = db.query(Prospect).filter(
            and_(Prospect.lead_score >= 30, Prospect.lead_score < 50)
        ).count()

        # ═══════════════════════════════════════════════════════
        #  QUOTA EMAIL
        # ═══════════════════════════════════════════════════════

        quota_daily = int(retrieve('email_quota_daily')['value']) if retrieve('email_quota_daily') else 50
        quota_used_today = db.query(EmailLog).filter(
            EmailLog.sent_at >= today.replace(hour=0, minute=0, second=0),
            EmailLog.email_type == "prospection"
        ).count()

        # ═══════════════════════════════════════════════════════
        #  CONSTRUCTION DU BRIEFING
        # ═══════════════════════════════════════════════════════

        lines = [
            f"🌅 *BRIEFING DU {today.strftime('%d %B %Y').upper()}*\n",
            f"📊 *CRM — VUE D'ENSEMBLE*",
            f"  • Total prospects : *{total_prospects:,}*",
            f"  • Avec email : {with_email} ({with_email/total_prospects*100:.0f}%)" if total_prospects > 0 else "  • Avec email : 0",
            f"  • Avec téléphone : {with_phone} ({with_phone/total_prospects*100:.0f}%)" if total_prospects > 0 else "  • Avec téléphone : 0",
            f"  • Score moyen : {avg_score:.1f}/100",
            f"  • Nouveaux hier : {new_yesterday} | Cette semaine : {new_this_week}\n",
        ]

        # Distribution scores
        lines.append("📈 *QUALITÉ DES PROSPECTS*")
        lines.append(f"  🔥 Score ≥70 : *{high_score}* prospects")
        lines.append(f"  ⚡ Score 50-69 : *{medium_score}* prospects")
        lines.append(f"  🌱 Score 30-49 : *{low_score}* prospects\n")

        # Top 5 prospects
        if top_prospects:
            lines.append("🏆 *TOP 5 PROSPECTS À CONTACTER*")
            for i, p in enumerate(top_prospects, 1):
                score_emoji = "🔥" if p.lead_score >= 70 else "⚡" if p.lead_score >= 50 else "🌱"
                lines.append(f"  {i}. {score_emoji} *{p.company_name[:30]}* — {p.city} ({p.lead_score:.0f}/100)")
            lines.append("")
        else:
            lines.append("⚠️ *Aucun prospect prioritaire à contacter*\n")

        # Prospection
        lines.append("📧 *PROSPECTION EMAIL*")
        lines.append(f"  • Envoyés hier : {emails_sent_yesterday}")
        lines.append(f"  • Envoyés cette semaine : {emails_sent_week}")
        lines.append(f"  • Quota aujourd'hui : {quota_used_today}/{quota_daily}")
        if replied > 0:
            lines.append(f"  • Réponses reçues : *{replied}* 🎉")
        if to_followup > 0:
            lines.append(f"  • À relancer (>3j) : *{to_followup}* ⚠️")
        lines.append("")

        # Plan du jour
        lines.append("🎯 *PLAN DU JOUR*")

        actions = []

        if quota_used_today < quota_daily and with_email > emails_sent_week:
            remaining = quota_daily - quota_used_today
            actions.append(f"  1. Envoyer {remaining} emails prospection (auto toutes les 10min)")

        if to_followup > 0:
            actions.append(f"  2. Relancer {min(to_followup, 10)} prospects (auto à 10h)")

        if high_score > 0 and emails_sent_yesterday == 0:
            actions.append(f"  3. Contacter les {high_score} prospects prioritaires (score ≥70)")

        # Jobs automatiques
        actions.append("  • Enrichissement Pappers (auto 6h)")
        actions.append("  • Email Finder (auto 7h)")
        actions.append("  • Scoring (auto après enrichissement)")

        if not actions:
            lines.append("  ✅ Tout est à jour — journée calme")
        else:
            lines.extend(actions)

        lines.append("")

        # Alertes
        alerts = []
        if with_email < total_prospects * 0.3:
            alerts.append("  🟡 Seulement 26% prospects ont un email → Lancer Email Finder batch")
        if avg_score < 30:
            alerts.append("  🟡 Score moyen faible (24.6) → Enrichir via Pappers")
        if emails_sent_week == 0 and with_email > 100:
            alerts.append("  🔴 Aucun email envoyé cette semaine → Activer prospection")

        if alerts:
            lines.append("⚠️ *ALERTES*")
            lines.extend(alerts)
            lines.append("")

        # Note finale
        lines.append("💡 *BESOIN D'AIDE*")
        lines.append("  Demande-moi n'importe quoi :")
        lines.append("  • 'Claude, envoie 20 emails aux meilleurs prospects'")
        lines.append("  • 'Montre-moi les prospects du 94'")
        lines.append("  • 'Quel est le taux de réponse cette semaine ?'")

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
        two_weeks_ago = today - timedelta(days=14)

        # ═══════════════════════════════════════════════════════
        #  STATS PROSPECTION
        # ═══════════════════════════════════════════════════════

        # Nouveaux prospects
        new_this_week = db.query(Prospect).filter(
            Prospect.created_at >= week_ago
        ).count()

        new_last_week = db.query(Prospect).filter(
            and_(
                Prospect.created_at >= two_weeks_ago,
                Prospect.created_at < week_ago
            )
        ).count()

        # Emails
        emails_sent_week = db.query(EmailLog).filter(
            EmailLog.sent_at >= week_ago,
            EmailLog.email_type == "prospection"
        ).count()

        emails_sent_last_week = db.query(EmailLog).filter(
            and_(
                EmailLog.sent_at >= two_weeks_ago,
                EmailLog.sent_at < week_ago
            ),
            EmailLog.email_type == "prospection"
        ).count()

        # Réponses
        replied_week = db.query(Prospect).filter(
            Prospect.status == "replied",
            Prospect.updated_at >= week_ago
        ).count()

        # Taux réponse
        reply_rate = (replied_week / emails_sent_week * 100) if emails_sent_week > 0 else 0

        # ═══════════════════════════════════════════════════════
        #  STATS GLOBALES
        # ═══════════════════════════════════════════════════════

        total_prospects = db.query(Prospect).count()
        avg_score = db.query(func.avg(Prospect.lead_score)).scalar() or 0

        # ═══════════════════════════════════════════════════════
        #  MEILLEURS PERFORMERS
        # ═══════════════════════════════════════════════════════

        # Meilleure journée emails
        best_day_query = db.query(
            func.date(EmailLog.sent_at).label('day'),
            func.count(EmailLog.id).label('count')
        ).filter(
            EmailLog.sent_at >= week_ago,
            EmailLog.email_type == "prospection"
        ).group_by(func.date(EmailLog.sent_at)).order_by(func.count(EmailLog.id).desc()).first()

        best_day = best_day_query[0].strftime("%A %d/%m") if best_day_query else "N/A"
        best_day_count = best_day_query[1] if best_day_query else 0

        # Top secteur
        top_industry = db.query(
            Prospect.industry,
            func.count(Prospect.id).label('count')
        ).filter(
            Prospect.created_at >= week_ago,
            Prospect.industry.isnot(None)
        ).group_by(Prospect.industry).order_by(func.count(Prospect.id).desc()).first()

        # ═══════════════════════════════════════════════════════
        #  CONSTRUCTION DU RAPPORT
        # ═══════════════════════════════════════════════════════

        # Evolution
        prospect_evolution = ((new_this_week - new_last_week) / new_last_week * 100) if new_last_week > 0 else 0
        email_evolution = ((emails_sent_week - emails_sent_last_week) / emails_sent_last_week * 100) if emails_sent_last_week > 0 else 0

        lines = [
            f"📊 *RAPPORT HEBDO — Semaine du {week_ago.strftime('%d/%m')} au {today.strftime('%d/%m')}*\n",

            f"🎯 *KPIs PROSPECTION*",
            f"  📧 Emails envoyés : *{emails_sent_week}* {'↗️' if email_evolution > 0 else '↘️'} {abs(email_evolution):.0f}% vs semaine dernière",
            f"  📬 Réponses reçues : *{replied_week}* (taux {reply_rate:.1f}%)",
            f"  🆕 Nouveaux prospects : *{new_this_week}* {'↗️' if prospect_evolution > 0 else '↘️'} {abs(prospect_evolution):.0f}%\n",

            f"📈 *PERFORMANCE*",
            f"  🏆 Meilleur jour : {best_day} ({best_day_count} emails)",
        ]

        if top_industry:
            lines.append(f"  🏆 Top secteur : {top_industry[0]} ({top_industry[1]} prospects)")

        lines.append(f"  📊 Score moyen CRM : {avg_score:.1f}/100\n")

        # Base CRM
        lines.append(f"📊 *BASE CRM*")
        lines.append(f"  • Total : *{total_prospects:,}* prospects")

        # Distribution par statut
        status_dist = db.query(
            Prospect.status,
            func.count(Prospect.id)
        ).group_by(Prospect.status).all()

        for status, count in status_dist:
            emoji = {
                "new": "🆕",
                "scored": "📊",
                "contacted": "📧",
                "replied": "💬",
                "to_followup": "⏰",
                "signed": "✅",
                "lost": "❌"
            }.get(status, "•")
            lines.append(f"  {emoji} {status}: {count}")

        lines.append("")

        # Recommandations
        lines.append("💡 *RECOMMANDATIONS*")

        if reply_rate < 2:
            lines.append("  🔴 Taux réponse faible (<2%) → A/B tester templates emails")
        elif reply_rate < 5:
            lines.append("  🟡 Taux réponse moyen (2-5%) → Améliorer ciblage")
        else:
            lines.append("  ✅ Taux réponse bon (>5%) → Continuer stratégie")

        if emails_sent_week < 200:
            lines.append("  🟡 Volume emails faible → Augmenter quota quotidien (SendGrid)")

        if avg_score < 35:
            lines.append("  🟡 Score moyen faible → Lancer cycle enrichissement Pappers")

        lines.append("")

        # Plan semaine prochaine
        lines.append("🎯 *PLAN SEMAINE PROCHAINE*")
        lines.append("  1. Augmenter volume prospection (+50%)")
        lines.append("  2. Enrichir top 500 prospects via Pappers")
        lines.append("  3. A/B tester 2 templates emails")
        lines.append("  4. Relancer tous prospects >7j sans réponse")

        return "\n".join(lines)

    finally:
        db.close()


def get_crm_stats() -> dict:
    """
    Retourne les statistiques CRM pour les tools Claude.

    Returns:
        Dict avec toutes les stats importantes
    """
    db = SessionLocal()
    try:
        today = datetime.now()
        week_ago = today - timedelta(days=7)

        stats = {
            "total_prospects": db.query(Prospect).count(),
            "with_email": db.query(Prospect).filter(Prospect.email.isnot(None)).count(),
            "with_phone": db.query(Prospect).filter(Prospect.phone.isnot(None)).count(),
            "avg_score": db.query(func.avg(Prospect.lead_score)).scalar() or 0,
            "high_score": db.query(Prospect).filter(Prospect.lead_score >= 70).count(),
            "replied": db.query(Prospect).filter(Prospect.status == "replied").count(),
            "new_this_week": db.query(Prospect).filter(Prospect.created_at >= week_ago).count(),
            "emails_sent_today": db.query(EmailLog).filter(
                EmailLog.sent_at >= today.replace(hour=0, minute=0, second=0)
            ).count()
        }

        return stats
    finally:
        db.close()
