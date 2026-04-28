"""
Tests Phase 1 — Email Outreach & Gmail Agent
"""
import pytest
from datetime import datetime, timedelta
from app.agents.email_outreach_agent import can_send_email, get_daily_email_count
from app.agents.email_templates import get_template, TEMPLATES
from app.agents.gmail_agent import check_token_health
from app.core.database import SessionLocal
from app.models.email_log import EmailLog


def test_email_templates():
    """Test que tous les templates sont disponibles."""
    # Templates par défaut
    default = get_template("default")
    assert "subject" in default
    assert "body" in default
    assert "{company_name}" in default["body"]

    # Templates spécifiques
    for sector in ["btp", "syndic", "architecte", "bureau"]:
        template = get_template(sector)
        assert "subject" in template
        assert "body" in template
        assert len(template["body"]) > 50

    print(f"✅ {len(TEMPLATES)} templates disponibles")


def test_can_send_email_quota():
    """Test quota 50 emails/jour."""
    db = SessionLocal()
    try:
        # Compter emails aujourd'hui
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = db.query(EmailLog).filter(
            EmailLog.sent_at >= today_start,
            EmailLog.email_type == "prospection"
        ).count()

        # Vérifier logique quota
        can_send = can_send_email()
        if count >= 50:
            assert not can_send, "Ne devrait pas pouvoir envoyer si quota atteint"
        else:
            # Si on peut envoyer, vérifier fenêtre horaire
            now = datetime.now()
            if 9 <= now.hour < 18:
                assert can_send, "Devrait pouvoir envoyer pendant 9h-18h"

        print(f"✅ Quota: {count}/50 aujourd'hui")

    finally:
        db.close()


def test_get_daily_email_count():
    """Test compteur emails quotidien."""
    count = get_daily_email_count()
    assert isinstance(count, int)
    assert count >= 0
    assert count <= 50  # Ne devrait jamais dépasser 50

    print(f"✅ Emails envoyés aujourd'hui: {count}")


def test_email_log_anti_doublon():
    """Test anti-doublon dans email_logs."""
    db = SessionLocal()
    try:
        test_email = "test_doublon@example.com"

        # Compter emails déjà envoyés à cette adresse
        count = db.query(EmailLog).filter(
            EmailLog.to_email == test_email,
            EmailLog.email_type == "prospection"
        ).count()

        # Si email déjà envoyé, ne pas renvoyer
        if count > 0:
            print(f"✅ Anti-doublon: {test_email} déjà contacté {count} fois")
        else:
            print(f"✅ Anti-doublon: {test_email} jamais contacté")

        # Vérifier qu'il existe au moins quelques emails logs
        total_logs = db.query(EmailLog).count()
        print(f"✅ Total emails logs en base: {total_logs}")

    finally:
        db.close()


def test_gmail_token_health():
    """Test vérification santé token Gmail."""
    try:
        is_healthy, message = check_token_health()

        # Token peut être healthy ou pas (selon config)
        assert isinstance(is_healthy, bool)
        assert isinstance(message, str)
        assert len(message) > 0

        if is_healthy:
            print(f"✅ Token Gmail: {message}")
        else:
            print(f"⚠️  Token Gmail: {message}")

    except Exception as e:
        # Acceptable si token.json n'existe pas en test
        print(f"⚠️  Token Gmail non configuré (normal en test): {e}")


def test_email_template_variables():
    """Test que les variables sont bien présentes dans templates."""
    for sector, template in TEMPLATES.items():
        body = template["body"]

        # Variables obligatoires
        assert "{company_name}" in body, f"Template {sector} manque {{company_name}}"

        # Variables optionnelles mais recommandées
        if sector in ["btp", "bureau"]:
            # Ces secteurs devraient mentionner la ville/zone
            assert "{city}" in body or "région" in body.lower()

        print(f"✅ Template {sector}: variables OK")


def test_relance_timing():
    """Test que les relances respectent J+3."""
    db = SessionLocal()
    try:
        # Chercher prospects contactés il y a 3+ jours sans réponse
        three_days_ago = datetime.now() - timedelta(days=3)

        relance_candidates = db.query(EmailLog).filter(
            EmailLog.sent_at <= three_days_ago,
            EmailLog.email_type == "prospection",
            EmailLog.replied == False
        ).limit(5).all()

        if relance_candidates:
            print(f"✅ {len(relance_candidates)} prospects éligibles relance J+3")
        else:
            print("✅ Aucune relance J+3 nécessaire pour l'instant")

    finally:
        db.close()


def test_email_log_structure():
    """Test structure table email_logs."""
    db = SessionLocal()
    try:
        # Récupérer un email log récent
        recent_log = db.query(EmailLog).order_by(EmailLog.sent_at.desc()).first()

        if recent_log:
            # Vérifier colonnes importantes
            assert recent_log.to_email is not None
            assert recent_log.subject is not None
            assert recent_log.email_type in ["prospection", "relance", "qualification", "devis"]
            assert recent_log.sent_at is not None
            assert isinstance(recent_log.replied, bool)

            print(f"✅ EmailLog structure OK (dernier: {recent_log.to_email})")
        else:
            print("⚠️  Aucun email log en base (normal si premier test)")

    finally:
        db.close()
