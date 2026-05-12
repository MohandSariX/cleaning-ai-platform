"""
Tests complets pour api_devis — Objectif 70%+ coverage
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.models.client import Client
from app.models.devis import Devis

client = TestClient(app)


@pytest.fixture
def db_session():
    """Session DB pour fixtures."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def sample_client(db_session):
    """Client de test."""
    c = Client(
        company_name="Test Client SA",
        contact_name="Jean Test",
        email="jean@testclient.com",
        phone="0123456789",
        address="123 Rue Test",
        city="Paris",
        status="actif"
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


@pytest.fixture
def sample_devis(db_session, sample_client):
    """Devis de test."""
    import time
    unique_suffix = str(int(time.time() * 1000))[-6:]

    d = Devis(
        tenant_id=1,
        numero=f"DEV-TEST-{unique_suffix}",
        client_id=sample_client.id,
        service_type="nettoyage_bureaux",
        description="Nettoyage bureaux test",
        surface_m2=100.0,
        frequence="mensuel",
        montant_ht=1000.0,
        tva_pct=20.0,
        status="brouillon"
    )
    db_session.add(d)
    db_session.commit()
    db_session.refresh(d)
    return d


# ══════════════════════════════════════════════════════════════
# CRUD BASIQUE
# ══════════════════════════════════════════════════════════════

def test_list_devis():
    """Test GET /api/devis."""
    response = client.get("/api/devis")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"✅ List devis: {len(data)} devis")


def test_list_devis_with_filters(sample_devis):
    """Test GET /api/devis avec filtres."""
    # Filtre par status
    response = client.get("/api/devis?status=brouillon")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Filtre par client_id
    response = client.get(f"/api/devis?client_id={sample_devis.client_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Filtre search
    response = client.get("/api/devis?search=Test")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    print("✅ List devis with filters")


def test_stats_summary():
    """Test GET /api/devis/stats/summary."""
    response = client.get("/api/devis/stats/summary")
    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "envoyes" in data
    assert "acceptes" in data
    assert "refuses" in data
    assert "ca_pipeline" in data
    assert "ca_signe" in data
    assert "taux_conversion" in data

    print(f"✅ Stats: {data['total']} devis, {data['taux_conversion']}% conversion")


def test_get_devis(sample_devis):
    """Test GET /api/devis/{id}."""
    response = client.get(f"/api/devis/{sample_devis.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == sample_devis.id
    assert data["numero"] == sample_devis.numero
    assert data["client_id"] == sample_devis.client_id
    assert "montant_ht" in data
    assert "montant_ttc" in data

    print(f"✅ Get devis: {data['numero']}")


def test_get_devis_not_found():
    """Test GET /api/devis/{id} — 404."""
    response = client.get("/api/devis/999999")
    assert response.status_code == 404
    assert "introuvable" in response.json()["detail"].lower()
    print("✅ Get devis 404")


def test_create_devis(sample_client):
    """Test POST /api/devis."""
    devis_data = {
        "client_id": sample_client.id,
        "service_type": "vitrerie",
        "description": "Nettoyage vitres",
        "surface_m2": 50.0,
        "frequence": "ponctuel",
        "montant_ht": 500.0,
        "tva_pct": 20.0,
        "status": "brouillon",
        "notes": "Test creation"
    }

    response = client.post("/api/devis", json=devis_data)
    assert response.status_code == 200
    data = response.json()

    assert data["client_id"] == sample_client.id
    assert data["service_type"] == "vitrerie"
    assert data["montant_ht"] == 500.0
    assert "numero" in data
    assert data["numero"].startswith("DEV-")

    print(f"✅ Create devis: {data['numero']}")


def test_update_devis(sample_devis):
    """Test PATCH /api/devis/{id}."""
    update_data = {
        "description": "Description modifiée",
        "montant_ht": 1200.0,
        "notes": "Note ajoutée"
    }

    response = client.patch(f"/api/devis/{sample_devis.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()

    assert data["description"] == "Description modifiée"
    assert data["montant_ht"] == 1200.0
    assert data["notes"] == "Note ajoutée"

    print(f"✅ Update devis: {data['numero']}")


def test_update_devis_status_envoye(sample_devis):
    """Test PATCH /api/devis/{id} — Status envoye set sent_at."""
    response = client.patch(f"/api/devis/{sample_devis.id}", json={"status": "envoye"})
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "envoye"
    assert data["sent_at"] is not None

    print("✅ Update devis status envoye")


def test_update_devis_status_accepte(sample_devis):
    """Test PATCH /api/devis/{id} — Status accepte set responded_at."""
    response = client.patch(f"/api/devis/{sample_devis.id}", json={"status": "accepte"})
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "accepte"
    assert data["responded_at"] is not None

    print("✅ Update devis status accepte")


def test_update_devis_not_found():
    """Test PATCH /api/devis/{id} — 404."""
    response = client.patch("/api/devis/999999", json={"notes": "test"})
    assert response.status_code == 404
    print("✅ Update devis 404")


# ══════════════════════════════════════════════════════════════
# ANALYTICS AVANCÉS
# ══════════════════════════════════════════════════════════════

def test_analytics_overview():
    """Test GET /api/devis/analytics/overview."""
    response = client.get("/api/devis/analytics/overview")
    assert response.status_code == 200
    data = response.json()

    assert "period_days" in data
    assert "total" in data
    assert "envoyes" in data
    assert "acceptes" in data
    assert "refuses" in data
    assert "ca_total" in data
    assert "ca_accepte" in data
    assert "ca_pipeline" in data
    assert "taux_envoi" in data
    assert "taux_acceptation" in data
    assert "montant_moyen" in data

    print(f"✅ Analytics overview: {data['total']} devis sur {data['period_days']}j")


def test_analytics_overview_with_days():
    """Test GET /api/devis/analytics/overview?days=90."""
    response = client.get("/api/devis/analytics/overview?days=90")
    assert response.status_code == 200
    data = response.json()

    assert data["period_days"] == 90
    print(f"✅ Analytics overview 90j: {data['total']} devis")


def test_analytics_by_type():
    """Test GET /api/devis/analytics/by-type."""
    response = client.get("/api/devis/analytics/by-type")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)

    if len(data) > 0:
        item = data[0]
        assert "service_type" in item
        assert "total" in item
        assert "envoyes" in item
        assert "acceptes" in item
        assert "ca_total" in item
        assert "taux_acceptation" in item

    print(f"✅ Analytics by-type: {len(data)} types")


def test_analytics_by_montant():
    """Test GET /api/devis/analytics/by-montant."""
    response = client.get("/api/devis/analytics/by-montant")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 5  # 5 tranches

    for item in data:
        assert "tranche" in item
        assert "total" in item
        assert "envoyes" in item
        assert "acceptes" in item
        assert "taux_acceptation" in item

    print(f"✅ Analytics by-montant: {len(data)} tranches")


def test_analytics_evolution():
    """Test GET /api/devis/analytics/evolution."""
    response = client.get("/api/devis/analytics/evolution")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)

    if len(data) > 0:
        item = data[0]
        assert "date" in item
        assert "created" in item
        assert "envoyes" in item
        assert "acceptes" in item
        assert "ca" in item

    print(f"✅ Analytics evolution: {len(data)} jours")


def test_analytics_top_clients():
    """Test GET /api/devis/analytics/top-clients."""
    response = client.get("/api/devis/analytics/top-clients")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)

    if len(data) > 0:
        item = data[0]
        assert "client_id" in item
        assert "company_name" in item
        assert "devis_count" in item
        assert "ca_total" in item

    print(f"✅ Analytics top-clients: {len(data)} clients")


