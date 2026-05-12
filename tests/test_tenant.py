"""
Tests Phase 3.5 — Multi-tenant
"""
import pytest
from app.core.database import SessionLocal
from app.models.tenant import (
    Tenant, TenantConfig, TenantSubscription,
    get_tenant_by_id, get_tenant_by_email
)


def test_owner_tenant_exists():
    """Test que le tenant owner existe."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")

        assert owner is not None
        assert owner.name == "Proprexis"
        assert owner.plan == "owner"
        assert owner.status == "active"

        print(f"✅ Tenant owner: {owner.name} (ID: {owner.id})")

    finally:
        db.close()


def test_owner_has_config():
    """Test que le tenant owner a une configuration."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
        assert owner.config is not None

        config = owner.config
        assert config.tenant_id == owner.id
        assert config.max_emails_per_day >= 50
        assert config.max_prospects >= 10000
        assert isinstance(config.zones_json, list)

        print(f"✅ Config owner: {config.max_emails_per_day} emails/j, {config.max_prospects} prospects max")

    finally:
        db.close()


def test_owner_has_subscription():
    """Test que le tenant owner a un abonnement."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
        assert owner.subscription is not None

        sub = owner.subscription
        assert sub.tenant_id == owner.id
        assert sub.plan == "owner"
        assert sub.price_monthly == 0.0
        assert sub.status == "active"

        print(f"✅ Subscription owner: {sub.plan} - {sub.price_monthly}€/mois")

    finally:
        db.close()


def test_create_new_tenant():
    """Test création d'un nouveau tenant."""
    db = SessionLocal()
    try:
        # Créer tenant test
        test_tenant = Tenant(
            name="Test Company",
            email=f"test_{str(hash(str(__name__)))}@example.com",
            plan="starter",
            status="active"
        )
        db.add(test_tenant)
        db.commit()
        db.refresh(test_tenant)

        # Vérifier
        assert test_tenant.id is not None
        assert test_tenant.name == "Test Company"
        assert test_tenant.plan == "starter"

        print(f"✅ Nouveau tenant créé: {test_tenant.name} (ID: {test_tenant.id})")

        # Cleanup
        db.delete(test_tenant)
        db.commit()

    finally:
        db.close()


def test_tenant_config_crud():
    """Test CRUD TenantConfig."""
    db = SessionLocal()
    try:
        # Créer tenant test
        test_tenant = Tenant(
            name="Config Test",
            email=f"config_test_{str(hash(str(__name__)))}@example.com",
            plan="pro",
            status="active"
        )
        db.add(test_tenant)
        db.commit()
        db.refresh(test_tenant)

        # Créer config
        config = TenantConfig(
            tenant_id=test_tenant.id,
            max_emails_per_day=100,
            max_prospects=50000,
            zones_json=["75", "92", "93"]
        )
        db.add(config)
        db.commit()

        # Vérifier
        assert config.id is not None
        assert config.tenant_id == test_tenant.id
        assert config.max_emails_per_day == 100
        assert len(config.zones_json) == 3

        print(f"✅ Config créée: {config.max_emails_per_day} emails/j")

        # Cleanup
        db.delete(test_tenant)  # Cascade delete config
        db.commit()

    finally:
        db.close()


def test_tenant_subscription_crud():
    """Test CRUD TenantSubscription."""
    db = SessionLocal()
    try:
        # Créer tenant test
        test_tenant = Tenant(
            name="Sub Test",
            email=f"sub_test_{str(hash(str(__name__)))}@example.com",
            plan="pro",
            status="active"
        )
        db.add(test_tenant)
        db.commit()
        db.refresh(test_tenant)

        # Créer subscription
        sub = TenantSubscription(
            tenant_id=test_tenant.id,
            plan="pro",
            price_monthly=49.99,
            status="active"
        )
        db.add(sub)
        db.commit()

        # Vérifier
        assert sub.id is not None
        assert sub.tenant_id == test_tenant.id
        assert sub.plan == "pro"
        assert sub.price_monthly == 49.99

        print(f"✅ Subscription créée: {sub.plan} - {sub.price_monthly}€/mois")

        # Cleanup
        db.delete(test_tenant)  # Cascade delete subscription
        db.commit()

    finally:
        db.close()


def test_get_tenant_by_id():
    """Test récupération tenant par ID."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
        owner_id = owner.id

        # Récupérer par ID
        tenant = get_tenant_by_id(db, owner_id)

        assert tenant is not None
        assert tenant.id == owner_id
        assert tenant.name == "Proprexis"

        print(f"✅ get_tenant_by_id({owner_id}): {tenant.name}")

    finally:
        db.close()


def test_get_tenant_by_email():
    """Test récupération tenant par email."""
    db = SessionLocal()
    try:
        tenant = get_tenant_by_email(db, "contact.proprexis@gmail.com")

        assert tenant is not None
        assert tenant.email == "contact.proprexis@gmail.com"
        assert tenant.name == "Proprexis"

        print(f"✅ get_tenant_by_email: {tenant.name}")

    finally:
        db.close()


def test_tenant_cascade_delete():
    """Test suppression cascade (tenant → config → subscription)."""
    db = SessionLocal()
    try:
        # Créer tenant avec config et subscription
        test_tenant = Tenant(
            name="Cascade Test",
            email=f"cascade_test_{str(hash(str(__name__)))}@example.com",
            plan="starter",
            status="active"
        )
        db.add(test_tenant)
        db.commit()
        db.refresh(test_tenant)

        config = TenantConfig(tenant_id=test_tenant.id, max_emails_per_day=50)
        sub = TenantSubscription(tenant_id=test_tenant.id, plan="starter", price_monthly=0)

        db.add(config)
        db.add(sub)
        db.commit()

        tenant_id = test_tenant.id

        # Supprimer tenant
        db.delete(test_tenant)
        db.commit()

        # Vérifier cascade delete
        assert db.query(Tenant).filter(Tenant.id == tenant_id).first() is None
        assert db.query(TenantConfig).filter(TenantConfig.tenant_id == tenant_id).first() is None
        assert db.query(TenantSubscription).filter(TenantSubscription.tenant_id == tenant_id).first() is None

        print("✅ Cascade delete fonctionne")

    finally:
        db.close()


def test_prospects_have_tenant_id():
    """Test que les prospects ont tenant_id."""
    db = SessionLocal()
    try:
        from app.models.prospect import Prospect

        # Vérifier que le modèle Prospect a le champ tenant_id
        prospects = db.query(Prospect).limit(10).all()

        if prospects:
            # Tous doivent avoir l'attribut tenant_id (même si None pour anciennes données)
            for p in prospects:
                assert hasattr(p, 'tenant_id'), "Prospect devrait avoir tenant_id"

            # Compter combien ont tenant_id défini
            with_tenant = sum(1 for p in prospects if p.tenant_id is not None)
            print(f"✅ {with_tenant}/{len(prospects)} prospects ont tenant_id défini")
        else:
            print("⚠️  Aucun prospect en base")

    finally:
        db.close()
