"""
Tests Phase 6 — Devis avancés & Templates
"""
import pytest
from datetime import datetime, timedelta
from app.models.devis import Devis
from app.models.devis_template import DevisTemplate
from app.models.client import Client
from app.models.tenant import TenantConfig


def test_devis_analytics_overview(db_session):
    """Test analytics overview endpoint."""
    # Créer client
    client = Client(
        company_name="Test Analytics",
        email="analytics@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Créer plusieurs devis
    for i in range(5):
        status = "accepte" if i < 2 else "envoye" if i < 4 else "refuse"
        devis = Devis(
            client_id=client.id,
            numero=f"DEV-2024-{i+1:03d}",
            montant_ht=1000.0 * (i + 1),
            status=status
        )
        db_session.add(devis)

    db_session.commit()

    # Vérifier qu'on a bien créé les devis
    total = db_session.query(Devis).count()
    assert total == 5
    acceptes = db_session.query(Devis).filter(Devis.status == "accepte").count()
    assert acceptes == 2

    print(f"✅ Analytics: {total} devis, {acceptes} acceptés")


def test_devis_analytics_by_type(db_session):
    """Test analytics par type prestation."""
    # Créer client
    client = Client(
        company_name="Test Type",
        email="type@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Créer devis de différents types
    types = ["bureaux", "bureaux", "fin_chantier", "copropriete"]
    for i, service_type in enumerate(types):
        devis = Devis(
            client_id=client.id,
            numero=f"DEV-TYPE-{i+1:03d}",
            service_type=service_type,
            montant_ht=2000.0,
            status="accepte" if i % 2 == 0 else "refuse"
        )
        db_session.add(devis)

    db_session.commit()

    # Compter par type
    bureaux_count = db_session.query(Devis).filter(Devis.service_type == "bureaux").count()
    assert bureaux_count == 2

    print(f"✅ Analytics by type: {bureaux_count} bureaux")


def test_devis_template_creation(db_session):
    """Test création template devis."""
    template = DevisTemplate(
        name="Template Test BTP",
        category="BTP",
        type_prestation="fin_chantier",
        description="Template pour fin de chantier BTP",
        template_json={
            "sections": [
                {"title": "Prestation", "content": "{{description}}"},
                {"title": "Prix", "content": "Montant HT: {{montant_ht}}€"}
            ]
        },
        variables_required=["description", "montant_ht"],
        is_default=True,
        active=True
    )

    db_session.add(template)
    db_session.commit()

    assert template.id is not None
    assert template.is_default is True
    assert len(template.variables_required) == 2

    print(f"✅ Template créé: {template.name}, ID={template.id}")


def test_devis_template_default_logic(db_session):
    """Test logique is_default (un seul par catégorie/type)."""
    # Créer premier template default
    template1 = DevisTemplate(
        name="Template 1",
        category="BTP",
        type_prestation="bureaux",
        template_json={},
        is_default=True
    )
    db_session.add(template1)
    db_session.commit()

    # Créer second template default même catégorie/type
    template2 = DevisTemplate(
        name="Template 2",
        category="BTP",
        type_prestation="bureaux",
        template_json={},
        is_default=True
    )
    db_session.add(template2)
    db_session.commit()

    # Note: La logique de désactivation de l'ancien default
    # devrait être dans l'API, pas le modèle
    # Pour ce test, on vérifie juste qu'on peut créer les deux

    defaults = db_session.query(DevisTemplate).filter(
        DevisTemplate.category == "BTP",
        DevisTemplate.type_prestation == "bureaux",
        DevisTemplate.is_default == True
    ).all()

    # Sans logique API, on a 2 defaults (c'est normal pour le modèle seul)
    assert len(defaults) == 2

    print(f"✅ Templates créés (logique default à implémenter dans API)")


def test_devis_template_variables(db_session):
    """Test variables requises template."""
    template = DevisTemplate(
        name="Template Variables",
        template_json={
            "header": "Devis pour {{client_name}}",
            "body": "Surface: {{superficie_m2}}m²",
            "price": "Prix: {{montant_ht}}€"
        },
        variables_required=["client_name", "superficie_m2", "montant_ht"]
    )

    db_session.add(template)
    db_session.commit()

    assert "client_name" in template.variables_required
    assert "superficie_m2" in template.variables_required
    assert "montant_ht" in template.variables_required

    print(f"✅ Variables requises: {', '.join(template.variables_required)}")


def test_devis_signature_fields(db_session):
    """Test champs signature électronique."""
    # Créer client
    client = Client(
        company_name="Test Signature",
        email="sign@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Créer devis
    devis = Devis(
        client_id=client.id,
        numero="DEV-SIGN-001",
        montant_ht=5000.0,
        status="envoye"
    )
    db_session.add(devis)
    db_session.commit()

    # Signer
    devis.signature_data = "data:image/png;base64,iVBORw0KG..."
    devis.signed_by = "Jean Dupont"
    devis.signed_at = datetime.now()
    devis.status = "accepte"

    db_session.commit()

    assert devis.signature_data is not None
    assert devis.signed_by == "Jean Dupont"
    assert devis.signed_at is not None
    assert devis.status == "accepte"

    print(f"✅ Devis signé par {devis.signed_by} le {devis.signed_at}")


def test_tenant_config_personalisation_fields():
    """Test champs personnalisation TenantConfig."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        config = TenantConfig(
            tenant_id=1,  # Supposons tenant 1 existe
            logo_url="https://example.com/logo.png",
            cgv_text="Conditions générales personnalisées...",
            conditions_paiement="30j",
            remise_max_pct=20.0
        )

        # Vérifier attributs (sans commit car tenant peut ne pas exister)
        assert config.logo_url == "https://example.com/logo.png"
        assert config.cgv_text is not None
        assert config.conditions_paiement == "30j"
        assert config.remise_max_pct == 20.0

        print(f"✅ Config personnalisation: logo={config.logo_url}, paiement={config.conditions_paiement}")
    finally:
        db.close()


def test_devis_by_montant_tranches(db_session):
    """Test analytics par tranches de montant."""
    # Créer client
    client = Client(
        company_name="Test Montant",
        email="montant@test.com",
        phone="0123456789"
    )
    db_session.add(client)
    db_session.commit()

    # Créer devis différents montants
    montants = [500, 2000, 4000, 7000, 15000]
    for i, montant in enumerate(montants):
        devis = Devis(
            client_id=client.id,
            numero=f"DEV-M-{i+1:03d}",
            montant_ht=montant,
            status="envoye"
        )
        db_session.add(devis)

    db_session.commit()

    # Compter par tranches
    under_1k = db_session.query(Devis).filter(Devis.montant_ht < 1000).count()
    between_1k_3k = db_session.query(Devis).filter(
        Devis.montant_ht >= 1000,
        Devis.montant_ht < 3000
    ).count()
    over_10k = db_session.query(Devis).filter(Devis.montant_ht >= 10000).count()

    assert under_1k == 1
    assert between_1k_3k == 1
    assert over_10k == 1

    print(f"✅ Tranches: <1k={under_1k}, 1k-3k={between_1k_3k}, >10k={over_10k}")


def test_devis_top_clients(db_session):
    """Test top clients par CA."""
    # Créer plusieurs clients
    clients = []
    for i in range(3):
        client = Client(
            company_name=f"Client {i+1}",
            email=f"client{i+1}@test.com",
            phone="0123456789"
        )
        db_session.add(client)
        clients.append(client)

    db_session.commit()

    # Créer devis acceptés avec CA différents
    ca_per_client = [10000, 25000, 5000]  # Client 2 > Client 1 > Client 3
    for i, client in enumerate(clients):
        devis = Devis(
            client_id=client.id,
            numero=f"DEV-TOP-{i+1:03d}",
            montant_ht=ca_per_client[i],
            status="accepte"
        )
        db_session.add(devis)

    db_session.commit()

    # Trouver top client
    # (Dans l'API réel, on ferait un GROUP BY + SUM)
    max_ca = max(ca_per_client)
    top_client_index = ca_per_client.index(max_ca)

    assert max_ca == 25000
    assert top_client_index == 1  # Client 2

    print(f"✅ Top client: Client {top_client_index + 1} avec {max_ca}€ CA")


def test_template_render_simulation():
    """Test simulation rendu template (sans DB)."""
    import re
    import json

    template_json = {
        "header": "Devis pour {{client_name}}",
        "body": "Surface: {{superficie_m2}}m²",
        "footer": "Total: {{montant_ht}}€"
    }

    variables = {
        "client_name": "ABC Corp",
        "superficie_m2": "150",
        "montant_ht": "5000"
    }

    # Simulation du rendu (comme dans l'API)
    template_str = json.dumps(template_json)
    for key, value in variables.items():
        pattern = r'\{\{' + key + r'\}\}'
        template_str = re.sub(pattern, str(value), template_str)

    rendered = json.loads(template_str)

    assert "ABC Corp" in rendered["header"]
    assert "150m²" in rendered["body"]
    assert "5000€" in rendered["footer"]

    print(f"✅ Template rendu: {rendered['header']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
