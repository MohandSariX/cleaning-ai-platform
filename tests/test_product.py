"""
Tests Phase 3.6 — Products (catalogue produits/services)
"""
import pytest
from app.core.database import SessionLocal
from app.models.product import (
    Product,
    get_products_by_tenant,
    get_product_by_name,
    get_products_by_category,
    deactivate_product,
    calculate_line_totals
)
from app.models.tenant import get_tenant_by_email


def test_products_exist():
    """Test que les produits ont été migrés."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
        products = get_products_by_tenant(db, owner.id)

        assert len(products) >= 10
        assert all(p.tenant_id == owner.id for p in products)
        assert all(p.active for p in products)

        print(f"✅ {len(products)} produits actifs trouvés")
    finally:
        db.close()


def test_product_structure():
    """Test structure d'un produit."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
        product = db.query(Product).filter(Product.tenant_id == owner.id).first()

        assert product.id is not None
        assert product.tenant_id == owner.id
        assert product.name is not None
        assert product.category in ["prestation", "forfait", "materiel"]
        assert product.unit in ["m2", "heure", "forfait", "mois", "unite", "m2_par_semaine", "m2_par_mois", "m2_par_trimestre", "m2_par_an"]
        assert product.unit_price_ht > 0
        assert product.tva_rate == 0.20
        assert product.active is True

        print(f"✅ Structure produit: {product.name} - {product.unit_price_ht}€/{product.unit}")
    finally:
        db.close()


def test_get_product_by_name():
    """Test récupération produit par nom."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
        product = get_product_by_name(db, owner.id, "Nettoyage fin de chantier")

        assert product is not None
        assert product.name == "Nettoyage fin de chantier"
        assert product.unit_price_ht == 8.0
        assert product.minimum_ht == 400

        print(f"✅ Produit trouvé: {product.name} - {product.unit_price_ht}€/{product.unit}")
    finally:
        db.close()


def test_get_products_by_category():
    """Test récupération produits par catégorie."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
        products = get_products_by_category(db, owner.id, "prestation")

        assert len(products) >= 10
        assert all(p.category == "prestation" for p in products)

        print(f"✅ {len(products)} produits catégorie 'prestation'")
    finally:
        db.close()


def test_create_product():
    """Test création d'un nouveau produit."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")

        # Créer produit test
        test_product = Product(
            tenant_id=owner.id,
            name="Test Produit",
            description="Produit de test",
            category="materiel",
            unit="unite",
            unit_price_ht=25.0,
            tva_rate=0.20,
            active=True
        )
        db.add(test_product)
        db.commit()
        db.refresh(test_product)

        assert test_product.id is not None
        assert test_product.name == "Test Produit"
        assert test_product.unit_price_ht == 25.0

        print(f"✅ Produit créé: {test_product.name} (ID: {test_product.id})")

        # Cleanup
        db.delete(test_product)
        db.commit()
    finally:
        db.close()


def test_update_product():
    """Test modification d'un produit."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")

        # Créer produit test
        test_product = Product(
            tenant_id=owner.id,
            name="Test Update",
            description="Avant update",
            category="prestation",
            unit="m2",
            unit_price_ht=10.0,
            tva_rate=0.20,
            active=True
        )
        db.add(test_product)
        db.commit()
        db.refresh(test_product)

        # Modifier
        test_product.unit_price_ht = 15.0
        test_product.description = "Après update"
        db.commit()

        # Vérifier
        updated = db.query(Product).filter(Product.id == test_product.id).first()
        assert updated.unit_price_ht == 15.0
        assert updated.description == "Après update"

        print(f"✅ Produit modifié: {updated.name} - {updated.unit_price_ht}€")

        # Cleanup
        db.delete(test_product)
        db.commit()
    finally:
        db.close()


def test_deactivate_product():
    """Test désactivation produit (soft delete)."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")

        # Créer produit test
        test_product = Product(
            tenant_id=owner.id,
            name="Test Deactivate",
            category="prestation",
            unit="m2",
            unit_price_ht=10.0,
            tva_rate=0.20,
            active=True
        )
        db.add(test_product)
        db.commit()
        db.refresh(test_product)

        product_id = test_product.id

        # Désactiver
        result = deactivate_product(db, product_id)
        assert result is True

        # Vérifier
        deactivated = db.query(Product).filter(Product.id == product_id).first()
        assert deactivated.active is False

        # Ne devrait plus apparaître dans active_only=True
        active_products = get_products_by_tenant(db, owner.id, active_only=True)
        assert product_id not in [p.id for p in active_products]

        print(f"✅ Produit désactivé (soft delete)")

        # Cleanup
        db.delete(test_product)
        db.commit()
    finally:
        db.close()


def test_calculate_line_totals():
    """Test calcul montants ligne."""
    # Cas 1: 100m2 à 4.5€/m2 avec TVA 20%
    result = calculate_line_totals(100, 4.5, 0.20)

    assert result["total_ht"] == 450.0
    assert result["total_tva"] == 90.0
    assert result["total_ttc"] == 540.0

    # Cas 2: 3h à 45€/h avec TVA 20%
    result = calculate_line_totals(3, 45.0, 0.20)

    assert result["total_ht"] == 135.0
    assert result["total_tva"] == 27.0
    assert result["total_ttc"] == 162.0

    print("✅ Calculs montants corrects")


def test_minimum_ht():
    """Test que les forfaits minimums sont importés."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")

        # Nettoyage fin de chantier doit avoir minimum_ht = 400
        product = get_product_by_name(db, owner.id, "Nettoyage fin de chantier")
        assert product.minimum_ht == 400

        # Nettoyage bureaux ponctuel doit avoir minimum_ht = 150
        product = get_product_by_name(db, owner.id, "Nettoyage bureaux ponctuel")
        assert product.minimum_ht == 150

        print("✅ Forfaits minimums corrects")
    finally:
        db.close()


def test_product_units():
    """Test que les unités sont correctes."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")

        # Produit au m2
        product = get_product_by_name(db, owner.id, "Nettoyage fin de chantier")
        assert product.unit == "m2"

        # Produit horaire
        product = get_product_by_name(db, owner.id, "Remise en état après sinistre/travaux")
        assert product.unit == "heure"
        assert product.unit_price_ht == 45.0

        print("✅ Unités correctes (m2, heure, etc.)")
    finally:
        db.close()


def test_products_isolated_by_tenant():
    """Test isolation multi-tenant."""
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")

        # Tous les produits doivent appartenir au tenant owner
        all_products = db.query(Product).all()
        assert all(p.tenant_id == owner.id for p in all_products)

        # get_products_by_tenant ne doit retourner que les produits du tenant
        owner_products = get_products_by_tenant(db, owner.id)
        fake_tenant_products = get_products_by_tenant(db, 99999)

        assert len(owner_products) >= 10
        assert len(fake_tenant_products) == 0

        print(f"✅ Isolation multi-tenant OK")
    finally:
        db.close()
