"""
Tests API Products — CRUD endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.tenant import get_tenant_by_email


client = TestClient(app)


def test_list_products():
    """Test GET /api/products."""
    response = client.get("/api/products")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 10

    # Vérifier structure
    product = data[0]
    assert "id" in product
    assert "name" in product
    assert "unit_price_ht" in product
    assert "category" in product
    assert "active" in product

    print(f"✅ {len(data)} produits retournés")


def test_list_products_by_category():
    """Test GET /api/products?category=prestation."""
    response = client.get("/api/products?category=prestation")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10
    assert all(p["category"] == "prestation" for p in data)

    print(f"✅ {len(data)} produits catégorie 'prestation'")


def test_list_products_include_inactive():
    """Test GET /api/products?active_only=false."""
    response = client.get("/api/products?active_only=false")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10

    print(f"✅ {len(data)} produits (actifs + inactifs)")


def test_get_product_by_id():
    """Test GET /api/products/{id}."""
    # Récupérer premier produit
    list_response = client.get("/api/products")
    products = list_response.json()
    first_product = products[0]

    # Récupérer par ID
    response = client.get(f"/api/products/{first_product['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == first_product["id"]
    assert data["name"] == first_product["name"]

    print(f"✅ Produit récupéré: {data['name']}")


def test_get_product_by_id_not_found():
    """Test GET /api/products/{id} avec ID inexistant."""
    response = client.get("/api/products/999999")

    assert response.status_code == 404
    assert "introuvable" in response.json()["detail"]

    print("✅ 404 pour produit inexistant")


def test_get_product_by_name():
    """Test GET /api/products/name/{name}."""
    response = client.get("/api/products/name/Nettoyage fin de chantier")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Nettoyage fin de chantier"
    assert data["unit_price_ht"] == 8.0

    print(f"✅ Produit trouvé par nom: {data['name']}")


def test_get_product_by_name_not_found():
    """Test GET /api/products/name/{name} avec nom inexistant."""
    response = client.get("/api/products/name/Produit Inexistant XYZ")

    assert response.status_code == 404

    print("✅ 404 pour nom inexistant")


def test_create_product():
    """Test POST /api/products."""
    payload = {
        "name": "Test API Create",
        "description": "Produit de test API",
        "category": "materiel",
        "unit": "unite",
        "unit_price_ht": 99.99,
        "tva_rate": 0.20,
        "minimum_ht": 50.0
    }

    response = client.post("/api/products", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test API Create"
    assert data["unit_price_ht"] == 99.99
    assert data["active"] is True
    assert "id" in data

    product_id = data["id"]

    print(f"✅ Produit créé: {data['name']} (ID: {product_id})")

    # Cleanup
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
    finally:
        db.close()


def test_create_product_duplicate_name():
    """Test POST /api/products avec nom existant."""
    payload = {
        "name": "Nettoyage fin de chantier",  # Existe déjà
        "category": "prestation",
        "unit": "m2",
        "unit_price_ht": 10.0
    }

    response = client.post("/api/products", json=payload)

    assert response.status_code == 400
    assert "existe déjà" in response.json()["detail"]

    print("✅ 400 pour nom dupliqué")


def test_update_product():
    """Test PATCH /api/products/{id}."""
    # Créer produit test
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
        test_product = Product(
            tenant_id=owner.id,
            name="Test API Update",
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
    finally:
        db.close()

    # Modifier via API
    payload = {
        "unit_price_ht": 15.0,
        "description": "Prix mis à jour"
    }

    response = client.patch(f"/api/products/{product_id}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["unit_price_ht"] == 15.0
    assert data["description"] == "Prix mis à jour"

    print(f"✅ Produit modifié: {data['name']} - {data['unit_price_ht']}€")

    # Cleanup
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
    finally:
        db.close()


def test_delete_product():
    """Test DELETE /api/products/{id} (soft delete)."""
    # Créer produit test
    db = SessionLocal()
    try:
        owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
        test_product = Product(
            tenant_id=owner.id,
            name="Test API Delete",
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
    finally:
        db.close()

    # Supprimer via API
    response = client.delete(f"/api/products/{product_id}")

    assert response.status_code == 204

    # Vérifier que produit est désactivé, pas supprimé
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        assert product is not None
        assert product.active is False

        print(f"✅ Produit désactivé (soft delete)")

        # Cleanup final
        db.delete(product)
        db.commit()
    finally:
        db.close()


def test_delete_product_not_found():
    """Test DELETE /api/products/{id} avec ID inexistant."""
    response = client.delete("/api/products/999999")

    assert response.status_code == 404

    print("✅ 404 pour suppression produit inexistant")
