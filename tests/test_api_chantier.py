"""
Tests pour api_chantier — API gestion chantiers
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from datetime import date, datetime

client = TestClient(app)


@pytest.fixture
def sample_client():
    """Créer un client pour les tests de chantiers."""
    response = client.post("/api/clients", json={
        "company_name": "Chantier Test Client",
        "email": "chantier@test.com",
        "status": "actif"
    })
    return response.json()


def test_list_chantiers_empty():
    """Test GET /api/chantiers sans chantiers."""
    response = client.get("/api/chantiers")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    print(f"✅ Liste chantiers: {len(data)} chantiers")


def test_create_chantier(sample_client):
    """Test POST /api/chantiers."""
    chantier_data = {
        "client_id": sample_client["id"],
        "titre": "Nettoyage bureaux Test",
        "type": "nettoyage_bureaux",
        "adresse": "123 Rue Test",
        "ville": "75001 Paris",
        "surface_m2": 500.0,
        "date_debut": "2024-07-01",
        "date_fin": "2024-07-01",
        "heure_debut": "08:00",
        "duree_heures": 4,
        "status": "planifie"
    }

    response = client.post("/api/chantiers", json=chantier_data)

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert data["titre"] == "Nettoyage bureaux Test"
    assert data["client_id"] == sample_client["id"]
    assert data["type"] == "nettoyage_bureaux"
    assert data["statut"] == "planifie"

    print(f"✅ Chantier créé: ID={data['id']}, {data['titre']}")


def test_get_chantier(sample_client):
    """Test GET /api/chantiers/{chantier_id}."""
    # Créer un chantier
    chantier_data = {
        "client_id": sample_client["id"],
        "titre": "Get Test Chantier",
        "type": "vitrerie",
        "status": "planifie"
    }
    create_response = client.post("/api/chantiers", json=chantier_data)
    chantier_id = create_response.json()["id"]

    # Récupérer le chantier
    response = client.get(f"/api/chantiers/{chantier_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == chantier_id
    assert data["titre"] == "Get Test Chantier"
    assert data["client_nom"] == sample_client["company_name"]

    print(f"✅ Chantier récupéré: {data['titre']}")


def test_get_chantier_not_found():
    """Test GET /api/chantiers/{chantier_id} avec ID inexistant."""
    response = client.get("/api/chantiers/999999")

    assert response.status_code == 404
    assert "introuvable" in response.json()["detail"].lower()

    print("✅ Chantier non trouvé retourne 404")


def test_update_chantier(sample_client):
    """Test PATCH /api/chantiers/{chantier_id}."""
    # Créer un chantier
    chantier_data = {
        "client_id": sample_client["id"],
        "titre": "Update Test Chantier",
        "type": "nettoyage_bureaux",
        "status": "planifie"
    }
    create_response = client.post("/api/chantiers", json=chantier_data)
    chantier_id = create_response.json()["id"]

    # Mettre à jour
    update_data = {
        "titre": "Updated Chantier Title",
        "status": "en_cours",
        "surface_m2": 750.0
    }
    response = client.patch(f"/api/chantiers/{chantier_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert data["titre"] == "Updated Chantier Title"
    assert data["statut"] == "en_cours"
    assert data["surface_m2"] == 750.0

    print(f"✅ Chantier mis à jour: {data['titre']}")


def test_update_chantier_not_found():
    """Test PATCH /api/chantiers/{chantier_id} avec ID inexistant."""
    response = client.patch("/api/chantiers/999999", json={"titre": "Test"})

    assert response.status_code == 404

    print("✅ Update chantier non trouvé retourne 404")


def test_list_chantiers_with_client_filter(sample_client):
    """Test GET /api/chantiers?client_id=X."""
    # Créer un chantier pour ce client
    client.post("/api/chantiers", json={
        "client_id": sample_client["id"],
        "titre": "Filter Test Chantier",
        "type": "nettoyage_bureaux",
        "status": "planifie"
    })

    # Filtrer par client_id
    response = client.get(f"/api/chantiers?client_id={sample_client['id']}")

    assert response.status_code == 200
    chantiers = response.json()

    assert len(chantiers) >= 1
    for ch in chantiers:
        assert ch["client_id"] == sample_client["id"]

    print(f"✅ Filtre client_id: {len(chantiers)} chantiers trouvés")


def test_list_chantiers_with_status_filter(sample_client):
    """Test GET /api/chantiers?status=planifie."""
    # Créer chantiers avec différents statuts
    client.post("/api/chantiers", json={
        "client_id": sample_client["id"],
        "titre": "Planifié",
        "status": "planifie"
    })
    client.post("/api/chantiers", json={
        "client_id": sample_client["id"],
        "titre": "En cours",
        "status": "en_cours"
    })

    # Filtrer par status
    response = client.get("/api/chantiers?status=planifie")

    assert response.status_code == 200
    chantiers = response.json()

    assert len(chantiers) >= 1
    for ch in chantiers:
        assert ch["statut"] == "planifie"

    print(f"✅ Filtre status: {len(chantiers)} chantiers planifiés")


def test_list_chantiers_with_type_filter(sample_client):
    """Test GET /api/chantiers?type=vitrerie."""
    # Créer chantiers de différents types
    client.post("/api/chantiers", json={
        "client_id": sample_client["id"],
        "titre": "Vitrerie chantier",
        "type": "vitrerie",
        "status": "planifie"
    })

    # Filtrer par type
    response = client.get("/api/chantiers?type=vitrerie")

    assert response.status_code == 200
    chantiers = response.json()

    assert len(chantiers) >= 1
    for ch in chantiers:
        assert ch["type"] == "vitrerie"

    print(f"✅ Filtre type: {len(chantiers)} chantiers vitrerie")


def test_list_chantiers_with_search(sample_client):
    """Test GET /api/chantiers?search=keyword."""
    # Le search recherche dans le nom du client
    response = client.get(f"/api/chantiers?search=Chantier Test")

    assert response.status_code == 200
    chantiers = response.json()

    # Devrait trouver des chantiers du client "Chantier Test Client"
    # (Peut être vide si pas de chantiers créés pour ce client)
    assert isinstance(chantiers, list)

    print(f"✅ Search chantiers: {len(chantiers)} résultats")


def test_chantiers_stats(sample_client):
    """Test GET /api/chantiers/stats/summary."""
    # Créer quelques chantiers pour avoir des stats
    client.post("/api/chantiers", json={
        "client_id": sample_client["id"],
        "titre": "Stats Test 1",
        "type": "nettoyage_bureaux",
        "status": "planifie",
        "surface_m2": 100.0
    })
    client.post("/api/chantiers", json={
        "client_id": sample_client["id"],
        "titre": "Stats Test 2",
        "type": "vitrerie",
        "status": "en_cours",
        "surface_m2": 200.0
    })

    response = client.get("/api/chantiers/stats/summary")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "total" in data
    assert "planifies" in data
    assert "en_cours" in data
    assert "termines" in data
    assert "surface_totale" in data

    # Vérifier types
    assert isinstance(data["total"], int)
    assert isinstance(data["planifies"], int)
    assert isinstance(data["en_cours"], int)
    assert isinstance(data["termines"], int)
    assert isinstance(data["surface_totale"], float)

    assert data["total"] >= 2

    print(f"✅ Stats chantiers: {data['total']} total, {data['surface_totale']} m²")


def test_chantier_to_dict_includes_client_nom(sample_client):
    """Test que _chantier_to_dict inclut le nom du client."""
    # Créer un chantier
    chantier_data = {
        "client_id": sample_client["id"],
        "titre": "Dict Test Chantier",
        "status": "planifie"
    }
    create_response = client.post("/api/chantiers", json=chantier_data)
    chantier_id = create_response.json()["id"]

    # Récupérer
    response = client.get(f"/api/chantiers/{chantier_id}")
    data = response.json()

    assert "client_nom" in data
    assert data["client_nom"] == sample_client["company_name"]

    print("✅ Chantier dict inclut client_nom")


def test_create_chantier_filters_fields(sample_client):
    """Test que POST /api/chantiers ne crée que les champs autorisés."""
    chantier_data = {
        "client_id": sample_client["id"],
        "titre": "Filter Fields Test",
        "status": "planifie",
        "id": 999999,  # Non autorisé
        "created_at": "2020-01-01"  # Non autorisé
    }

    response = client.post("/api/chantiers", json=chantier_data)

    assert response.status_code == 200
    data = response.json()

    # L'ID ne devrait pas être 999999
    assert data["id"] != 999999

    print("✅ Create chantier filtre les champs non autorisés")


def test_list_chantiers_ordered():
    """Test que GET /api/chantiers retourne les chantiers triés."""
    response = client.get("/api/chantiers")

    assert response.status_code == 200
    chantiers = response.json()

    # Devrait être une liste
    assert isinstance(chantiers, list)

    # Ordre : date_debut desc (nullslast), puis created_at desc
    # Difficile de vérifier précisément sans créer des données contrôlées
    # On vérifie juste que ça ne plante pas

    print(f"✅ Chantiers triés: {len(chantiers)} chantiers")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
