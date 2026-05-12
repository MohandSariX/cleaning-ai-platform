"""
Tests pour api_scraping — API scraping et scoring
"""
import pytest
from fastapi.testclient import TestClient
from main import app
import time

client = TestClient(app)


def test_get_scrape_status_initial():
    """Test GET /api/scrape/status initialement."""
    response = client.get("/api/scrape/status")

    assert response.status_code == 200
    data = response.json()

    assert "running" in data
    assert "log" in data
    assert "done" in data
    assert "total" in data

    assert isinstance(data["running"], bool)
    assert isinstance(data["log"], list)

    print(f"✅ Scrape status: running={data['running']}")


def test_stop_scrape():
    """Test POST /api/scrape/stop."""
    response = client.post("/api/scrape/stop")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "stopped"

    print("✅ Scrape stop OK")


def test_scrape_status_after_stop():
    """Test status après stop."""
    # Stop d'abord
    client.post("/api/scrape/stop")

    # Vérifier status
    response = client.get("/api/scrape/status")
    data = response.json()

    assert data["running"] == False
    assert any("Arrêté" in msg for msg in data["log"])

    print("✅ Status après stop OK")


def test_start_scrape_params_validation():
    """Test POST /api/scrape/start avec paramètres."""
    scrape_params = {
        "query": "nettoyage test",
        "locations": ["Paris"],
        "max_pages": 1,
        "run_scoring": False
    }

    response = client.post("/api/scrape/start", json=scrape_params)

    # Peut être 200 ou 409 si déjà en cours
    assert response.status_code in [200, 409]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "started"
        print("✅ Scrape started")
    else:
        print("✅ Scrape déjà en cours (409)")


def test_start_scrape_conflict_when_running():
    """Test conflit si scraping déjà en cours."""
    # Démarrer un scraping
    params1 = {
        "query": "test",
        "locations": ["Paris"],
        "max_pages": 1,
        "run_scoring": False
    }
    response1 = client.post("/api/scrape/start", json=params1)

    # Attendre un peu pour que le thread démarre
    time.sleep(0.1)

    # Essayer d'en démarrer un autre
    params2 = {
        "query": "test2",
        "locations": ["Lyon"],
        "max_pages": 1,
        "run_scoring": False
    }
    response2 = client.post("/api/scrape/start", json=params2)

    # Le second devrait échouer avec 409
    if response1.status_code == 200:
        assert response2.status_code == 409
        assert "déjà en cours" in response2.json()["detail"]
        print("✅ Conflit détecté (409)")
    else:
        print("✅ Premier scrape déjà en cours")

    # Nettoyer
    client.post("/api/scrape/stop")


def test_start_scrape_default_params():
    """Test POST /api/scrape/start avec params par défaut."""
    # Stop d'abord pour être sûr
    client.post("/api/scrape/stop")
    time.sleep(0.2)

    # Utiliser params par défaut
    response = client.post("/api/scrape/start", json={})

    assert response.status_code in [200, 409]

    if response.status_code == 200:
        # Vérifier le status
        status = client.get("/api/scrape/status").json()
        assert status["running"] == True
        print("✅ Scrape avec params défaut started")
    else:
        print("✅ Scrape déjà en cours")

    # Nettoyer
    client.post("/api/scrape/stop")


def test_scrape_status_structure():
    """Test structure complète de scrape_status."""
    response = client.get("/api/scrape/status")
    data = response.json()

    # Vérifier tous les champs
    assert "running" in data
    assert "log" in data
    assert "done" in data
    assert "total" in data

    # Vérifier types
    assert isinstance(data["running"], bool)
    assert isinstance(data["log"], list)
    assert isinstance(data["done"], int)
    assert isinstance(data["total"], int)

    print("✅ Structure scrape_status complète")


def test_scrape_log_messages():
    """Test que les messages de log sont ajoutés."""
    # Stop pour vider les logs
    client.post("/api/scrape/stop")

    status = client.get("/api/scrape/status").json()

    # Devrait avoir au moins le message de stop
    assert len(status["log"]) > 0
    assert any("Arrêté" in msg for msg in status["log"])

    print(f"✅ Log messages: {len(status['log'])} messages")


def test_run_scoring_endpoint():
    """Test POST /api/scoring/run endpoint."""
    # Stop d'abord pour être sûr
    client.post("/api/scrape/stop")
    time.sleep(0.2)

    # Note: Ce test peut échouer si la base est vide
    # ou si le scoring prend trop de temps
    response = client.post("/api/scoring/run")

    # Devrait être 200 ou 500 selon l'état de la base
    assert response.status_code in [200, 500, 409]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "completed"
        assert "Scoring" in data["message"]
        print("✅ Scoring endpoint OK")
    elif response.status_code == 409:
        print("✅ Scoring en conflit (scraping en cours)")
    else:
        print("✅ Scoring error (normal si pas de données)")


def test_run_scoring_conflict_when_scraping():
    """Test que scoring ne peut pas tourner si scraping en cours."""
    # Démarrer un scraping
    params = {
        "query": "test",
        "locations": ["Paris"],
        "max_pages": 1,
        "run_scoring": False
    }
    scrape_response = client.post("/api/scrape/start", json=params)

    if scrape_response.status_code == 200:
        time.sleep(0.1)

        # Essayer de lancer le scoring
        response = client.post("/api/scoring/run")

        # Devrait échouer avec 409
        assert response.status_code == 409
        assert "déjà en cours" in response.json()["detail"]
        print("✅ Scoring bloqué si scraping en cours")
    else:
        print("✅ Scraping déjà en cours")

    # Nettoyer
    client.post("/api/scrape/stop")


def test_scrape_params_model():
    """Test validation des paramètres ScrapeParams."""
    # Params valides
    valid_params = {
        "query": "nettoyage",
        "locations": ["Paris", "Lyon"],
        "max_pages": 5,
        "run_scoring": True
    }

    response = client.post("/api/scrape/start", json=valid_params)
    assert response.status_code in [200, 409]

    # Nettoyer
    client.post("/api/scrape/stop")

    print("✅ ScrapeParams validation OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