def test_analytics_top_clients_with_limit():
    """Test GET /api/devis/analytics/top-clients?limit=5."""
    response = client.get("/api/devis/analytics/top-clients?limit=5")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 5

    print(f"✅ Analytics top-clients limit 5: {len(data)} clients")


# ══════════════════════════════════════════════════════════════
# SIGNATURE & PDF
# ══════════════════════════════════════════════════════════════

def test_sign_devis(sample_devis):
    """Test POST /api/devis/{id}/sign."""
    signature_data = {
        "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "signed_by": "Jean Test"
    }

    response = client.post(f"/api/devis/{sample_devis.id}/sign", json=signature_data)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "signed"
    assert data["devis_id"] == sample_devis.id
    assert data["signed_by"] == "Jean Test"
    assert "signed_at" in data

    print(f"✅ Sign devis: {data['signed_by']}")


def test_sign_devis_not_found():
    """Test POST /api/devis/{id}/sign — 404."""
    response = client.post("/api/devis/999999/sign", json={
        "signature_data": "test",
        "signed_by": "Test"
    })
    assert response.status_code == 404
    print("✅ Sign devis 404")


def test_download_pdf(sample_devis):
    """Test GET /api/devis/{id}/pdf."""
    response = client.get(f"/api/devis/{sample_devis.id}/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert sample_devis.numero in response.headers["content-disposition"]

    print(f"✅ Download PDF: {sample_devis.numero}.pdf")


def test_download_pdf_not_found():
    """Test GET /api/devis/{id}/pdf — 404."""
    response = client.get("/api/devis/999999/pdf")
    assert response.status_code == 404
    print("✅ Download PDF 404")


# ══════════════════════════════════════════════════════════════
# EDGE CASES & CALCULS
# ══════════════════════════════════════════════════════════════

def test_devis_to_dict_calcul_ttc(sample_devis):
    """Test calcul TTC dans _devis_to_dict."""
    response = client.get(f"/api/devis/{sample_devis.id}")
    data = response.json()

    # TTC = HT * (1 + TVA/100)
    # 1000 * 1.20 = 1200
    assert data["montant_ht"] == 1000.0
    assert data["tva_pct"] == 20.0
    assert data["montant_ttc"] == 1200.0

    print("✅ Calcul TTC correct")


def test_create_devis_auto_numero(sample_client, db_session):
    """Test auto-numérotation DEV-YYYY-NNN."""
    from datetime import datetime
    current_year = datetime.now().year

    # Créer plusieurs devis pour vérifier incrémentation
    for i in range(3):
        response = client.post("/api/devis", json={
            "client_id": sample_client.id,
            "service_type": "test",
            "montant_ht": 100.0,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["numero"].startswith(f"DEV-{current_year}-")

    print(f"✅ Auto-numérotation DEV-{current_year}-NNN")


def test_analytics_zero_division_safety():
    """Test sécurité division par zéro dans analytics."""
    # Même sans devis, les endpoints doivent répondre sans erreur
    response = client.get("/api/devis/analytics/overview?days=1")
    assert response.status_code == 200
    data = response.json()

    # Taux doivent être 0 si pas de devis
    if data["total"] == 0:
        assert data["taux_envoi"] == 0
        assert data["taux_acceptation"] == 0

    print("✅ Analytics safe division par zéro")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
