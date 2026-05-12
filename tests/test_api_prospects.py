"""
Tests pour api_prospects — API gestion prospects
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.models.prospect import Prospect

client = TestClient(app)


def test_list_prospects():
    """Test GET /api/prospects."""
    response = client.get("/api/prospects")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    print(f"✅ Liste prospects: {len(data)} prospects")


def test_list_prospects_with_city_filter():
    """Test GET /api/prospects?city=Paris."""
    response = client.get("/api/prospects?city=Paris")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Tous les résultats devraient être de Paris
    for p in data:
        assert p["city"] == "Paris"

    print(f"✅ Filtre city: {len(data)} prospects à Paris")


def test_list_prospects_with_status_filter():
    """Test GET /api/prospects?status=new."""
    response = client.get("/api/prospects?status=new")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Tous les résultats devraient avoir status=new
    for p in data:
        assert p["status"] == "new"

    print(f"✅ Filtre status: {len(data)} prospects new")


def test_list_prospects_with_min_score_filter():
    """Test GET /api/prospects?min_score=80."""
    response = client.get("/api/prospects?min_score=80")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Tous les résultats devraient avoir score >= 80
    for p in data:
        if p["lead_score"] is not None:
            assert p["lead_score"] >= 80

    print(f"✅ Filtre min_score: {len(data)} prospects score >= 80")


def test_list_prospects_with_has_email_true():
    """Test GET /api/prospects?has_email=true."""
    response = client.get("/api/prospects?has_email=true")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Tous les résultats devraient avoir un email
    for p in data:
        assert p["email"] is not None

    print(f"✅ Filtre has_email=true: {len(data)} prospects avec email")


def test_list_prospects_with_has_email_false():
    """Test GET /api/prospects?has_email=false."""
    response = client.get("/api/prospects?has_email=false")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Tous les résultats devraient ne pas avoir d'email
    for p in data:
        assert p["email"] is None

    print(f"✅ Filtre has_email=false: {len(data)} prospects sans email")


def test_list_prospects_with_search():
    """Test GET /api/prospects?search=keyword."""
    response = client.get("/api/prospects?search=nettoyage")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Les résultats devraient contenir le mot "nettoyage" dans company_name
    for p in data:
        assert "nettoyage" in p["company_name"].lower()

    print(f"✅ Search: {len(data)} prospects trouvés")


def test_list_prospects_with_limit():
    """Test GET /api/prospects?limit=10."""
    response = client.get("/api/prospects?limit=10")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10

    print(f"✅ Limit: {len(data)} prospects (max 10)")


def test_list_prospects_ordered_by_score():
    """Test que les prospects sont triés par score décroissant."""
    response = client.get("/api/prospects?limit=50")

    assert response.status_code == 200
    data = response.json()

    # Vérifier que les scores sont en ordre décroissant
    if len(data) >= 2:
        scores = [p["lead_score"] for p in data if p["lead_score"] is not None]
        if len(scores) >= 2:
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i+1], "Devrait être trié par score décroissant"

    print("✅ Prospects triés par score décroissant")


def test_get_prospect():
    """Test GET /api/prospects/{prospect_id}."""
    # Récupérer un prospect existant
    list_response = client.get("/api/prospects?limit=1")
    prospects = list_response.json()

    if len(prospects) > 0:
        prospect_id = prospects[0]["id"]

        response = client.get(f"/api/prospects/{prospect_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == prospect_id
        assert "company_name" in data
        assert "lead_score" in data

        print(f"✅ Prospect récupéré: {data['company_name']}")
    else:
        print("⚠️ Aucun prospect en base pour tester")


def test_get_prospect_not_found():
    """Test GET /api/prospects/{prospect_id} avec ID inexistant."""
    response = client.get("/api/prospects/999999999")

    assert response.status_code == 200
    data = response.json()
    assert "error" in data

    print("✅ Prospect non trouvé retourne erreur")


def test_update_prospect():
    """Test PATCH /api/prospects/{prospect_id}."""
    # Récupérer un prospect existant
    list_response = client.get("/api/prospects?limit=1")
    prospects = list_response.json()

    if len(prospects) > 0:
        prospect_id = prospects[0]["id"]
        original_status = prospects[0]["status"]

        # Mettre à jour
        new_status = "contacted" if original_status != "contacted" else "replied"
        response = client.patch(f"/api/prospects/{prospect_id}", json={
            "status": new_status,
            "email": "updated@test.com"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == new_status
        assert data["email"] == "updated@test.com"

        print(f"✅ Prospect mis à jour: status={new_status}")
    else:
        print("⚠️ Aucun prospect en base pour tester")


def test_update_prospect_filters_fields():
    """Test que PATCH ne met à jour que status, email, phone."""
    # Récupérer un prospect existant
    list_response = client.get("/api/prospects?limit=1")
    prospects = list_response.json()

    if len(prospects) > 0:
        prospect_id = prospects[0]["id"]
        original_company = prospects[0]["company_name"]

        # Essayer de mettre à jour avec des champs non autorisés
        response = client.patch(f"/api/prospects/{prospect_id}", json={
            "status": "contacted",
            "company_name": "New Company Name",  # Non autorisé
            "lead_score": 999  # Non autorisé
        })

        assert response.status_code == 200
        data = response.json()

        # Le status devrait être mis à jour
        assert data["status"] == "contacted"
        # Mais pas le company_name ni le lead_score
        assert data["company_name"] == original_company
        assert data["lead_score"] != 999

        print("✅ Update filtre les champs non autorisés")
    else:
        print("⚠️ Aucun prospect en base pour tester")


def test_update_prospect_not_found():
    """Test PATCH /api/prospects/{prospect_id} avec ID inexistant."""
    response = client.patch("/api/prospects/999999999", json={"status": "contacted"})

    assert response.status_code == 200
    data = response.json()
    assert "error" in data

    print("✅ Update prospect non trouvé retourne erreur")


def test_get_stats():
    """Test GET /api/stats."""
    response = client.get("/api/stats")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "total" in data
    assert "with_email" in data
    assert "with_phone" in data
    assert "with_web" in data
    assert "email_rate" in data
    assert "avg_score" in data
    assert "score_distribution" in data
    assert "by_city" in data

    # Vérifier types
    assert isinstance(data["total"], int)
    assert isinstance(data["with_email"], int)
    assert isinstance(data["email_rate"], int)
    assert isinstance(data["avg_score"], float)

    # Vérifier score_distribution
    dist = data["score_distribution"]
    assert "haute" in dist
    assert "moyenne" in dist
    assert "faible" in dist
    assert "nulle" in dist

    # Vérifier by_city
    assert isinstance(data["by_city"], list)

    print(f"✅ Stats: {data['total']} prospects, {data['email_rate']}% avec email")


def test_get_cities():
    """Test GET /api/cities."""
    response = client.get("/api/cities")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)

    # Les villes devraient être triées
    if len(data) >= 2:
        assert data == sorted(data), "Les villes devraient être triées"

    print(f"✅ Villes: {len(data)} villes distinctes")


def test_get_prospect_emails():
    """Test GET /api/prospects/{prospect_id}/emails."""
    # Récupérer un prospect existant
    list_response = client.get("/api/prospects?limit=1")
    prospects = list_response.json()

    if len(prospects) > 0:
        prospect_id = prospects[0]["id"]

        response = client.get(f"/api/prospects/{prospect_id}/emails")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # Si des emails existent
        if len(data) > 0:
            email = data[0]
            assert "id" in email
            assert "email_type" in email
            assert "recipient" in email
            assert "status" in email
            assert "sent_at" in email

        print(f"✅ Emails prospect: {len(data)} emails")
    else:
        print("⚠️ Aucun prospect en base pour tester")


def test_get_prospect_conversation():
    """Test GET /api/prospects/{prospect_id}/conversation."""
    # Récupérer un prospect existant
    list_response = client.get("/api/prospects?limit=1")
    prospects = list_response.json()

    if len(prospects) > 0:
        prospect_id = prospects[0]["id"]

        response = client.get(f"/api/prospects/{prospect_id}/conversation")

        assert response.status_code == 200
        data = response.json()

        # Peut être None si pas de conversation
        if data is not None:
            assert "status" in data
            assert "infos" in data
            assert "historique" in data
            assert "nb_echanges" in data

            print(f"✅ Conversation: {data['nb_echanges']} échanges")
        else:
            print("✅ Conversation: Aucune conversation (normal)")
    else:
        print("⚠️ Aucun prospect en base pour tester")


def test_prospect_to_dict_structure():
    """Test structure de _prospect_to_dict."""
    response = client.get("/api/prospects?limit=1")

    assert response.status_code == 200
    prospects = response.json()

    if len(prospects) > 0:
        p = prospects[0]

        # Vérifier tous les champs attendus
        expected_fields = [
            "id", "company_name", "industry", "city", "address",
            "website", "email", "phone", "lead_score", "score_label",
            "score_explanation", "status", "created_at"
        ]

        for field in expected_fields:
            assert field in p, f"Champ {field} manquant"

        print("✅ Structure prospect dict complète")
    else:
        print("⚠️ Aucun prospect en base pour tester")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
