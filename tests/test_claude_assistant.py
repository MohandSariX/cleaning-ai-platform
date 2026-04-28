"""
Tests pour Claude Assistant — Briefings et rapports
"""
import pytest
from app.agents.claude_assistant import (
    generate_daily_briefing, generate_weekly_report, get_crm_stats
)
from app.agents.claude_optimizer import (
    analyze_email_performance, suggest_optimizations, run_optimization_cycle
)


def test_generate_daily_briefing():
    """Test génération briefing quotidien."""
    briefing = generate_daily_briefing()

    assert isinstance(briefing, str), "Should return string"
    assert len(briefing) > 100, "Briefing should have content"
    assert "BRIEFING" in briefing, "Should have title"
    assert "CRM" in briefing, "Should mention CRM"
    assert "prospects" in briefing.lower(), "Should mention prospects"


def test_generate_weekly_report():
    """Test génération rapport hebdomadaire."""
    report = generate_weekly_report()

    assert isinstance(report, str), "Should return string"
    assert len(report) > 100, "Report should have content"
    assert "RAPPORT" in report, "Should have title"
    assert "HEBDO" in report or "SEMAINE" in report, "Should mention week"


def test_get_crm_stats():
    """Test récupération stats CRM."""
    stats = get_crm_stats()

    assert isinstance(stats, dict), "Should return dict"
    assert "total_prospects" in stats, "Should have total"
    assert "with_email" in stats, "Should have email count"
    assert "avg_score" in stats, "Should have avg score"
    assert stats["total_prospects"] >= 0, "Total should be non-negative"


def test_analyze_email_performance():
    """Test analyse performance emails."""
    analysis = analyze_email_performance()

    assert isinstance(analysis, dict), "Should return dict"
    assert "total_sent" in analysis, "Should have total sent"
    assert "replied" in analysis, "Should have replied count"
    assert "reply_rate" in analysis, "Should have reply rate"
    assert "recommendations" in analysis, "Should have recommendations"


def test_suggest_optimizations():
    """Test suggestions optimisations."""
    suggestions = suggest_optimizations()

    assert isinstance(suggestions, list), "Should return list"
    for suggestion in suggestions:
        assert "type" in suggestion, "Suggestion should have type"
        assert "message" in suggestion, "Suggestion should have message"
        assert "action" in suggestion, "Suggestion should have action"
        assert "priority" in suggestion, "Suggestion should have priority"


def test_run_optimization_cycle():
    """Test cycle complet optimisation."""
    result = run_optimization_cycle()

    assert isinstance(result, dict), "Should return dict"
    assert "suggestions_generated" in result, "Should have suggestions count"
    assert "optimizations_applied" in result, "Should have applied count"
    assert result["suggestions_generated"] >= 0, "Count should be non-negative"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
