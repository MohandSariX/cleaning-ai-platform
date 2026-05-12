"""
Tests pour api_optimizations — API optimisations Claude
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_suggestions():
    """Test GET /api/optimizations/suggestions."""
    response = client.get("/api/optimizations/suggestions")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Chaque suggestion devrait avoir la structure attendue
    if len(data) > 0:
        suggestion = data[0]
        assert "type" in suggestion
        assert "priority" in suggestion
        assert "message" in suggestion
        assert "action" in suggestion

    print(f"✅ Suggestions: {len(data)} suggestions")


def test_get_email_performance():
    """Test GET /api/optimizations/email-performance."""
    response = client.get("/api/optimizations/email-performance")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "total_sent" in data
    assert "replied" in data
    assert "reply_rate" in data
    assert "best_day" in data
    assert "best_day_count" in data
    assert "recommendations" in data

    # Vérifier types
    assert isinstance(data["total_sent"], int)
    assert isinstance(data["replied"], int)
    assert isinstance(data["reply_rate"], (int, float))
    assert isinstance(data["recommendations"], list)

    print(f"✅ Email performance: {data['total_sent']} envoyés, {data['reply_rate']}% réponse")


def test_get_lost_prospects():
    """Test GET /api/optimizations/lost-prospects."""
    response = client.get("/api/optimizations/lost-prospects")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "total" in data
    assert "avg_score" in data

    # Vérifier types
    assert isinstance(data["total"], int)
    assert isinstance(data["avg_score"], (int, float))

    print(f"✅ Lost prospects: {data['total']} perdus, score moyen {data['avg_score']}")


def test_get_scoring_adjustments():
    """Test GET /api/optimizations/scoring-adjustments."""
    response = client.get("/api/optimizations/scoring-adjustments")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "adjustments" in data or "status" in data

    print("✅ Scoring adjustments OK")


def test_get_ab_test():
    """Test GET /api/optimizations/ab-test."""
    response = client.get("/api/optimizations/ab-test")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "results" in data or "status" in data

    print(f"✅ A/B test: status={data.get('status', 'ok')}")


def test_post_run_cycle():
    """Test POST /api/optimizations/run-cycle."""
    response = client.post("/api/optimizations/run-cycle")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "completed"

    print("✅ Run cycle OK")


def test_get_learnings():
    """Test GET /api/optimizations/learnings."""
    response = client.get("/api/optimizations/learnings")

    assert response.status_code == 200
    data = response.json()

    # Peut être une liste ou un dict avec learnings
    if isinstance(data, list):
        count = len(data)
    else:
        assert "learnings" in data
        count = data.get("count", len(data["learnings"]))

    print(f"✅ Learnings: {count} learnings")


def test_get_strategy():
    """Test GET /api/optimizations/strategy."""
    response = client.get("/api/optimizations/strategy")

    assert response.status_code == 200
    data = response.json()

    # Devrait contenir des infos stratégiques
    assert isinstance(data, dict)

    print("✅ Strategy OK")


def test_email_performance_with_params():
    """Test email performance avec paramètre days."""
    response = client.get("/api/optimizations/email-performance?days=30")

    assert response.status_code == 200
    data = response.json()

    assert "total_sent" in data

    print(f"✅ Email performance 30j: {data['total_sent']} emails")


def test_lost_prospects_with_params():
    """Test lost prospects avec paramètre days."""
    response = client.get("/api/optimizations/lost-prospects?days=60")

    assert response.status_code == 200
    data = response.json()

    assert "total" in data

    print(f"✅ Lost prospects 60j: {data['total']} perdus")


def test_suggestions_structure():
    """Test structure détaillée des suggestions."""
    response = client.get("/api/optimizations/suggestions")
    data = response.json()

    for suggestion in data:
        assert suggestion["type"] in ["email", "scoring", "targeting", "strategy", "communication"]
        assert suggestion["priority"] in ["high", "medium", "low"]
        assert len(suggestion["message"]) > 0
        assert len(suggestion["action"]) > 0

    print(f"✅ {len(data)} suggestions validées")


def test_email_performance_calculations():
    """Test calculs email performance."""
    response = client.get("/api/optimizations/email-performance")
    data = response.json()

    # Si des emails ont été envoyés
    if data["total_sent"] > 0:
        # Le taux devrait être cohérent
        expected_rate = (data["replied"] / data["total_sent"]) * 100
        assert abs(data["reply_rate"] - expected_rate) < 1  # Tolérance arrondi

    print("✅ Calculs email performance cohérents")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
