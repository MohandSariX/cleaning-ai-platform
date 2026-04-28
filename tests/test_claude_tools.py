"""
Tests pour Claude Tools — Function calling CRM
"""
import pytest
from app.agents.claude_tools import (
    get_prospects, update_prospect,
    send_prospecting_email, enrich_prospect_pappers,
    generate_quote, get_crm_statistics
)


def test_get_prospects():
    """Test récupération prospects."""
    # Sans filtres
    prospects = get_prospects(limit=10)
    assert isinstance(prospects, list), "Should return list"

    # Avec filtres
    prospects_filtered = get_prospects(
        filters={"min_score": 30, "has_email": True},
        limit=5
    )
    assert isinstance(prospects_filtered, list), "Should return list"
    if len(prospects_filtered) > 0:
        assert prospects_filtered[0]["lead_score"] >= 30, "Score should match filter"


def test_get_crm_statistics():
    """Test statistiques CRM."""
    # Stats semaine
    stats = get_crm_statistics("week")
    assert "total_prospects" in stats, "Should have total_prospects"
    assert "avg_score" in stats, "Should have avg_score"
    assert "emails_sent" in stats, "Should have emails_sent"
    assert stats["period"] == "week", "Period should match"

    # Stats aujourd'hui
    stats_today = get_crm_statistics("today")
    assert stats_today["period"] == "today"


def test_update_prospect():
    """Test mise à jour prospect."""
    # Récupérer un prospect
    prospects = get_prospects(limit=1)
    if len(prospects) == 0:
        pytest.skip("No prospects in database")

    prospect_id = prospects[0]["id"]

    # Mettre à jour
    success = update_prospect(prospect_id, {
        "notes": "Test note added by test suite"
    })

    assert success, "Update should succeed"


def test_send_prospecting_email():
    """Test envoi email prospection (dry run)."""
    # Récupérer prospect avec email
    prospects = get_prospects(filters={"has_email": True}, limit=1)
    if len(prospects) == 0:
        pytest.skip("No prospects with email")

    prospect_id = prospects[0]["id"]

    # Envoyer email (mock)
    result = send_prospecting_email(prospect_id, template_name="default")

    assert isinstance(result, dict), "Should return dict"
    assert "success" in result, "Should have success key"


def test_generate_quote():
    """Test génération devis."""
    # Récupérer un prospect
    prospects = get_prospects(limit=1)
    if len(prospects) == 0:
        pytest.skip("No prospects in database")

    prospect_id = prospects[0]["id"]

    # Générer devis
    result = generate_quote(
        prospect_id=prospect_id,
        service_type="bureaux",
        surface_m2=100,
        frequency="hebdo"
    )

    assert isinstance(result, dict), "Should return dict"
    assert "success" in result or "montant_ttc" in result, "Should have result data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
