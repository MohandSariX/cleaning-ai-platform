"""
Tests pour activity_logger — 100% coverage
"""
import pytest
from datetime import date
from app.agents.activity_logger import (
    log,
    log_email_sent,
    log_email_received,
    log_qualification,
    log_devis,
    log_scraping,
    log_enrichment,
    log_system,
    log_error,
    log_scheduler_job,
    get_daily_summary,
    log_claude_tool_call,
    log_claude_decision,
    log_claude_briefing,
    log_claude_optimization,
    log_claude_escalation,
    log_claude_conversation,
    log_claude_learning,
)
from app.core.database import SessionLocal
from app.models.activity_log import ActivityLog


@pytest.fixture
def db_session():
    """Fixture pour session DB."""
    db = SessionLocal()
    yield db
    db.close()


def test_log_basic(db_session):
    """Test fonction log de base."""
    log(
        event_type="test",
        message="Test message",
        status="info",
    )

    # Vérifier qu'un log a été créé
    entry = db_session.query(ActivityLog).filter(
        ActivityLog.message == "Test message"
    ).first()
    assert entry is not None
    assert entry.event_type == "test"
    print("✅ log() basic")


def test_log_email_sent(db_session):
    """Test log_email_sent."""
    log_email_sent(
        prospect_id=None,
        prospect_name="Test Prospect",
        city="Paris",
        email_type="prospection",
        subject="Test email",
        score=75
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "email_sent"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert "Test Prospect" in entry.message
    print("✅ log_email_sent")


def test_log_email_received(db_session):
    """Test log_email_received."""
    log_email_received(
        prospect_id=None,
        prospect_name="Test Prospect",
        intention="interesse",
        message_preview="Bonjour, je suis intéressé",
        ia_reason="Positive sentiment detected"
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "email_received"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.event_sub == "interesse"
    print("✅ log_email_received")


def test_log_qualification(db_session):
    """Test log_qualification."""
    log_qualification(
        prospect_id=None,
        prospect_name="Test Prospect",
        action="devis_sent",
        infos={"superficie": 100},
        ia_decision="All info collected"
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "qualification"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.event_sub == "devis_sent"
    print("✅ log_qualification")


def test_log_devis(db_session):
    """Test log_devis."""
    log_devis(
        prospect_id=None,
        client_name="Test Client",
        numero="DEV-2025-001",
        montant_ttc=1200.0,
        type_prestation="bureaux"
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "devis_sent"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.metric_value == 1200.0
    print("✅ log_devis")


def test_log_scraping(db_session):
    """Test log_scraping."""
    log_scraping(
        dept="75",
        dept_name="Paris",
        nb_prospects=25,
        nb_queries=10,
        duration_min=5.5
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "scraping"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.metric_value == 25
    print("✅ log_scraping")


def test_log_enrichment(db_session):
    """Test log_enrichment."""
    log_enrichment(nb_enriched=15, nb_not_found=5)

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "enrichment"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.metric_value == 15
    print("✅ log_enrichment")


def test_log_system(db_session):
    """Test log_system."""
    log_system(
        message="System started",
        status="success",
        details={"version": "1.0"}
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "system"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert "started" in entry.message
    print("✅ log_system")


def test_log_error(db_session):
    """Test log_error."""
    log_error(
        source="test_module",
        error="Test error message",
        details={"code": 500}
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "error"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.status == "error"
    print("✅ log_error")


def test_log_scheduler_job(db_session):
    """Test log_scheduler_job."""
    log_scheduler_job(
        job_name="test_job",
        status="success",
        details={"duration": 2.5}
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "scheduler"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.event_sub == "test_job"
    print("✅ log_scheduler_job")


def test_get_daily_summary():
    """Test get_daily_summary."""
    summary = get_daily_summary()

    assert isinstance(summary, dict)
    assert "date" in summary
    assert "emails_envoyes" in summary
    assert "emails_recus" in summary
    assert "devis_envoyes" in summary
    assert "total_actions" in summary
    print("✅ get_daily_summary")


def test_get_daily_summary_with_date():
    """Test get_daily_summary avec date spécifique."""
    target = date(2025, 1, 1)
    summary = get_daily_summary(target_date=target)

    assert summary["date"] == "2025-01-01"
    print("✅ get_daily_summary with date")


def test_log_claude_tool_call(db_session):
    """Test log_claude_tool_call."""
    log_claude_tool_call(
        tool_name="get_prospects",
        arguments={"status": "new"},
        result={"count": 5},
        success=True,
        execution_time_ms=150.0
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "claude_tool"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.event_sub == "get_prospects"
    print("✅ log_claude_tool_call")


def test_log_claude_decision(db_session):
    """Test log_claude_decision."""
    log_claude_decision(
        decision_type="send_email",
        action_taken="Email sent to prospect",
        reasoning="High score prospect",
        autonomous=True,
        escalated=False
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "claude_decision"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.event_sub == "send_email"
    print("✅ log_claude_decision")


def test_log_claude_decision_escalated(db_session):
    """Test log_claude_decision avec escalation."""
    log_claude_decision(
        decision_type="large_discount",
        action_taken="Escalated to human",
        reasoning="Discount > 15%",
        autonomous=False,
        escalated=True
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "claude_decision",
        ActivityLog.status == "warning"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    print("✅ log_claude_decision escalated")


def test_log_claude_briefing(db_session):
    """Test log_claude_briefing."""
    log_claude_briefing(
        briefing_type="daily",
        recipient="Mohand",
        content_preview="Today's summary..."
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "claude_briefing"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.event_sub == "daily"
    print("✅ log_claude_briefing")


def test_log_claude_optimization(db_session):
    """Test log_claude_optimization."""
    log_claude_optimization(
        optimization_type="email_timing",
        action="Adjusted send time to 10am",
        metrics_before={"response_rate": 10},
        metrics_after={"response_rate": 15}
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "claude_optimization"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.event_sub == "email_timing"
    print("✅ log_claude_optimization")


def test_log_claude_escalation(db_session):
    """Test log_claude_escalation."""
    log_claude_escalation(
        reason="Large contract needs approval",
        context={"amount": 50000},
        priority="high",
        decision_id=1
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "claude_escalation"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.event_sub == "high"
    print("✅ log_claude_escalation")


def test_log_claude_conversation(db_session):
    """Test log_claude_conversation."""
    log_claude_conversation(
        message_from="Mohand",
        message_preview="What's the status?",
        response_preview="All systems operational"
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "claude_conversation"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.event_sub == "telegram"
    print("✅ log_claude_conversation")


def test_log_claude_learning(db_session):
    """Test log_claude_learning."""
    log_claude_learning(
        learning_type="email_response",
        pattern="Morning emails get better response",
        confidence=0.85,
        sample_size=100
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "claude_learning"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.metric_value == 0.85
    print("✅ log_claude_learning")


def test_log_with_all_params(db_session):
    """Test log avec tous les paramètres."""
    log(
        event_type="test_complete",
        message="Full test",
        event_sub="sub_test",
        status="success",
        prospect_id=None,
        client_id=None,
        details={"key": "value"},
        metric_value=99.9,
        ia_decision="AI decision text"
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.message == "Full test"
    ).first()
    assert entry is not None
    assert entry.metric_value == 99.9
    print("✅ log with all params")


def test_log_enrichment_zero_enriched(db_session):
    """Test log_enrichment avec 0 enrichis."""
    log_enrichment(nb_enriched=0, nb_not_found=10)

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "enrichment",
        ActivityLog.metric_value == 0
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.status == "info"  # Not "success" when 0 enriched
    print("✅ log_enrichment zero")


def test_log_scheduler_job_error(db_session):
    """Test log_scheduler_job avec status error."""
    log_scheduler_job(
        job_name="failing_job",
        status="error",
        details={"error": "Something went wrong"}
    )

    entry = db_session.query(ActivityLog).filter(
        ActivityLog.event_type == "scheduler",
        ActivityLog.event_sub == "failing_job"
    ).order_by(ActivityLog.created_at.desc()).first()
    assert entry is not None
    assert entry.status == "error"
    print("✅ log_scheduler_job error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
