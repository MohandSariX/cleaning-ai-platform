"""
Tests pour api_escalations — API gestion escalations (version simplifiée)
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_escalation_stats():
    """Test GET /api/escalations/stats."""
    response = client.get("/api/escalations/stats")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "total" in data
    assert "pending" in data
    assert "approved" in data
    assert "rejected" in data
    assert "auto_resolved" in data
    assert "by_type" in data
    assert "by_priority" in data

    # Vérifier types
    assert isinstance(data["total"], int)
    assert isinstance(data["pending"], int)
    assert isinstance(data["by_type"], dict)
    assert isinstance(data["by_priority"], dict)

    print(f"✅ Stats: {data['total']} total, {data['pending']} pending")


def test_get_escalation_not_found():
    """Test GET /api/escalations/{id} avec ID inexistant."""
    response = client.get("/api/escalations/999999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

    print("✅ Escalation non trouvée retourne 404")


def test_decide_escalation_not_found():
    """Test POST /api/escalations/{id}/decide avec ID inexistant."""
    decision_data = {
        "decision": "approve",
        "approved_by": "Mohand"
    }

    response = client.post(
        "/api/escalations/999999/decide",
        json=decision_data
    )

    assert response.status_code == 404

    print("✅ Decide escalation non trouvée retourne 404")


def test_get_autonomy_config():
    """Test GET /api/escalations/config/autonomy."""
    response = client.get("/api/escalations/config/autonomy")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "devis_auto_threshold_ht" in data
    assert "discount_auto_max_pct" in data
    assert "chantier_auto_planning" in data
    assert "chantier_notification_client" in data
    assert "planning_conflict_escalate" in data

    # Vérifier types
    assert isinstance(data["devis_auto_threshold_ht"], (int, float))
    assert isinstance(data["discount_auto_max_pct"], (int, float))
    assert isinstance(data["chantier_auto_planning"], bool)

    print(f"✅ Config autonomie: seuil {data['devis_auto_threshold_ht']}€, remise max {data['discount_auto_max_pct']}%")


def test_update_autonomy_config():
    """Test PATCH /api/escalations/config/autonomy."""
    update_data = {
        "devis_auto_threshold_ht": 12000.0,
        "discount_auto_max_pct": 18.0
    }

    response = client.patch(
        "/api/escalations/config/autonomy",
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "config" in data
    assert data["config"]["devis_auto_threshold_ht"] == 12000.0
    assert data["config"]["discount_auto_max_pct"] == 18.0

    print(f"✅ Config mise à jour: {data['config']['devis_auto_threshold_ht']}€")


def test_update_autonomy_config_partial():
    """Test PATCH /api/escalations/config/autonomy avec update partiel."""
    update_data = {
        "chantier_auto_planning": False
    }

    response = client.patch(
        "/api/escalations/config/autonomy",
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["config"]["chantier_auto_planning"] == False

    print("✅ Config partielle mise à jour")


def test_update_autonomy_config_all_fields():
    """Test PATCH /api/escalations/config/autonomy avec tous les champs."""
    update_data = {
        "devis_auto_threshold_ht": 15000.0,
        "discount_auto_max_pct": 20.0,
        "chantier_auto_planning": True,
        "chantier_notification_client": True,
        "planning_conflict_escalate": True
    }

    response = client.patch(
        "/api/escalations/config/autonomy",
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()

    config = data["config"]
    assert config["devis_auto_threshold_ht"] == 15000.0
    assert config["discount_auto_max_pct"] == 20.0
    assert config["chantier_auto_planning"] == True
    assert config["chantier_notification_client"] == True
    assert config["planning_conflict_escalate"] == True

    print("✅ Config complète mise à jour")


def test_escalation_stats_by_type():
    """Test que stats inclut groupement by_type."""
    response = client.get("/api/escalations/stats")

    assert response.status_code == 200
    data = response.json()

    by_type = data["by_type"]
    assert isinstance(by_type, dict)

    print(f"✅ Stats by_type: {by_type}")


def test_escalation_stats_by_priority():
    """Test que stats inclut groupement by_priority."""
    response = client.get("/api/escalations/stats")

    assert response.status_code == 200
    data = response.json()

    by_priority = data["by_priority"]
    assert isinstance(by_priority, dict)

    print(f"✅ Stats by_priority: {by_priority}")


def test_escalation_stats_totals():
    """Test cohérence totaux stats."""
    response = client.get("/api/escalations/stats")

    assert response.status_code == 200
    data = response.json()

    # La somme des statuts devrait égaler le total
    sum_status = (
        data["pending"] +
        data["approved"] +
        data["rejected"] +
        data["auto_resolved"]
    )

    assert sum_status == data["total"], f"Somme statuts ({sum_status}) != total ({data['total']})"

    print(f"✅ Totaux cohérents: {data['total']} total = {sum_status} somme statuts")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
