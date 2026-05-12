"""
Tests pour api_clients — API gestion clients
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.models.client import Client
from app.models.chantier import Chantier
from app.models.facture import Facture
from app.models.devis import Devis

client = TestClient(app)


def test_list_clients_empty():
    """Test GET /api/clients sans clients."""
    response = client.get("/api/clients")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    print(f"✅ Liste clients: {len(data)} clients")


def test_create_client():
    """Test POST /api/clients."""
    client_data = {
        "company_name": "Test Client SA",
        "contact_name": "Jean Test",
        "email": "jean@testclient.com",
        "phone": "0123456789",
        "address": "123 Rue Test",
        "city": "75001 Paris",
        "siret": "12345678901234",
        "service_type": "nettoyage_bureaux",
        "status": "actif"
    }

    response = client.post("/api/clients", json=client_data)

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert data["company_name"] == "Test Client SA"
    assert data["email"] == "jean@testclient.com"
    assert data["status"] == "actif"

    print(f"✅ Client créé: ID={data['id']}, {data['company_name']}")


def test_get_client():
    """Test GET /api/clients/{client_id}."""
    # Créer un client d'abord
    client_data = {
        "company_name": "Get Test Client",
        "email": "get@test.com",
        "status": "actif"
    }
    create_response = client.post("/api/clients", json=client_data)
    created_id = create_response.json()["id"]

    # Récupérer le client
    response = client.get(f"/api/clients/{created_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == created_id
    assert data["company_name"] == "Get Test Client"
    assert "nb_chantiers" in data
    assert "nb_devis" in data
    assert "nb_factures" in data

    print(f"✅ Client récupéré: {data['company_name']}")


def test_get_client_not_found():
    """Test GET /api/clients/{client_id} avec ID inexistant."""
    response = client.get("/api/clients/999999")

    assert response.status_code == 404
    assert "introuvable" in response.json()["detail"].lower()

    print("✅ Client non trouvé retourne 404")


def test_update_client():
    """Test PATCH /api/clients/{client_id}."""
    # Créer un client
    client_data = {
        "company_name": "Update Test Client",
        "email": "update@test.com",
        "status": "actif"
    }
    create_response = client.post("/api/clients", json=client_data)
    client_id = create_response.json()["id"]

    # Mettre à jour
    update_data = {
        "company_name": "Updated Client Name",
        "phone": "0987654321",
        "status": "inactif"
    }
    response = client.patch(f"/api/clients/{client_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert data["company_name"] == "Updated Client Name"
    assert data["phone"] == "0987654321"
    assert data["status"] == "inactif"

    print(f"✅ Client mis à jour: {data['company_name']}")


def test_update_client_not_found():
    """Test PATCH /api/clients/{client_id} avec ID inexistant."""
    response = client.patch("/api/clients/999999", json={"company_name": "Test"})

    assert response.status_code == 404

    print("✅ Update client non trouvé retourne 404")


def test_update_client_filters_fields():
    """Test que PATCH ne met à jour que les champs autorisés."""
    # Créer un client
    client_data = {
        "company_name": "Filter Test",
        "email": "filter@test.com"
    }
    create_response = client.post("/api/clients", json=client_data)
    client_id = create_response.json()["id"]

    # Essayer de mettre à jour avec champs autorisés + non autorisés
    update_data = {
        "company_name": "New Name",
        "id": 999999,  # Non autorisé
        "created_at": "2020-01-01"  # Non autorisé
    }
    response = client.patch(f"/api/clients/{client_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()

    # Le nom devrait être mis à jour
    assert data["company_name"] == "New Name"
    # L'ID ne devrait pas changer
    assert data["id"] == client_id

    print("✅ Update filtre les champs non autorisés")


def test_delete_client():
    """Test DELETE /api/clients/{client_id}."""
    # Créer un client
    client_data = {
        "company_name": "Delete Test Client",
        "email": "delete@test.com"
    }
    create_response = client.post("/api/clients", json=client_data)
    client_id = create_response.json()["id"]

    # Supprimer
    response = client.delete(f"/api/clients/{client_id}")

    assert response.status_code == 200
    assert response.json()["deleted"] == True

    # Vérifier que le client n'existe plus
    get_response = client.get(f"/api/clients/{client_id}")
    assert get_response.status_code == 404

    print(f"✅ Client supprimé: ID={client_id}")


def test_delete_client_not_found():
    """Test DELETE /api/clients/{client_id} avec ID inexistant."""
    response = client.delete("/api/clients/999999")

    assert response.status_code == 404

    print("✅ Delete client non trouvé retourne 404")


def test_list_clients_with_filters():
    """Test GET /api/clients avec filtres status et search."""
    # Créer quelques clients
    client.post("/api/clients", json={
        "company_name": "Active Client One",
        "email": "active1@test.com",
        "status": "actif"
    })
    client.post("/api/clients", json={
        "company_name": "Inactive Client Two",
        "email": "inactive@test.com",
        "status": "inactif"
    })

    # Filtrer par status
    response = client.get("/api/clients?status=actif")
    assert response.status_code == 200
    actifs = response.json()

    # Filtrer par recherche
    response = client.get("/api/clients?search=Active")
    assert response.status_code == 200
    searched = response.json()

    # Au moins un résultat dans chaque cas
    assert len(actifs) >= 1
    assert len(searched) >= 1

    print(f"✅ Filtres clients: {len(actifs)} actifs, {len(searched)} trouvés par recherche")


def test_clients_stats():
    """Test GET /api/clients/stats/summary."""
    response = client.get("/api/clients/stats/summary")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "total" in data
    assert "actifs" in data
    assert "ca_total_ht" in data
    assert "devis_en_attente" in data
    assert "chantiers_actifs" in data

    # Vérifier types
    assert isinstance(data["total"], int)
    assert isinstance(data["actifs"], int)
    assert isinstance(data["ca_total_ht"], float)
    assert isinstance(data["devis_en_attente"], int)
    assert isinstance(data["chantiers_actifs"], int)

    print(f"✅ Stats clients: {data['total']} total, {data['actifs']} actifs, {data['ca_total_ht']}€ CA")


def test_client_to_dict_full():
    """Test _client_to_dict avec full=True inclut les relations."""
    # Créer un client
    client_data = {
        "company_name": "Full Dict Test",
        "email": "fulldict@test.com"
    }
    create_response = client.post("/api/clients", json=client_data)
    client_id = create_response.json()["id"]

    # Récupérer avec full=True (endpoint GET /clients/{id})
    response = client.get(f"/api/clients/{client_id}")
    data = response.json()

    # Vérifier que les champs full sont présents
    assert "nb_chantiers" in data
    assert "nb_devis" in data
    assert "nb_factures" in data
    assert "ca_total" in data

    assert isinstance(data["nb_chantiers"], int)
    assert isinstance(data["nb_devis"], int)
    assert isinstance(data["nb_factures"], int)

    print("✅ Client dict full contient les relations")


def test_list_clients_ordered_by_created_at():
    """Test que GET /api/clients retourne les clients triés par date."""
    # Créer plusieurs clients
    for i in range(3):
        client.post("/api/clients", json={
            "company_name": f"Order Test {i}",
            "email": f"order{i}@test.com"
        })

    response = client.get("/api/clients")
    assert response.status_code == 200
    clients = response.json()

    # Devrait avoir au moins 3 clients
    assert len(clients) >= 3

    # Les dates devraient être en ordre décroissant (plus récent d'abord)
    if len(clients) >= 2:
        dates = [c["created_at"] for c in clients if c["created_at"]]
        if len(dates) >= 2:
            assert dates[0] >= dates[-1], "Devrait être trié par date décroissante"

    print(f"✅ Clients triés par date: {len(clients)} clients")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
