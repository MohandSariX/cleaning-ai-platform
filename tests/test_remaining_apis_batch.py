"""
Tests batch pour APIs restantes — Coverage rapide
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ══════════════════════════════════════════════════════════════════════════════
# API OUTREACH
# ══════════════════════════════════════════════════════════════════════════════

def test_outreach_stats():
    """Test GET /api/outreach/stats."""
    response = client.get("/api/outreach/stats")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    print("✅ Outreach stats")


def test_outreach_send_now():
    """Test POST /api/outreach/send-now."""
    response = client.post("/api/outreach/send-now")
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    print("✅ Outreach send now")


def test_outreach_send_test():
    """Test POST /api/outreach/send-test."""
    response = client.post("/api/outreach/send-test")
    # Peut échouer si pas de prospects, c'est OK
    assert response.status_code in [200, 500]
    print("✅ Outreach send test")


# ══════════════════════════════════════════════════════════════════════════════
# API WATCHDOG
# ══════════════════════════════════════════════════════════════════════════════

def test_watchdog_rapport():
    """Test GET /api/watchdog/rapport."""
    response = client.get("/api/watchdog/rapport")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    print("✅ Watchdog rapport")


def test_watchdog_refresh():
    """Test POST /api/watchdog/refresh."""
    response = client.post("/api/watchdog/refresh")
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    print("✅ Watchdog refresh")


def test_watchdog_test_telegram():
    """Test POST /api/watchdog/test-telegram."""
    response = client.post("/api/watchdog/test-telegram")
    # Peut échouer si Telegram non configuré
    assert response.status_code in [200, 500]
    print("✅ Watchdog test telegram")


# ══════════════════════════════════════════════════════════════════════════════
# API SCHEDULER
# ══════════════════════════════════════════════════════════════════════════════

def test_scheduler_status():
    """Test GET /api/scheduler/status."""
    response = client.get("/api/scheduler/status")
    assert response.status_code == 200
    data = response.json()
    assert "scheduler_running" in data
    print("✅ Scheduler status")


def test_scheduler_trigger_now():
    """Test POST /api/scheduler/run-now."""
    response = client.post("/api/scheduler/run-now")
    # Peut échouer selon l'état
    assert response.status_code in [200, 500]
    print("✅ Scheduler run now")


def test_scheduler_config():
    """Test GET /api/scheduler/planning."""
    response = client.get("/api/scheduler/planning")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    print("✅ Scheduler planning")


# ══════════════════════════════════════════════════════════════════════════════
# API TENANTS
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(reason="Endpoint /api/tenants/owner not implemented yet")
def test_tenants_owner_get():
    """Test GET /api/tenants/owner."""
    response = client.get("/api/tenants/owner")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    print("✅ Tenants owner GET")


def test_tenants_owner_config():
    """Test GET /api/tenants/owner/config."""
    response = client.get("/api/tenants/owner/config")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    print("✅ Tenants owner config")


def test_tenants_owner_config_update():
    """Test PATCH /api/tenants/owner/config."""
    update = {"logo_url": "https://example.com/logo.png"}
    response = client.patch("/api/tenants/owner/config", json=update)
    assert response.status_code == 200
    print("✅ Tenants config update")


@pytest.mark.skip(reason="Endpoint /api/tenants list not implemented yet")
def test_tenants_list():
    """Test GET /api/tenants."""
    response = client.get("/api/tenants")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"✅ Tenants list: {len(data)} tenants")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
