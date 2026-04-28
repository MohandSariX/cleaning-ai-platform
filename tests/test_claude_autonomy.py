"""
Tests pour Claude Autonomy — Décisions autonomes et escalation
"""
import pytest
from app.agents.claude_autonomy import (
    can_act_autonomously, should_escalate,
    get_daily_counters, get_autonomy_status
)


def test_can_act_autonomously_email():
    """Test autonomie envoi email."""
    # Sous quota
    can_act, reason = can_act_autonomously(
        "email_prospection",
        {"daily_sent": 30}
    )
    assert can_act is True, "Should be autonomous under quota"

    # Au quota
    can_act, reason = can_act_autonomously(
        "email_prospection",
        {"daily_sent": 50}
    )
    assert can_act is False, "Should not be autonomous at quota"


def test_can_act_autonomously_devis():
    """Test autonomie génération devis."""
    # Devis petit
    can_act, reason = can_act_autonomously(
        "generate_devis",
        {"amount": 5000}
    )
    assert can_act is True, "Should be autonomous for small devis"

    # Devis gros
    can_act, reason = can_act_autonomously(
        "generate_devis",
        {"amount": 18000}
    )
    assert can_act is False, "Should not be autonomous for large devis"


def test_can_act_autonomously_negotiation():
    """Test autonomie négociation."""
    # Remise faible
    can_act, reason = can_act_autonomously(
        "negotiate_price",
        {"discount_percent": 10}
    )
    assert can_act is True, "Should be autonomous for small discount"

    # Remise forte
    can_act, reason = can_act_autonomously(
        "negotiate_price",
        {"discount_percent": 20}
    )
    assert can_act is False, "Should not be autonomous for large discount"


def test_should_escalate_devis():
    """Test escalation devis montant élevé."""
    # Devis normal
    escalate, reason, priority = should_escalate(
        "devis_montant_eleve",
        {"amount": 12000}
    )
    assert escalate is False, "Should not escalate normal devis"

    # Devis élevé
    escalate, reason, priority = should_escalate(
        "devis_montant_eleve",
        {"amount": 18000}
    )
    assert escalate is True, "Should escalate large devis"
    assert priority == "high", "Priority should be high"


def test_should_escalate_negotiation():
    """Test escalation négociation importante."""
    # Remise normale
    escalate, reason, priority = should_escalate(
        "negociation_importante",
        {"discount_percent": 10}
    )
    assert escalate is False, "Should not escalate small discount"

    # Remise importante
    escalate, reason, priority = should_escalate(
        "negociation_importante",
        {"discount_percent": 20}
    )
    assert escalate is True, "Should escalate large discount"


def test_get_daily_counters():
    """Test compteurs quotidiens."""
    counters = get_daily_counters()

    assert "emails_sent" in counters, "Should have emails_sent"
    assert "budget_spent" in counters, "Should have budget_spent"
    assert "date" in counters, "Should have date"
    assert counters["emails_sent"] >= 0, "Emails should be non-negative"
    assert counters["budget_spent"] >= 0, "Budget should be non-negative"


def test_get_autonomy_status():
    """Test status autonomie complet."""
    status = get_autonomy_status()

    assert "emails" in status, "Should have emails section"
    assert "enrichment" in status, "Should have enrichment section"
    assert "limits" in status, "Should have limits section"

    # Vérifier structure emails
    assert "sent_today" in status["emails"]
    assert "quota_daily" in status["emails"]
    assert "remaining" in status["emails"]

    # Vérifier structure enrichment
    assert "spent_today" in status["enrichment"]
    assert "budget_daily" in status["enrichment"]

    # Vérifier limites
    assert status["limits"]["devis_max_autonomous"] == 10000
    assert status["limits"]["discount_max_autonomous"] == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
