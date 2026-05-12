"""
Tests pour api_factures — API gestion factures
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from datetime import date

client = TestClient(app)


@pytest.fixture
def sample_client():
    """Créer un client pour les tests de factures."""
    response = client.post("/api/clients", json={
        "company_name": "Facture Test Client",
        "email": "facture@test.com",
        "status": "actif"
    })
    return response.json()


def test_list_factures():
    """Test GET /api/factures."""
    response = client.get("/api/factures")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    print(f"✅ Liste factures: {len(data)} factures")


def test_create_facture(sample_client):
    """Test POST /api/factures."""
    facture_data = {
        "client_id": sample_client["id"],
        "montant_ht": 1000.0,
        "tva_pct": 20.0,
        "description": "Prestation nettoyage",
        "date_emission": "2024-06-01",
        "date_echeance": "2024-07-01",
        "status": "envoyee"
    }

    response = client.post("/api/factures", json=facture_data)

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert "numero" in data
    assert data["numero"].startswith("FAC-")
    assert data["montant_ht"] == 1000.0
    assert data["client_id"] == sample_client["id"]
    assert data["status"] == "envoyee"

    print(f"✅ Facture créée: {data['numero']}, {data['montant_ht']}€ HT")


def test_create_facture_generates_numero(sample_client):
    """Test que POST /api/factures génère un numéro automatique."""
    facture_data = {
        "client_id": sample_client["id"],
        "montant_ht": 500.0,
        "status": "envoyee"
    }

    response = client.post("/api/factures", json=facture_data)

    assert response.status_code == 200
    data = response.json()

    # Le numéro devrait être au format FAC-YYYY-NNN
    assert data["numero"].startswith("FAC-2")
    parts = data["numero"].split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 4  # Année
    assert len(parts[2]) == 3  # Numéro

    print(f"✅ Numéro généré: {data['numero']}")


def test_get_facture(sample_client):
    """Test GET /api/factures/{facture_id}."""
    # Créer une facture
    facture_data = {
        "client_id": sample_client["id"],
        "montant_ht": 800.0,
        "status": "envoyee"
    }
    create_response = client.post("/api/factures", json=facture_data)
    facture_id = create_response.json()["id"]

    # Récupérer la facture
    response = client.get(f"/api/factures/{facture_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == facture_id
    assert data["montant_ht"] == 800.0
    assert data["client_name"] == sample_client["company_name"]

    print(f"✅ Facture récupérée: {data['numero']}")


def test_get_facture_not_found():
    """Test GET /api/factures/{facture_id} avec ID inexistant."""
    response = client.get("/api/factures/999999")

    assert response.status_code == 404
    assert "introuvable" in response.json()["detail"].lower()

    print("✅ Facture non trouvée retourne 404")


def test_update_facture(sample_client):
    """Test PATCH /api/factures/{facture_id}."""
    # Créer une facture
    facture_data = {
        "client_id": sample_client["id"],
        "montant_ht": 1200.0,
        "status": "envoyee"
    }
    create_response = client.post("/api/factures", json=facture_data)
    facture_id = create_response.json()["id"]

    # Mettre à jour
    update_data = {
        "montant_ht": 1500.0,
        "description": "Prestation mise à jour",
        "status": "envoyee"
    }
    response = client.patch(f"/api/factures/{facture_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert data["montant_ht"] == 1500.0
    assert data["description"] == "Prestation mise à jour"

    print(f"✅ Facture mise à jour: {data['montant_ht']}€ HT")


def test_update_facture_status_payee_sets_date(sample_client):
    """Test que PATCH status=payee définit automatiquement date_paiement."""
    # Créer une facture
    facture_data = {
        "client_id": sample_client["id"],
        "montant_ht": 1000.0,
        "status": "envoyee"
    }
    create_response = client.post("/api/factures", json=facture_data)
    facture_id = create_response.json()["id"]

    # Marquer comme payée
    response = client.patch(f"/api/factures/{facture_id}", json={"status": "payee"})

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "payee"
    assert data["date_paiement"] is not None

    print(f"✅ Facture payée: date_paiement={data['date_paiement']}")


def test_update_facture_not_found():
    """Test PATCH /api/factures/{facture_id} avec ID inexistant."""
    response = client.patch("/api/factures/999999", json={"montant_ht": 1000.0})

    assert response.status_code == 404

    print("✅ Update facture non trouvée retourne 404")


def test_list_factures_with_client_filter(sample_client):
    """Test GET /api/factures?client_id=X."""
    # Créer une facture pour ce client
    client.post("/api/factures", json={
        "client_id": sample_client["id"],
        "montant_ht": 500.0,
        "status": "envoyee"
    })

    # Filtrer par client_id
    response = client.get(f"/api/factures?client_id={sample_client['id']}")

    assert response.status_code == 200
    factures = response.json()

    assert len(factures) >= 1
    for f in factures:
        assert f["client_id"] == sample_client["id"]

    print(f"✅ Filtre client_id: {len(factures)} factures")


def test_list_factures_with_status_filter(sample_client):
    """Test GET /api/factures?status=payee."""
    # Créer factures avec différents statuts
    client.post("/api/factures", json={
        "client_id": sample_client["id"],
        "montant_ht": 100.0,
        "status": "envoyee"
    })
    facture_payee = client.post("/api/factures", json={
        "client_id": sample_client["id"],
        "montant_ht": 200.0,
        "status": "payee"
    }).json()

    # Filtrer par status
    response = client.get("/api/factures?status=payee")

    assert response.status_code == 200
    factures = response.json()

    assert len(factures) >= 1
    for f in factures:
        assert f["status"] == "payee"

    print(f"✅ Filtre status: {len(factures)} factures payées")


def test_list_factures_with_search(sample_client):
    """Test GET /api/factures?search=keyword."""
    # Le search recherche dans le nom du client
    response = client.get(f"/api/factures?search=Facture Test")

    assert response.status_code == 200
    factures = response.json()

    # Devrait trouver les factures du client "Facture Test Client"
    assert isinstance(factures, list)

    print(f"✅ Search factures: {len(factures)} résultats")


def test_factures_stats(sample_client):
    """Test GET /api/factures/stats/summary."""
    # Créer quelques factures pour avoir des stats
    client.post("/api/factures", json={
        "client_id": sample_client["id"],
        "montant_ht": 1000.0,
        "status": "payee"
    })
    client.post("/api/factures", json={
        "client_id": sample_client["id"],
        "montant_ht": 500.0,
        "status": "envoyee"
    })

    response = client.get("/api/factures/stats/summary")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "total" in data
    assert "payees" in data
    assert "en_attente" in data
    assert "en_retard" in data
    assert "ca_encaisse" in data
    assert "ca_en_attente" in data

    # Vérifier types
    assert isinstance(data["total"], int)
    assert isinstance(data["payees"], int)
    assert isinstance(data["ca_encaisse"], float)
    assert isinstance(data["ca_en_attente"], float)

    assert data["total"] >= 2

    print(f"✅ Stats factures: {data['total']} total, {data['ca_encaisse']}€ encaissé")


def test_facture_to_dict_calculates_ttc(sample_client):
    """Test que _facture_to_dict calcule montant_ttc correctement."""
    # Créer une facture avec TVA
    facture_data = {
        "client_id": sample_client["id"],
        "montant_ht": 1000.0,
        "tva_pct": 20.0,
        "status": "envoyee"
    }
    response = client.post("/api/factures", json=facture_data)

    assert response.status_code == 200
    data = response.json()

    assert data["montant_ht"] == 1000.0
    assert data["tva_pct"] == 20.0
    assert data["montant_ttc"] == 1200.0

    print(f"✅ Calcul TTC: {data['montant_ht']}€ HT → {data['montant_ttc']}€ TTC")


def test_facture_to_dict_default_tva(sample_client):
    """Test que _facture_to_dict utilise 20% par défaut si tva_pct absent."""
    # Créer une facture sans TVA spécifiée
    facture_data = {
        "client_id": sample_client["id"],
        "montant_ht": 1000.0,
        "status": "envoyee"
    }
    response = client.post("/api/factures", json=facture_data)

    assert response.status_code == 200
    data = response.json()

    # TVA par défaut devrait être 20%
    assert data["tva_pct"] == 20.0
    assert data["montant_ttc"] == 1200.0

    print("✅ TVA par défaut: 20%")


def test_download_facture_pdf(sample_client):
    """Test GET /api/factures/{facture_id}/pdf."""
    # Créer une facture
    facture_data = {
        "client_id": sample_client["id"],
        "montant_ht": 1000.0,
        "status": "envoyee"
    }
    create_response = client.post("/api/factures", json=facture_data)
    facture_id = create_response.json()["id"]

    # Télécharger le PDF
    response = client.get(f"/api/factures/{facture_id}/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "Content-Disposition" in response.headers
    assert "attachment" in response.headers["Content-Disposition"]

    # Vérifier que c'est bien un PDF
    pdf_content = response.content
    assert pdf_content.startswith(b'%PDF')

    print(f"✅ PDF facture téléchargé: {len(pdf_content)} bytes")


def test_download_facture_pdf_not_found():
    """Test GET /api/factures/{facture_id}/pdf avec ID inexistant."""
    response = client.get("/api/factures/999999/pdf")

    assert response.status_code == 404

    print("✅ PDF facture non trouvée retourne 404")


def test_list_factures_ordered_by_created_at():
    """Test que GET /api/factures retourne les factures triées par date."""
    response = client.get("/api/factures")

    assert response.status_code == 200
    factures = response.json()

    # Devrait être une liste
    assert isinstance(factures, list)

    # Ordre : created_at desc (plus récent d'abord)
    if len(factures) >= 2:
        dates = [f["created_at"] for f in factures if f["created_at"]]
        if len(dates) >= 2:
            assert dates[0] >= dates[-1], "Devrait être trié par created_at décroissant"

    print(f"✅ Factures triées: {len(factures)} factures")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
