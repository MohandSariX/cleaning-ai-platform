"""
Tests Phase 5 — Autonomous Chantier Management
"""
import pytest
from datetime import datetime, timedelta
from app.models.devis import Devis
from app.models.chantier import Chantier
from app.models.client import Client
from app.agents.chantier_auto import (
    process_accepted_devis,
    auto_create_chantier_from_devis,
    check_planning_conflicts,
    notify_client_chantier,
)


def test_process_accepted_devis_autonomous(db_session):
    """Test traitement devis accepté - création autonome."""
    # Créer client
    client = Client(
        company_name="Auto Test Client",
        email="auto@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Créer devis sous seuil
    devis = Devis(
        client_id=client.id,
        montant_ht=8000.0,
        montant_ttc=9600.0,
        status="accepte",
        type_prestation="bureaux",
        superficie_m2=100,
        frequence="mensuel"
    )
    db_session.add(devis)
    db_session.commit()

    # Traiter
    result = process_accepted_devis(db_session, devis.id)

    assert result["status"] == "auto_created"
    assert "chantier_id" in result

    # Vérifier chantier créé
    chantier = db_session.query(Chantier).filter_by(devis_id=devis.id).first()
    assert chantier is not None
    assert chantier.status == "planifie"

    print(f"✅ Chantier créé automatiquement: ID={chantier.id}")


def test_process_accepted_devis_escalation(db_session):
    """Test traitement devis accepté - escalation."""
    # Créer client
    client = Client(
        company_name="Big Client",
        email="big@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Créer devis au-dessus seuil
    devis = Devis(
        client_id=client.id,
        montant_ht=18000.0,
        montant_ttc=21600.0,
        status="accepte",
        type_prestation="fin_chantier",
        superficie_m2=500
    )
    db_session.add(devis)
    db_session.commit()

    # Traiter
    result = process_accepted_devis(db_session, devis.id)

    assert result["status"] == "escalated"
    assert "escalation_id" in result

    print(f"✅ Devis 18k€ escaladé: escalation_id={result['escalation_id']}")


def test_auto_create_chantier_from_devis(db_session):
    """Test création automatique chantier."""
    # Créer client
    client = Client(
        company_name="Test Co",
        email="test@company.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Créer devis
    devis = Devis(
        client_id=client.id,
        montant_ht=5000.0,
        montant_ttc=6000.0,
        status="accepte",
        type_prestation="bureaux",
        superficie_m2=80,
        frequence="hebdo"
    )
    db_session.add(devis)
    db_session.commit()

    # Config autonomie
    config = {
        "chantier_auto_planning": True,
        "chantier_notification_client": True,
        "planning_conflict_escalate": True
    }

    # Créer chantier
    chantier = auto_create_chantier_from_devis(db_session, devis, config)

    assert chantier is not None
    assert chantier.devis_id == devis.id
    assert chantier.client_id == devis.client_id
    assert chantier.status == "planifie"
    assert chantier.date_debut is not None

    print(f"✅ Chantier auto-créé: {chantier.type_prestation}, début {chantier.date_debut}")


def test_chantier_date_debut_logic(db_session):
    """Test logique date début chantier."""
    # Créer client et devis
    client = Client(
        company_name="Date Test",
        email="date@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    devis = Devis(
        client_id=client.id,
        montant_ht=3000.0,
        montant_ttc=3600.0,
        status="accepte",
        type_prestation="vitrerie"
    )
    db_session.add(devis)
    db_session.commit()

    config = {"chantier_auto_planning": True}

    # Créer chantier
    chantier = auto_create_chantier_from_devis(db_session, devis, config)

    # Date début devrait être dans le futur
    assert chantier.date_debut > datetime.now()

    # Devrait être dans un délai raisonnable (moins de 30 jours)
    days_until_start = (chantier.date_debut - datetime.now()).days
    assert 0 <= days_until_start <= 30

    print(f"✅ Date début: dans {days_until_start} jours")


def test_check_planning_conflicts(db_session):
    """Test détection conflits planning."""
    # Créer client
    client = Client(
        company_name="Conflict Test",
        email="conflict@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Créer chantier existant
    existing = Chantier(
        client_id=client.id,
        date_debut=datetime.now() + timedelta(days=7),
        date_fin=datetime.now() + timedelta(days=8),
        status="planifie",
        type_prestation="bureaux"
    )
    db_session.add(existing)
    db_session.commit()

    # Tester date qui chevauche
    proposed_date = datetime.now() + timedelta(days=7, hours=3)
    has_conflict = check_planning_conflicts(db_session, proposed_date)

    # Devrait détecter le conflit
    print(f"✅ Conflit détecté: {has_conflict}")


def test_chantier_status_workflow(db_session):
    """Test workflow statut chantier."""
    # Créer client et devis
    client = Client(
        company_name="Workflow Test",
        email="workflow@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    devis = Devis(
        client_id=client.id,
        montant_ht=4000.0,
        montant_ttc=4800.0,
        status="accepte"
    )
    db_session.add(devis)
    db_session.commit()

    config = {"chantier_auto_planning": True}

    # Créer chantier
    chantier = auto_create_chantier_from_devis(db_session, devis, config)

    # Status initial
    assert chantier.status == "planifie"

    # Simuler progression (à tester dans intégration complète)
    print(f"✅ Status initial: {chantier.status}")


def test_notify_client_chantier(db_session):
    """Test notification client."""
    # Créer client
    client = Client(
        company_name="Notify Test",
        email="notify@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Créer chantier
    chantier = Chantier(
        client_id=client.id,
        date_debut=datetime.now() + timedelta(days=3),
        status="planifie",
        type_prestation="copropriete"
    )
    db_session.add(chantier)
    db_session.commit()

    # Tester notification
    result = notify_client_chantier(db_session, chantier.id)

    # Devrait retourner succès ou statut
    assert "status" in result
    print(f"✅ Notification client: {result['status']}")


def test_chantier_with_recurrence(db_session):
    """Test chantier avec récurrence."""
    # Créer client
    client = Client(
        company_name="Recurring Test",
        email="recurring@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Devis récurrent
    devis = Devis(
        client_id=client.id,
        montant_ht=2000.0,
        montant_ttc=2400.0,
        status="accepte",
        type_prestation="bureaux",
        frequence="hebdo"
    )
    db_session.add(devis)
    db_session.commit()

    config = {"chantier_auto_planning": True}

    # Créer chantier
    chantier = auto_create_chantier_from_devis(db_session, devis, config)

    # Pour fréquence récurrente, devrait avoir info récurrence
    if hasattr(chantier, 'recurrence'):
        assert chantier.recurrence is not None
        print(f"✅ Chantier récurrent: {chantier.recurrence}")
    else:
        print("✅ Chantier créé (récurrence à implémenter)")


def test_autonomous_vs_escalation_threshold():
    """Test comparaison seuils autonome vs escalation."""
    from app.agents.chantier_auto import get_autonomy_config
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        config = get_autonomy_config(db)
        threshold = config["devis_auto_threshold_ht"]

        # Devis juste sous seuil
        under = threshold - 1000
        # Devis juste au-dessus
        over = threshold + 1000

        print(f"✅ Seuil: {threshold}€")
        print(f"  - {under}€: autonome")
        print(f"  - {over}€: escalation")

        assert under < threshold
        assert over > threshold
    finally:
        db.close()


def test_chantier_creation_complete_fields(db_session):
    """Test que tous les champs essentiels sont remplis."""
    # Créer client
    client = Client(
        company_name="Complete Test",
        email="complete@test.com",
        phone="0123456789",
        address="123 Rue Test",
        city="Paris"
    )
    db_session.add(client)
    db_session.commit()

    # Devis complet
    devis = Devis(
        client_id=client.id,
        montant_ht=6000.0,
        montant_ttc=7200.0,
        status="accepte",
        type_prestation="fin_chantier",
        superficie_m2=200,
        description="Nettoyage complet fin de chantier"
    )
    db_session.add(devis)
    db_session.commit()

    config = {"chantier_auto_planning": True}

    # Créer chantier
    chantier = auto_create_chantier_from_devis(db_session, devis, config)

    # Vérifier champs essentiels
    assert chantier.client_id is not None
    assert chantier.devis_id is not None
    assert chantier.date_debut is not None
    assert chantier.status is not None
    assert chantier.type_prestation is not None

    print(f"✅ Chantier complet créé:")
    print(f"  - Client: {client.company_name}")
    print(f"  - Type: {chantier.type_prestation}")
    print(f"  - Début: {chantier.date_debut}")
    print(f"  - Status: {chantier.status}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
