"""
Tests simples pour petites APIs — Coverage rapide sans mocks complexes
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ── API DVF ──────────────────────────────────────────────────────────────────

def test_scrape_dvf_async():
    """Test POST /api/dvf/scrape."""
    response = client.post("/api/dvf/scrape")
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    print("✅ DVF async")


# ── API PERMIS ───────────────────────────────────────────────────────────────

def test_scrape_permis_async():
    """Test POST /api/permis/scrape."""
    response = client.post("/api/permis/scrape")
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    print("✅ Permis async")


# ── API EMAIL FINDER ─────────────────────────────────────────────────────────

def test_email_finder_batch_async():
    """Test POST /api/email-finder/batch."""
    response = client.post("/api/email-finder/batch?limit=1")
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    print("✅ Email finder batch")


# ── API PAPPERS ──────────────────────────────────────────────────────────────

def test_pappers_enrich_batch_async():
    """Test POST /api/pappers/enrich-batch."""
    response = client.post("/api/pappers/enrich-batch?limit=1")
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    print("✅ Pappers batch")


# Note: Les autres endpoints (devis-rules, outreach, watchdog, scheduler)
# sont testés ailleurs ou n'existent pas dans ces modules


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
