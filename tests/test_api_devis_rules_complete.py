"""
Tests pour api_devis_rules — 100% coverage
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_rules():
    """Test GET /api/devis-rules."""
    response = client.get("/api/devis-rules")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)

    print("✅ Get rules OK")


def test_get_tarifs():
    """Test GET /api/devis-rules/tarifs."""
    response = client.get("/api/devis-rules/tarifs")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))

    print("✅ Get tarifs OK")


def test_update_tarif_deprecated():
    """Test PATCH /api/devis-rules/tarifs/{cle} - deprecated."""
    update = {"tarif_m2": 15.0}
    response = client.patch("/api/devis-rules/tarifs/bureaux", json=update)

    assert response.status_code == 410
    assert "déprécié" in response.json()["detail"].lower()

    print("✅ Update tarif deprecated OK (410)")


def test_update_societe_deprecated():
    """Test PATCH /api/devis-rules/societe - deprecated."""
    update = {"nom": "Test"}
    response = client.patch("/api/devis-rules/societe", json=update)

    assert response.status_code == 410
    assert "déprécié" in response.json()["detail"].lower()

    print("✅ Update societe deprecated OK (410)")


def test_simulate_devis():
    """Test POST /api/devis-rules/simulate."""
    response = client.post(
        "/api/devis-rules/simulate",
        params={
            "type_prestation": "nettoyage_bureaux",
            "superficie_m2": 100.0,
            "frequence": "hebdomadaire"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Devrait contenir des infos de calcul
    assert isinstance(data, dict)

    print("✅ Simulate devis OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
