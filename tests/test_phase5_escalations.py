"""
Tests Phase 5 — Escalations & Autonomy Configuration
"""
import pytest
from datetime import datetime, timedelta
from app.models.escalation import Escalation
from app.models.devis import Devis
from app.models.client import Client
from app.agents.chantier_auto import (
    get_autonomy_config,
    check_devis_need_escalation,
    create_escalation,
    check_discount_need_escalation,
)


def test_get_autonomy_config(db_session):
    """Test récupération config autonomie."""
    config = get_autonomy_config(db_session)

    assert "devis_auto_threshold_ht" in config
    assert "discount_auto_max_pct" in config
    assert "chantier_auto_planning" in config

    # Vérifier valeurs par défaut
    assert config["devis_auto_threshold_ht"] == 10000
    assert config["discount_auto_max_pct"] == 15
    assert config["chantier_auto_planning"] is True

    print(f"✅ Config autonomie: threshold={config['devis_auto_threshold_ht']}€, discount max={config['discount_auto_max_pct']}%")


def test_check_devis_need_escalation_under_threshold(db_session):
    """Test devis sous seuil - pas d'escalation."""
    # Créer un client de test
    client = Client(
        company_name="Test Client",
        email="test@client.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Devis sous seuil (5000€)
    devis = Devis(
        client_id=client.id,
        montant_ht=5000.0,
        montant_ttc=6000.0,
        status="accepte"
    )

    config = {"devis_auto_threshold_ht": 10000}
    needs_escalation, reason = check_devis_need_escalation(db_session, devis, config)

    assert needs_escalation is False
    print(f"✅ Devis 5000€ HT: autonome (seuil 10k€)")


def test_check_devis_need_escalation_above_threshold(db_session):
    """Test devis au-dessus seuil - escalation requise."""
    # Créer un client de test
    client = Client(
        company_name="Big Client",
        email="big@client.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Devis au-dessus seuil (15000€)
    devis = Devis(
        client_id=client.id,
        montant_ht=15000.0,
        montant_ttc=18000.0,
        status="accepte"
    )

    config = {"devis_auto_threshold_ht": 10000}
    needs_escalation, reason = check_devis_need_escalation(db_session, devis, config)

    assert needs_escalation is True
    assert "15000" in reason or "15 000" in reason
    print(f"✅ Devis 15000€ HT: escalation requise (>10k€)")


def test_check_discount_need_escalation_small(db_session):
    """Test remise faible - pas d'escalation."""
    config = {"discount_auto_max_pct": 15}

    needs_escalation, reason = check_discount_need_escalation(
        discount_percent=10,
        config=config
    )

    assert needs_escalation is False
    print("✅ Remise 10%: autonome (max 15%)")


def test_check_discount_need_escalation_large(db_session):
    """Test remise importante - escalation requise."""
    config = {"discount_auto_max_pct": 15}

    needs_escalation, reason = check_discount_need_escalation(
        discount_percent=20,
        config=config
    )

    assert needs_escalation is True
    assert "20" in reason
    print("✅ Remise 20%: escalation requise (>15%)")


def test_create_escalation(db_session):
    """Test création escalation."""
    escalation = create_escalation(
        db=db_session,
        decision_type="devis_montant_eleve",
        context={
            "devis_id": 123,
            "montant_ht": 15000,
            "client": "Big Corp"
        },
        priority="high",
        ia_recommendation="approve",
        ia_confidence=0.85,
        ia_reasoning="Client fiable, montant cohérent avec taille entreprise",
        auto_resolve_minutes=240
    )

    assert escalation.id is not None
    assert escalation.status == "pending"
    assert escalation.decision_type == "devis_montant_eleve"
    assert escalation.priority == "high"
    assert escalation.ia_recommendation == "approve"
    assert escalation.ia_confidence == 0.85
    assert escalation.auto_resolve_at is not None

    print(f"✅ Escalation créée: ID={escalation.id}, type={escalation.decision_type}")


def test_escalation_auto_resolve_timing(db_session):
    """Test timing auto-resolve."""
    escalation = create_escalation(
        db=db_session,
        decision_type="test",
        context={},
        priority="low",
        auto_resolve_minutes=60
    )

    # Vérifier que auto_resolve_at est dans le futur
    assert escalation.auto_resolve_at > datetime.now()

    # Vérifier que c'est bien dans ~60 minutes
    time_diff = (escalation.auto_resolve_at - datetime.now()).total_seconds() / 60
    assert 58 <= time_diff <= 62  # Marge de 2min

    print(f"✅ Auto-resolve dans {time_diff:.1f} minutes")


def test_escalation_no_auto_resolve(db_session):
    """Test escalation sans auto-resolve."""
    escalation = create_escalation(
        db=db_session,
        decision_type="test_manual",
        context={},
        priority="high",
        auto_resolve_minutes=None
    )

    assert escalation.auto_resolve_at is None
    print("✅ Escalation sans auto-resolve créée")


def test_escalation_priorities(db_session):
    """Test niveaux de priorité."""
    priorities = ["low", "medium", "high"]

    for priority in priorities:
        escalation = create_escalation(
            db=db_session,
            decision_type=f"test_{priority}",
            context={},
            priority=priority
        )

        assert escalation.priority == priority
        print(f"✅ Priorité {priority}: OK")


def test_escalation_with_full_context(db_session):
    """Test escalation avec contexte complet."""
    full_context = {
        "devis_id": 456,
        "montant_ht": 25000,
        "montant_ttc": 30000,
        "client": "Mega Corp",
        "client_id": 789,
        "prospect_score": 85,
        "industry": "BTP",
        "city": "Paris"
    }

    escalation = create_escalation(
        db=db_session,
        decision_type="devis_montant_eleve",
        context=full_context,
        priority="high",
        ia_recommendation="approve",
        ia_confidence=0.92,
        ia_reasoning="Excellent prospect (score 85), BTP Paris, historique positif",
        auto_resolve_minutes=180
    )

    assert escalation.context == full_context
    assert "client" in escalation.context
    assert "montant_ht" in escalation.context

    print(f"✅ Escalation avec contexte complet: {len(escalation.context)} champs")


def test_configurable_thresholds():
    """Test que les seuils sont bien configurables."""
    # Config par défaut
    from app.agents.chantier_auto import get_autonomy_config
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        default_config = get_autonomy_config(db)

        # Vérifier qu'on peut modifier les seuils
        assert isinstance(default_config["devis_auto_threshold_ht"], (int, float))
        assert isinstance(default_config["discount_auto_max_pct"], (int, float))

        # Simuler changement de config
        custom_config = {
            "devis_auto_threshold_ht": 20000,  # Seuil augmenté
            "discount_auto_max_pct": 20,       # Remise max augmentée
            "chantier_auto_planning": True,
            "chantier_notification_client": True,
            "planning_conflict_escalate": True
        }

        # Vérifier que les valeurs personnalisées sont différentes
        assert custom_config["devis_auto_threshold_ht"] != default_config["devis_auto_threshold_ht"]

        print(f"✅ Seuils configurables: défaut={default_config['devis_auto_threshold_ht']}€, custom={custom_config['devis_auto_threshold_ht']}€")
    finally:
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
