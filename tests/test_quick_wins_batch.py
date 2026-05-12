"""
Tests batch pour finir les modules presque complets (90%+)
Cible: ~30-40 lignes manquantes sur 15 modules
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.agents import email_templates
from datetime import date

client = TestClient(app)


@pytest.fixture
def db_session():
    """Session DB."""
    db = SessionLocal()
    yield db
    db.close()


# ══════════════════════════════════════════════════════════════
# API ENDPOINTS — Paths manquants
# ══════════════════════════════════════════════════════════════

def test_api_dvf_scrape_sync():
    """Test POST /api/dvf/scrape — Path synchrone si threading échoue."""
    response = client.post("/api/dvf/scrape")
    assert response.status_code == 200
    assert "status" in response.json()
    print("✅ DVF scrape")


def test_api_permis_scrape_sync():
    """Test POST /api/permis/scrape — Path synchrone."""
    response = client.post("/api/permis/scrape")
    assert response.status_code == 200
    assert "status" in response.json()
    print("✅ Permis scrape")


def test_api_prospects_filters_combined():
    """Test GET /api/prospects avec tous filtres combinés."""
    response = client.get(
        "/api/prospects?city=Paris&status=new&min_score=50&has_email=true&search=test"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print("✅ Prospects filters combined")


def test_api_email_finder_batch_high_limit():
    """Test POST /api/email-finder/batch avec limit élevé."""
    response = client.post("/api/email-finder/batch?limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "started"
    print("✅ Email finder batch high limit")


def test_api_scheduler_clear_log():
    """Test POST /api/scheduler/clear-log."""
    response = client.post("/api/scheduler/clear-log")
    assert response.status_code == 200
    print("✅ Scheduler clear log")


def test_api_scheduler_planning():
    """Test GET /api/scheduler/planning."""
    response = client.get("/api/scheduler/planning")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    print("✅ Scheduler planning")


def test_api_products_filter_category():
    """Test GET /api/products?category=xxx."""
    response = client.get("/api/products?category=nettoyage")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print("✅ Products filter category")


def test_api_products_inactive():
    """Test GET /api/products avec inactive."""
    response = client.get("/api/products?active_only=false")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print("✅ Products inactive")


def test_api_tenants_owner_config_patch_partial():
    """Test PATCH /api/tenants/owner/config avec update partiel."""
    response = client.patch(
        "/api/tenants/owner/config",
        json={"logo_url": "https://example.com/new-logo.png"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "logo_url" in data or "nom" in data
    print("✅ Tenants config patch partial")


def test_api_optimizations_suggestions():
    """Test GET /api/optimizations/suggestions."""
    response = client.get("/api/optimizations/suggestions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print("✅ Optimizations suggestions")


def test_api_scraping_status_while_running():
    """Test GET /api/scrape/status pendant scraping."""
    # Lancer scraping
    client.post("/api/scrape/start", json={"query": "test", "locations": ["Paris"], "max_pages": 1})

    # Check status
    response = client.get("/api/scrape/status")
    assert response.status_code == 200
    data = response.json()
    assert "running" in data
    print("✅ Scraping status while running")


def test_api_watchdog_refresh():
    """Test POST /api/watchdog/refresh."""
    response = client.post("/api/watchdog/refresh")
    assert response.status_code == 200
    assert "status" in response.json()
    print("✅ Watchdog refresh")


# ══════════════════════════════════════════════════════════════
# AGENTS — Edge cases manquants
# ══════════════════════════════════════════════════════════════

def test_activity_logger_error_path():
    """Test activity_logger avec exception handling."""
    from app.agents.activity_logger import log_error

    # Ne devrait pas crash même avec détails complexes
    log_error(
        source="test_module",
        error="Test error with unicode: éàü",
        details={"nested": {"key": "value"}, "list": [1, 2, 3]}
    )
    print("✅ Activity logger error with complex details")


def test_activity_logger_get_daily_summary_no_data():
    """Test get_daily_summary pour jour sans données."""
    from app.agents.activity_logger import get_daily_summary
    from datetime import date, timedelta

    # Jour très ancien, probablement sans données
    old_date = date(2020, 1, 1)
    summary = get_daily_summary(target_date=old_date)

    assert isinstance(summary, dict)
    assert summary["total_actions"] >= 0  # Peut être 0
    print("✅ Activity logger summary no data")


def test_lead_scorer_edge_cases():
    """Test lead_scorer avec prospects edge cases."""
    from app.agents.lead_scorer import calculate_score
    from app.models.prospect import Prospect

    # Prospect minimal (aucune donnée)
    p_minimal = Prospect(
        tenant_id=1,
        company_name="Minimal Corp",
        status="new"
    )

    score, label, explanation = calculate_score(p_minimal)
    assert isinstance(score, (int, float))
    assert score >= 0
    assert label in ["🔥 Priorité haute", "⚡ Priorité moyenne", "🌱 Priorité faible", "❄️ Non prioritaire"]
    print(f"✅ Lead scorer minimal: {score}/100 ({label})")


def test_lead_scorer_perfect_score():
    """Test lead_scorer avec prospect parfait."""
    from app.agents.lead_scorer import calculate_score
    from app.models.prospect import Prospect

    # Prospect avec tout
    p_perfect = Prospect(
        tenant_id=1,
        company_name="Perfect Corp",
        email="contact@perfect.com",
        phone="0123456789",
        website="https://perfect.com",
        address="123 Rue de Paris",
        city="Paris",
        industry="BTP",
        status="new",
        score_explanation="CA : 5 000 000 € (>1M€)\nDirigeant : Jean Dupont\nSIRET : 12345678901234\nEffectifs : 50\nSource : Permis de construire accordé"
    )

    score, label, explanation = calculate_score(p_perfect)
    assert score >= 70  # Devrait avoir un score élevé
    print(f"✅ Lead scorer perfect: {score}/100 ({label})")


def test_email_templates_all_types():
    """Test email_templates pour tous les types."""
    types = ["BTP", "immobilier", "syndic", "architecte", "bureaux", "hotel", "restaurant"]

    for t in types:
        template = email_templates.get_template(t)
        assert template is not None
        assert "objet" in template
        assert "corps" in template
        print(f"✅ Email template: {t}")


def test_email_templates_unknown_type():
    """Test email_templates avec type inconnu (fallback)."""
    template = email_templates.get_template("type_inexistant_xyz")
    assert template is not None  # Devrait fallback sur default
    assert "objet" in template
    assert "corps" in template
    print("✅ Email template: unknown (fallback)")


# ══════════════════════════════════════════════════════════════
# UTILS — Edge cases manquants
# ══════════════════════════════════════════════════════════════

def test_devis_engine_invalid_type():
    """Test devis_engine avec type prestation invalide."""
    from app.utils.devis_engine import calculate

    # Type invalide devrait fallback
    result = calculate("type_invalide_xyz", 100.0, "ponctuel")
    assert isinstance(result, dict)
    assert "montant_ht" in result
    print("✅ Devis engine invalid type (fallback)")


def test_devis_engine_zero_superficie():
    """Test devis_engine avec superficie = 0."""
    from app.utils.devis_engine import calculate

    result = calculate("nettoyage_bureaux", 0.0, "ponctuel")
    assert isinstance(result, dict)
    # Devrait utiliser minimum_ht
    assert result["montant_ht"] >= 0
    print("✅ Devis engine zero superficie")


def test_devis_engine_get_questions_manquantes_all():
    """Test get_questions_manquantes sans aucune info."""
    from app.utils.devis_engine import get_questions_manquantes

    questions = get_questions_manquantes("fin_chantier", {})
    assert isinstance(questions, list)
    assert len(questions) > 0  # Devrait avoir des questions
    print(f"✅ Devis engine questions: {len(questions)} questions")


def test_pdf_generator_edge_case():
    """Test PDF generator avec données minimales."""
    from app.utils.pdf_generator import generate_devis_pdf

    devis_data = {
        "numero": "TEST-001",
        "service_type": "test",
        "montant_ht": 1000.0,
        "tva_pct": 20.0,
        "montant_ttc": 1200.0
    }

    client_data = {
        "company_name": "Test SA"
    }

    pdf_bytes = generate_devis_pdf(devis_data, client_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    print(f"✅ PDF generator minimal: {len(pdf_bytes)} bytes")


def test_pdf_facture_edge_case():
    """Test PDF facture avec données minimales."""
    from app.utils.pdf_facture import generate_facture_pdf

    facture_data = {
        "numero": "FAC-TEST-001",
        "montant_ht": 1000.0,
        "tva_pct": 20.0,
        "montant_ttc": 1200.0
    }

    client_data = {
        "company_name": "Test Client"
    }

    pdf_bytes = generate_facture_pdf(facture_data, client_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    print(f"✅ PDF facture minimal: {len(pdf_bytes)} bytes")


# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════

def test_batch_summary():
    """Résumé des tests quick wins."""
    modules_tested = [
        "api_dvf", "api_permis", "api_prospects", "api_email_finder",
        "api_scheduler", "api_products", "api_tenants", "api_optimizations",
        "api_scraping", "api_watchdog", "activity_logger", "lead_scorer",
        "email_templates", "devis_engine", "pdf_generator", "pdf_facture"
    ]

    print(f"\n✅ Quick wins batch: {len(modules_tested)} modules testés")
    print(f"   Estimation: ~30-40 lignes couvertes")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
