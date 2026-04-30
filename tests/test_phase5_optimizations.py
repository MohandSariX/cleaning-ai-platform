"""
Tests Phase 5 — AI Optimizations & Learning
"""
import pytest
from datetime import datetime, timedelta
from app.agents.claude_optimizer import (
    analyze_email_performance,
    analyze_lost_prospects,
    adjust_scoring_weights,
    track_ab_test_results,
    suggest_optimizations,
    run_optimization_cycle
)


def test_analyze_email_performance():
    """Test analyse performance emails."""
    result = analyze_email_performance()

    # Vérifier structure
    assert "total_sent" in result
    assert "replied" in result
    assert "reply_rate" in result
    assert "best_day" in result
    assert "recommendations" in result

    # Vérifier types
    assert isinstance(result["total_sent"], int)
    assert isinstance(result["replied"], int)
    assert isinstance(result["reply_rate"], float)
    assert isinstance(result["recommendations"], list)

    # Vérifier cohérence
    assert result["total_sent"] >= 0
    assert result["replied"] >= 0
    assert result["replied"] <= result["total_sent"]
    assert 0 <= result["reply_rate"] <= 100

    print(f"✅ Performance emails: {result['total_sent']} envoyés, {result['reply_rate']:.1f}% réponse")


def test_analyze_lost_prospects():
    """Test analyse prospects perdus."""
    result = analyze_lost_prospects()

    # Vérifier structure
    assert "total" in result
    assert "avg_score" in result
    assert "by_score_range" in result
    assert "top_lost_industries" in result
    assert "recommendations" in result

    # Vérifier types
    assert isinstance(result["total"], int)
    assert isinstance(result["avg_score"], float)
    assert isinstance(result["by_score_range"], dict)
    assert isinstance(result["top_lost_industries"], list)

    # Vérifier cohérence
    assert result["total"] >= 0
    assert 0 <= result["avg_score"] <= 100

    if result["total"] > 0:
        print(f"✅ Prospects perdus: {result['total']} total, score moyen {result['avg_score']:.1f}")
    else:
        print("✅ Aucun prospect perdu (excellent!)")


def test_analyze_lost_prospects_score_ranges():
    """Test répartition par score."""
    result = analyze_lost_prospects()

    if result["total"] > 0:
        ranges = result["by_score_range"]

        # Vérifier structure
        assert "high" in ranges or "medium" in ranges or "low" in ranges

        # Vérifier que les totaux sont cohérents
        total_ranges = ranges.get("high", 0) + ranges.get("medium", 0) + ranges.get("low", 0)
        assert total_ranges <= result["total"]

        print(f"✅ Répartition: high={ranges.get('high', 0)}, medium={ranges.get('medium', 0)}, low={ranges.get('low', 0)}")


def test_analyze_lost_prospects_industries():
    """Test identification industries problématiques."""
    result = analyze_lost_prospects()

    industries = result["top_lost_industries"]

    # Vérifier structure
    assert isinstance(industries, list)

    for item in industries[:3]:  # Top 3
        assert "industry" in item
        assert "count" in item
        assert isinstance(item["count"], int)
        assert item["count"] > 0

        print(f"✅ Industrie problématique: {item['industry']} ({item['count']} perdus)")


def test_adjust_scoring_weights():
    """Test suggestions ajustement poids scoring."""
    result = adjust_scoring_weights()

    # Vérifier structure
    assert "status" in result
    assert "adjustments" in result

    # Vérifier type
    assert isinstance(result["adjustments"], list)

    # Si des ajustements sont suggérés
    for adjustment in result["adjustments"]:
        assert "criteria" in adjustment
        assert "current_weight" in adjustment or "suggestion" in adjustment

    print(f"✅ Ajustements scoring: {len(result['adjustments'])} suggestions")


def test_track_ab_test_results():
    """Test suivi résultats A/B testing."""
    result = track_ab_test_results()

    # Vérifier structure
    assert "status" in result

    # Statut peut être "no_test", "running", ou "completed"
    assert result["status"] in ["no_test", "running", "completed"]

    if result["status"] == "running":
        assert "variants" in result
        assert "total_sent" in result
        print(f"✅ A/B test en cours: {result['total_sent']} envois")

    elif result["status"] == "completed":
        assert "winner" in result
        print(f"✅ A/B test terminé: gagnant = {result['winner']}")

    else:
        print("✅ Aucun A/B test actif")


