#!/usr/bin/env python3
"""
Migration : devis_rules.json → table products
Corrigé avec imports dans le bon ordre
"""
# IMPORTANT : Importer TOUS les modèles en premier pour résoudre les relationships
import app.models.prospect
import app.models.client
import app.models.devis
import app.models.chantier
import app.models.facture
import app.models.email_log
import app.models.conversation
import app.models.activity_log
import app.models.ai_memory
import app.models.tenant
import app.models.product

import json
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.tenant import Tenant


def migrate_products():
    """Migre les tarifs de devis_rules.json vers table products."""
    db = SessionLocal()
    try:
        # Récupérer tenant owner
        owner = db.query(Tenant).filter(Tenant.email == "contact.proprexis@gmail.com").first()
        if not owner:
            print("❌ Tenant owner introuvable")
            return 0

        print(f"✅ Tenant owner: {owner.name} (ID: {owner.id})")

        # Charger devis_rules.json
        with open('devis_rules.json', 'r', encoding='utf-8') as f:
            rules = json.load(f)

        tarifs = rules.get("tarifs", {})
        print(f"\n🔄 Migration de {len(tarifs)} prestations...")

        count = 0
        for type_prestation, config in tarifs.items():
            # Ignorer si config n'est pas un dict (cas des commentaires)
            if not isinstance(config, dict):
                continue

            # Récupérer tarif_m2 (ou tarif_horaire si pas de m2)
            tarif_m2 = config.get("tarif_m2")
            tarif_horaire = config.get("tarif_horaire")

            # Déterminer prix unitaire et unité
            if tarif_m2:
                unit_price = tarif_m2
                unit = config.get("unite", "m2")
            elif tarif_horaire:
                unit_price = tarif_horaire
                unit = "heure"
            else:
                print(f"  ⚠️  {type_prestation}: Pas de tarif trouvé")
                continue

            # Créer produit
            product = Product(
                tenant_id=owner.id,
                name=config.get("label", type_prestation.replace("_", " ").title()),
                description=config.get("description", ""),
                category="prestation",
                unit=unit,
                unit_price_ht=unit_price,
                tva_rate=0.20,
                minimum_ht=config.get("minimum_ht"),
                active=True
            )

            db.add(product)
            count += 1
            print(f"  + {product.name}: {product.unit_price_ht}€/{product.unit}")

        db.commit()

        # Afficher tous les produits créés
        all_products = db.query(Product).filter(Product.tenant_id == owner.id).all()
        print(f"\n✅ {len(all_products)} produits en base:")
        for p in all_products:
            print(f"  • {p.name}: {p.unit_price_ht}€/{p.unit}")

        return count

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Migration devis_rules.json → Products")
    print("=" * 60)

    count = migrate_products()

    print("\n" + "=" * 60)
    print(f"✅ Migration terminée ! {count} produits importés")
    print("=" * 60)
