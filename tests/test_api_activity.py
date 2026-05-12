"""
Tests pour api_activity — API journal d'activité
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_logs():
    """Test GET /api/activity/logs."""
    response = client.get("/api/activity/logs")

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "logs" in data
    assert isinstance(data["logs"], list)

    print(f"✅ Activity logs: {data['total']} total, {len(data['logs'])} retournés")


def test_get_logs_with_limit():
    """Test GET /api/activity/logs?limit=10."""
    response = client.get("/api/activity/logs?limit=10")

    assert response.status_code == 200
    data = response.json()

    assert len(data["logs"]) <= 10

    print(f"✅ Activity logs limit: {len(data['logs'])} logs (max 10)")


def test_get_logs_with_offset():
    """Test GET /api/activity/logs?offset=5."""
    response = client.get("/api/activity/logs?offset=5&limit=10")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["logs"], list)

    print(f"✅ Activity logs offset: {len(data['logs'])} logs avec offset=5")


def test_get_logs_with_event_type_filter():
    """Test GET /api/activity/logs?event_type=email_sent."""
    response = client.get("/api/activity/logs?event_type=email_sent")

    assert response.status_code == 200
    data = response.json()

    # Tous les logs devraient avoir event_type=email_sent
    for log in data["logs"]:
        assert log["event_type"] == "email_sent"

    print(f"✅ Filter event_type: {len(data['logs'])} logs email_sent")


def test_get_logs_with_status_filter():
    """Test GET /api/activity/logs?status=success."""
    response = client.get("/api/activity/logs?status=success")

    assert response.status_code == 200
    data = response.json()

    # Tous les logs devraient avoir status=success
    for log in data["logs"]:
        assert log["status"] == "success"

    print(f"✅ Filter status: {len(data['logs'])} logs success")


def test_get_logs_with_days_filter():
    """Test GET /api/activity/logs?days=30."""
    response = client.get("/api/activity/logs?days=30")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["logs"], list)

    print(f"✅ Filter days: {data['total']} logs dans les 30 derniers jours")


def test_get_logs_structure():
    """Test structure des logs."""
    response = client.get("/api/activity/logs?limit=1")

    assert response.status_code == 200
    data = response.json()

    if len(data["logs"]) > 0:
        log = data["logs"][0]

        # Vérifier structure
        expected_fields = [
            "id", "event_type", "event_sub", "message", "status",
            "prospect_id", "prospect_name", "metric_value",
            "ia_decision", "details", "created_at"
        ]

        for field in expected_fields:
            assert field in log, f"Champ {field} manquant"

        print("✅ Structure log complète")
    else:
        print("⚠️ Aucun log en base pour tester")


def test_get_summary():
    """Test GET /api/activity/summary."""
    response = client.get("/api/activity/summary")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Par défaut, retourne 7 jours
    assert len(data) <= 7

    print(f"✅ Activity summary: {len(data)} jours")


def test_get_summary_with_days():
    """Test GET /api/activity/summary?days=14."""
    response = client.get("/api/activity/summary?days=14")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 14

    print(f"✅ Summary 14 jours: {len(data)} jours")


def test_get_today_summary():
    """Test GET /api/activity/summary/today."""
    response = client.get("/api/activity/summary/today")

    assert response.status_code == 200
    data = response.json()

    # Structure du daily summary
    assert "date" in data
    assert isinstance(data, dict)

    # Peut contenir emails_envoyes, devis_envoyes, etc.
    print(f"✅ Today summary: date={data['date']}")


def test_get_system_health():
    """Test GET /api/activity/health."""
    response = client.get("/api/activity/health")

    assert response.status_code == 200
    data = response.json()

    # Vérifier que les jobs sont présents
    expected_jobs = [
        "scraping", "enrichment", "email_sent", "email_received",
        "qualification", "scheduler", "system"
    ]

    for job in expected_jobs:
        assert job in data, f"Job {job} manquant"
        assert "last_run" in data[job]
        assert "last_status" in data[job]
        assert "last_message" in data[job]

    # Vérifier erreurs 24h
    assert "errors_last_24h" in data
    assert isinstance(data["errors_last_24h"], int)

    print(f"✅ System health: {data['errors_last_24h']} erreurs 24h")


def test_get_stats():
    """Test GET /api/activity/stats."""
    response = client.get("/api/activity/stats")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "periode" in data
    assert "emails_envoyes" in data
    assert "emails_recus" in data
    assert "taux_reponse_pct" in data
    assert "devis_envoyes" in data
    assert "ca_pipeline" in data
    assert "nouveaux_prospects" in data
    assert "signatures" in data

    # Vérifier types
    assert isinstance(data["emails_envoyes"], int)
    assert isinstance(data["taux_reponse_pct"], (int, float))

    print(f"✅ Stats: {data['emails_envoyes']} emails, {data['taux_reponse_pct']}% réponse")


def test_get_claude_tools():
    """Test GET /api/activity/claude/tools."""
    response = client.get("/api/activity/claude/tools")

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "tools" in data
    assert isinstance(data["tools"], list)

    # Si des tools existent
    if len(data["tools"]) > 0:
        tool = data["tools"][0]
        assert "tool_name" in tool
        assert "message" in tool
        assert "status" in tool
        assert "created_at" in tool

    print(f"✅ Claude tools: {data['total']} tools exécutés")


def test_get_claude_tools_with_days():
    """Test GET /api/activity/claude/tools?days=30."""
    response = client.get("/api/activity/claude/tools?days=30")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["tools"], list)

    print(f"✅ Claude tools 30j: {data['total']} tools")


def test_get_claude_tools_with_limit():
    """Test GET /api/activity/claude/tools?limit=10."""
    response = client.get("/api/activity/claude/tools?limit=10")

    assert response.status_code == 200
    data = response.json()

    assert len(data["tools"]) <= 10

    print(f"✅ Claude tools limit: {len(data['tools'])} tools (max 10)")


def test_get_claude_decisions():
    """Test GET /api/activity/claude/decisions."""
    response = client.get("/api/activity/claude/decisions")

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "decisions" in data
    assert isinstance(data["decisions"], list)

    # Si des décisions existent
    if len(data["decisions"]) > 0:
        decision = data["decisions"][0]
        assert "decision_type" in decision
        assert "message" in decision
        assert "reasoning" in decision
        assert "created_at" in decision

    print(f"✅ Claude decisions: {data['total']} décisions")


def test_get_claude_decisions_with_days():
    """Test GET /api/activity/claude/decisions?days=14."""
    response = client.get("/api/activity/claude/decisions?days=14")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["decisions"], list)

    print(f"✅ Claude decisions 14j: {data['total']} décisions")


def test_get_claude_escalations():
    """Test GET /api/activity/claude/escalations."""
    response = client.get("/api/activity/claude/escalations")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "total" in data
    assert "urgent" in data
    assert "high" in data
    assert "medium" in data
    assert "low" in data
    assert "escalations" in data

    # Vérifier types
    assert isinstance(data["total"], int)
    assert isinstance(data["urgent"], int)
    assert isinstance(data["escalations"], list)

    print(f"✅ Claude escalations: {data['total']} total ({data['urgent']} urgent)")


def test_get_claude_escalations_with_days():
    """Test GET /api/activity/claude/escalations?days=30."""
    response = client.get("/api/activity/claude/escalations?days=30")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["escalations"], list)

    print(f"✅ Claude escalations 30j: {data['total']} escalations")


def test_get_claude_stats():
    """Test GET /api/activity/claude/stats."""
    response = client.get("/api/activity/claude/stats")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "period_days" in data
    assert "tools_executed" in data
    assert "autonomous_decisions" in data
    assert "escalations" in data
    assert "autonomy_rate_pct" in data
    assert "optimizations_applied" in data
    assert "conversations" in data
    assert "briefings_sent" in data

    # Vérifier types
    assert isinstance(data["tools_executed"], int)
    assert isinstance(data["autonomy_rate_pct"], float)

    print(f"✅ Claude stats: {data['tools_executed']} tools, {data['autonomy_rate_pct']}% autonomie")


def test_get_claude_stats_with_days():
    """Test GET /api/activity/claude/stats?days=30."""
    response = client.get("/api/activity/claude/stats?days=30")

    assert response.status_code == 200
    data = response.json()

    assert data["period_days"] == 30

    print(f"✅ Claude stats 30j: {data['autonomous_decisions']} décisions")


def test_get_logs_with_prospect_id_filter():
    """Test GET /api/activity/logs?prospect_id=X."""
    # Utiliser un prospect existant si disponible
    response = client.get("/api/activity/logs?prospect_id=1&limit=5")

    assert response.status_code == 200
    data = response.json()

    # Tous les logs devraient avoir prospect_id=1
    for log in data["logs"]:
        assert log["prospect_id"] == 1

    print(f"✅ Filter prospect_id: {len(data['logs'])} logs pour prospect 1")


def test_get_logs_ordered_by_created_at():
    """Test que les logs sont triés par created_at desc."""
    response = client.get("/api/activity/logs?limit=50")

    assert response.status_code == 200
    data = response.json()

    # Vérifier ordre décroissant
    if len(data["logs"]) >= 2:
        dates = [log["created_at"] for log in data["logs"]]
        for i in range(len(dates) - 1):
            assert dates[i] >= dates[i+1], "Logs devraient être triés par date décroissante"

    print("✅ Logs triés par date décroissante")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