def test_suggest_optimizations():
    """Test génération suggestions d'optimisation."""
    suggestions = suggest_optimizations()

    # Vérifier structure
    assert isinstance(suggestions, list)

    for suggestion in suggestions:
        assert "type" in suggestion
        assert "priority" in suggestion
        assert "message" in suggestion
        assert "action" in suggestion

        # Vérifier priorité valide
        assert suggestion["priority"] in ["low", "medium", "high"]

        print(f"✅ Suggestion [{suggestion['priority']}]: {suggestion['message'][:60]}...")


def test_suggest_optimizations_priority_levels():
    """Test niveaux de priorité des suggestions."""
    suggestions = suggest_optimizations()

    priorities = {"low": 0, "medium": 0, "high": 0}

    for suggestion in suggestions:
        priorities[suggestion["priority"]] += 1

    print(f"✅ Priorités: high={priorities['high']}, medium={priorities['medium']}, low={priorities['low']}")


def test_run_optimization_cycle():
    """Test cycle d'optimisation complet."""
    result = run_optimization_cycle()

    # Vérifier structure
    assert "status" in result
    assert "timestamp" in result
    assert "analyses" in result
    assert "actions_taken" in result

    # Vérifier analyses effectuées
    analyses = result["analyses"]
    assert "email_performance" in analyses
    assert "lost_prospects" in analyses
    assert "scoring_adjustments" in analyses
    assert "ab_test" in analyses

    # Vérifier actions
    assert isinstance(result["actions_taken"], list)

    print(f"✅ Cycle optimisation: {len(result['actions_taken'])} actions")


def test_optimization_cycle_actions():
    """Test que le cycle prend des actions appropriées."""
    result = run_optimization_cycle()

    actions = result["actions_taken"]

    # Chaque action doit avoir une structure cohérente
    for action in actions:
        assert "action" in action
        assert "priority" in action

    print(f"✅ Actions du cycle: {len(actions)} actions effectuées")


def test_email_performance_recommendations():
    """Test recommandations basées sur performance email."""
    result = analyze_email_performance()

    recommendations = result["recommendations"]

    # Vérifier que des recommandations sont faites
    assert isinstance(recommendations, list)

    # Si taux de réponse faible, devrait recommander des améliorations
    if result["reply_rate"] < 2.0:
        assert len(recommendations) > 0
        print(f"✅ {len(recommendations)} recommandations pour améliorer taux réponse")
    else:
        print(f"✅ Bon taux de réponse ({result['reply_rate']:.1f}%)")


def test_lost_prospects_recommendations():
    """Test recommandations basées sur prospects perdus."""
    result = analyze_lost_prospects()

    recommendations = result["recommendations"]

    # Vérifier structure
    assert isinstance(recommendations, list)

    # Si beaucoup de prospects perdus, devrait recommander des actions
    if result["total"] > 10:
        assert len(recommendations) > 0
        print(f"✅ {len(recommendations)} recommandations pour réduire pertes")
    else:
        print("✅ Peu de prospects perdus")


def test_optimization_types():
    """Test types d'optimisations générées."""
    suggestions = suggest_optimizations()

    types = set()
    for suggestion in suggestions:
        types.add(suggestion["type"])

    # Vérifier diversité des types
    print(f"✅ Types d'optimisation: {', '.join(types)}")


def test_optimization_cycle_timestamp():
    """Test que le cycle enregistre bien le timestamp."""
    result = run_optimization_cycle()

    timestamp = result["timestamp"]

    # Vérifier que c'est un timestamp récent
    cycle_time = datetime.fromisoformat(timestamp)
    now = datetime.now()

    time_diff = abs((now - cycle_time).total_seconds())
    assert time_diff < 10  # Moins de 10 secondes de différence

    print(f"✅ Cycle exécuté à {timestamp}")


def test_scoring_adjustments_with_data():
    """Test ajustements scoring avec données réelles."""
    result = adjust_scoring_weights()

    if result["status"] == "insufficient_data":
        print("✅ Pas assez de données pour ajustements (normal au début)")
    else:
        sample_size = result.get("sample_size", {})
        print(f"✅ Ajustements basés sur: won={sample_size.get('won', 0)}, lost={sample_size.get('lost', 0)}")


def test_ab_test_variants():
    """Test structure variants A/B test."""
    result = track_ab_test_results()

    if result["status"] == "running" and "variants" in result:
        variants = result["variants"]

        for variant in variants:
            assert "name" in variant
            assert "sent" in variant
            assert "replied" in variant

            print(f"✅ Variant {variant['name']}: {variant['sent']} envois, {variant.get('reply_rate', 0):.1f}% réponse")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
