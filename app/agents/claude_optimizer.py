"""
Claude Optimizer — Optimisation continue et A/B testing
Analyse les patterns de succès et ajuste la stratégie automatiquement
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.email_log import EmailLog
from app.models.prospect import Prospect
from app.agents.claude_memory import store, retrieve, search
from sqlalchemy import func, and_

logger = logging.getLogger("proprexis.claude_optimizer")


def analyze_email_performance() -> Dict[str, Any]:
    """
    Analyse les performances des emails de prospection.

    Returns:
        Dict avec métriques et recommandations
    """
    db = SessionLocal()
    try:
        week_ago = datetime.now() - timedelta(days=7)

        # Emails envoyés
        total_sent = db.query(EmailLog).filter(
            EmailLog.sent_at >= week_ago,
            EmailLog.email_type == "prospection"
        ).count()

        # Prospects ayant répondu
        replied = db.query(Prospect).filter(
            Prospect.status == "replied",
            Prospect.updated_at >= week_ago
        ).count()

        # Taux de réponse
        reply_rate = (replied / total_sent * 100) if total_sent > 0 else 0

        # Performance par jour
        daily_perf = db.query(
            func.date(EmailLog.sent_at).label('day'),
            func.count(EmailLog.id).label('sent')
        ).filter(
            EmailLog.sent_at >= week_ago
        ).group_by(func.date(EmailLog.sent_at)).all()

        # Meilleur jour
        best_day = max(daily_perf, key=lambda x: x[1]) if daily_perf else None

        analysis = {
            "total_sent": total_sent,
            "replied": replied,
            "reply_rate": reply_rate,
            "best_day": best_day[0].strftime("%A") if best_day else "N/A",
            "best_day_count": best_day[1] if best_day else 0,
            "recommendations": []
        }

        # Recommandations
        if reply_rate < 2:
            analysis["recommendations"].append({
                "type": "low_reply_rate",
                "message": "Taux réponse <2% → Revoir templates emails",
                "action": "ab_test_templates"
            })
        elif reply_rate < 5:
            analysis["recommendations"].append({
                "type": "medium_reply_rate",
                "message": "Taux réponse 2-5% → Améliorer ciblage",
                "action": "refine_targeting"
            })

        if total_sent < 200:
            analysis["recommendations"].append({
                "type": "low_volume",
                "message": f"Volume faible ({total_sent}/semaine) → Augmenter quota",
                "action": "increase_quota"
            })

        return analysis

    finally:
        db.close()


def learn_from_successes() -> None:
    """
    Analyse les prospects convertis et stocke les patterns en mémoire.
    """
    db = SessionLocal()
    try:
        # Prospects signés
        signed = db.query(Prospect).filter(Prospect.status == "signed").all()

        if not signed:
            return

        # Analyser patterns communs
        industries = {}
        cities = {}
        score_ranges = {"high": 0, "medium": 0, "low": 0}

        for p in signed:
            # Industrie
            ind = p.industry or "unknown"
            industries[ind] = industries.get(ind, 0) + 1

            # Ville
            city = p.city or "unknown"
            cities[city] = cities.get(city, 0) + 1

            # Score range
            if p.lead_score >= 70:
                score_ranges["high"] += 1
            elif p.lead_score >= 50:
                score_ranges["medium"] += 1
            else:
                score_ranges["low"] += 1

        # Stocker insights
        if industries:
            top_industry = max(industries, key=industries.get)
            store(
                key="top_converting_industry",
                value=top_industry,
                context="learning",
                meta_data={
                    "conversions": industries[top_industry],
                    "total_signed": len(signed)
                }
            )

        if cities:
            top_city = max(cities, key=cities.get)
            store(
                key="top_converting_city",
                value=top_city,
                context="learning",
                meta_data={
                    "conversions": cities[top_city],
                    "total_signed": len(signed)
                }
            )

        # Score insights
        store(
            key="conversion_by_score",
            value=f"High:{score_ranges['high']}, Med:{score_ranges['medium']}, Low:{score_ranges['low']}",
            context="learning",
            meta_data=score_ranges
        )

        logger.info(f"Learned from {len(signed)} successful conversions")

    finally:
        db.close()


def suggest_optimizations() -> List[Dict[str, Any]]:
    """
    Suggère des optimisations basées sur les données.

    Returns:
        Liste de suggestions
    """
    suggestions = []

    # Récupérer learnings
    top_industry = retrieve("top_converting_industry")
    top_city = retrieve("top_converting_city")

    if top_industry:
        suggestions.append({
            "type": "targeting",
            "priority": "high",
            "message": f"Focus sur '{top_industry['value']}' (meilleur taux conversion)",
            "action": "prioritize_industry",
            "params": {"industry": top_industry['value']}
        })

    if top_city:
        suggestions.append({
            "type": "targeting",
            "priority": "medium",
            "message": f"Cibler davantage '{top_city['value']}'",
            "action": "prioritize_city",
            "params": {"city": top_city['value']}
        })

    # Analyser performance emails
    email_perf = analyze_email_performance()
    if email_perf["reply_rate"] < 3:
        suggestions.append({
            "type": "communication",
            "priority": "high",
            "message": f"Taux réponse faible ({email_perf['reply_rate']:.1f}%) → A/B test templates",
            "action": "ab_test_emails"
        })

    return suggestions


def apply_optimization(optimization: Dict[str, Any]) -> bool:
    """
    Applique une optimisation automatiquement si possible.

    Args:
        optimization: Dict avec type, action, params

    Returns:
        True si appliqué avec succès
    """
    action = optimization.get("action")

    if action == "prioritize_industry":
        industry = optimization["params"]["industry"]
        # Stocker en mémoire pour que l'IA priorise
        store(
            key="priority_industry",
            value=industry,
            context="strategy",
            meta_data={"auto_optimized": True, "date": datetime.now().isoformat()}
        )
        logger.info(f"Optimization applied: prioritize industry '{industry}'")
        return True

    elif action == "prioritize_city":
        city = optimization["params"]["city"]
        store(
            key="priority_city",
            value=city,
            context="strategy",
            meta_data={"auto_optimized": True, "date": datetime.now().isoformat()}
        )
        logger.info(f"Optimization applied: prioritize city '{city}'")
        return True

    elif action == "ab_test_emails":
        # Marquer pour A/B testing
        store(
            key="ab_test_active",
            value="email_templates",
            context="strategy",
            meta_data={"variants": ["default", "personalized"], "started": datetime.now().isoformat()}
        )
        logger.info("A/B test started for email templates")
        return True

    return False


def run_optimization_cycle() -> Dict[str, Any]:
    """
    Lance un cycle complet d'optimisation.

    Returns:
        Dict avec résultats
    """
    logger.info("🔧 Starting optimization cycle...")

    # 1. Apprendre des succès
    learn_from_successes()

    # 2. Générer suggestions
    suggestions = suggest_optimizations()

    # 3. Appliquer optimisations automatiques
    applied = []
    for suggestion in suggestions:
        if suggestion["priority"] == "high":
            if apply_optimization(suggestion):
                applied.append(suggestion)

    result = {
        "suggestions_generated": len(suggestions),
        "optimizations_applied": len(applied),
        "suggestions": suggestions,
        "applied": applied
    }

    logger.info(f"✅ Optimization cycle complete: {len(applied)} applied, {len(suggestions)} total")

    return result
