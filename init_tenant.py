#!/usr/bin/env python3
"""
Script d'initialisation Multi-tenant
Crée les tables tenant et le tenant owner par défaut
"""
from app.core.database import SessionLocal, engine, Base
from app.models.tenant import Tenant, TenantConfig, TenantSubscription, create_owner_tenant

# Importer tous les modèles pour que Base.metadata les connaisse
from app.models import (
    prospect, client, devis, chantier, facture,
    email_log, conversation, activity_log, ai_memory, tenant
)


def init_tenant_tables():
    """Crée les tables tenant si elles n'existent pas."""
    print("🔧 Création des tables tenant...")

    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)

    print("✅ Tables créées")


def init_owner_tenant():
    """Crée le tenant owner par défaut."""
    print("\n🏢 Initialisation tenant owner...")

    db = SessionLocal()
    try:
        owner = create_owner_tenant(db)
        print(f"✅ Tenant owner prêt: {owner.name} (ID: {owner.id})")
        print(f"   Email: {owner.email}")
        print(f"   Plan: {owner.plan}")
        print(f"   Status: {owner.status}")

        return owner
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Initialisation Multi-tenant")
    print("=" * 60)

    # Étape 1 : Créer tables
    init_tenant_tables()

    # Étape 2 : Créer tenant owner
    owner = init_owner_tenant()

    print("\n" + "=" * 60)
    print("✅ Initialisation terminée !")
    print("=" * 60)
    print(f"\nTenant owner créé : {owner.name} (ID: {owner.id})")
    print("Prochaine étape : Ajouter tenant_id sur les autres tables")
