"""
Tests pour api_dashboard — API Dashboard monitoring
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_dashboard_stats():
    """Test GET /api/dashboard/stats."""
    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "today" in data
    assert "pipeline" in data
    assert "top_prospects" in data
    assert "recent_activities" in data

    # Vérifier today
    today = data["today"]
    assert "emails_sent" in today
    assert "devis_generated" in today
    assert "devis_total_ht" in today
    assert "devis_total_ttc" in today
    assert "replies_received" in today

    # Vérifier types
    assert isinstance(today["emails_sent"], int)
    assert isinstance(today["devis_generated"], int)
    assert isinstance(today["replies_received"], int)

    print(f"✅ Dashboard stats: {today['emails_sent']} emails, {today['devis_generated']} devis")


def test_get_dashboard_pipeline():
    """Test structure pipeline dans stats."""
    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    data = response.json()

    pipeline = data["pipeline"]

    # Vérifier tous les statuts
    expected_statuses = ["new", "scored", "contacted", "replied", "qualified", "quoted", "won", "lost"]
    for status in expected_statuses:
        assert status in pipeline, f"Status {status} devrait être dans le pipeline"
        assert isinstance(pipeline[status], int)

    print(f"✅ Pipeline: {pipeline}")


def test_get_dashboard_top_prospects():
    """Test top prospects dans stats."""
    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    data = response.json()

    top_prospects = data["top_prospects"]

    assert isinstance(top_prospects, list)

    # Si des prospects existent
    if len(top_prospects) > 0:
        prospect = top_prospects[0]
        assert "id" in prospect
        assert "company_name" in prospect
        assert "city" in prospect
        assert "lead_score" in prospect
        assert "score_label" in prospect
        assert "source" in prospect

        # Le score doit être >= 80 (filtre du endpoint)
        assert prospect["lead_score"] >= 80

        print(f"✅ Top prospect: {prospect['company_name']} - score {prospect['lead_score']}")
    else:
        print("✅ Aucun prospect top score (normal en test)")


def test_get_dashboard_recent_activities():
    """Test activités récentes dans stats."""
    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    data = response.json()

    activities = data["recent_activities"]

    assert isinstance(activities, list)
    assert len(activities) <= 20, "Devrait limiter à 20 activités"

    # Si des activités existent
    if len(activities) > 0:
        activity = activities[0]
        assert "id" in activity
        assert "timestamp" in activity
        assert "event_type" in activity
        assert "message" in activity
        assert "status" in activity

        print(f"✅ Dernière activité: {activity['event_type']} - {activity['message'][:50]}")
    else:
        print("✅ Aucune activité récente (normal en test)")


def test_get_claude_summary():
    """Test GET /api/dashboard/claude-summary."""
    response = client.get("/api/dashboard/claude-summary")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "yesterday" in data
    assert "today" in data
    assert "alerts" in data

    # Vérifier structure yesterday
    yesterday = data["yesterday"]
    assert "emails_sent" in yesterday
    assert "prospects_enriched" in yesterday
    assert "devis_generated" in yesterday
    assert "replies_received" in yesterday

    # Vérifier structure today
    today = data["today"]
    assert "emails_sent" in today
    assert "prospects_enriched" in today
    assert "devis_generated" in today
    assert "replies_received" in today

    # Vérifier types
    assert isinstance(yesterday["emails_sent"], int)
    assert isinstance(today["emails_sent"], int)

    print(f"✅ Claude summary - Hier: {yesterday['emails_sent']} emails, Aujourd'hui: {today['emails_sent']} emails")


def test_get_claude_summary_alerts():
    """Test alertes dans claude summary."""
    response = client.get("/api/dashboard/claude-summary")

    assert response.status_code == 200
    data = response.json()

    alerts = data["alerts"]
    assert isinstance(alerts, list)

    print("✅ Alertes Claude présentes")


def test_get_pipeline_chart():
    """Test GET /api/dashboard/pipeline-chart."""
    response = client.get("/api/dashboard/pipeline-chart")

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure
    assert "days" in data
    days = data["days"]

    assert isinstance(days, list)
    assert len(days) == 7, "Devrait retourner 7 jours"

    # Vérifier structure d'un jour
    if len(days) > 0:
        day = days[0]
        assert "date" in day
        assert "new" in day
        assert "contacted" in day
        assert "replied" in day

        # Vérifier types
        assert isinstance(day["new"], int)
        assert isinstance(day["contacted"], int)
        assert isinstance(day["replied"], int)

        print(f"✅ Pipeline chart: {len(days)} jours, premier jour: {day['date']}")


def test_pipeline_chart_dates_order():
    """Test ordre des dates dans pipeline chart."""
    response = client.get("/api/dashboard/pipeline-chart")

    assert response.status_code == 200
    data = response.json()

    days = data["days"]
    assert len(days) == 7

    # Les dates doivent être en ordre chronologique
    dates = [day["date"] for day in days]
    assert dates == sorted(dates), "Dates devraient être en ordre chronologique"

    print(f"✅ Dates en ordre: {dates[0]} à {dates[-1]}")


def test_dashboard_stats_devis_calculation():
    """Test calcul montants devis."""
    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    data = response.json()

    today = data["today"]
    ht = today["devis_total_ht"]
    ttc = today["devis_total_ttc"]

    # Si des devis existent
    if ttc > 0:
        # HT devrait être environ 83% de TTC (TVA 20%)
        ratio = ht / ttc if ttc > 0 else 0
        assert 0.8 <= ratio <= 0.85, f"Ratio HT/TTC anormal: {ratio}"

        print(f"✅ Montants devis cohérents: {ht}€ HT, {ttc}€ TTC")
    else:
        # Pas de devis aujourd'hui
        assert ht == 0
        print("✅ Aucun devis aujourd'hui (montants à 0)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
