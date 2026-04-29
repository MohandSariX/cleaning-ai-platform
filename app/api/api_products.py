"""
API Products — CRUD produits/services
Remplace devis_rules.json par table PostgreSQL
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import SessionLocal
from app.models.product import (
    Product,
    get_products_by_tenant,
    get_product_by_name,
    get_products_by_category,
    deactivate_product
)
from app.models.tenant import get_tenant_by_email
from sqlalchemy.orm import Session


router = APIRouter(prefix="/api/products", tags=["products"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  SCHEMAS
# ══════════════════════════════════════════════════════════════

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    category: str  # prestation, forfait, materiel
    unit: str  # m2, heure, forfait, mois, unite
    unit_price_ht: float
    tva_rate: float = 0.20
    minimum_ht: Optional[float] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    unit_price_ht: Optional[float] = None
    tva_rate: Optional[float] = None
    minimum_ht: Optional[float] = None
    active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: Optional[str]
    category: str
    unit: str
    unit_price_ht: float
    tva_rate: float
    minimum_ht: Optional[float]
    active: bool

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.get("/", response_model=List[ProductResponse])
def list_products(
    category: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Liste tous les produits du tenant owner.

    Params:
    - category: Filtrer par catégorie (prestation, forfait, materiel)
    - active_only: Afficher uniquement les produits actifs (défaut: True)
    """
    owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
    if not owner:
        raise HTTPException(status_code=404, detail="Tenant owner introuvable")

    if category:
        products = get_products_by_category(db, owner.id, category, active_only)
    else:
        products = get_products_by_tenant(db, owner.id, active_only)

    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Récupère un produit par ID."""
    owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
    if not owner:
        raise HTTPException(status_code=404, detail="Tenant owner introuvable")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == owner.id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    return product


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau produit.

    Body:
    {
      "name": "Nettoyage bureaux",
      "description": "Entretien hebdomadaire",
      "category": "prestation",
      "unit": "m2",
      "unit_price_ht": 4.5,
      "tva_rate": 0.20,
      "minimum_ht": 150
    }
    """
    owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
    if not owner:
        raise HTTPException(status_code=404, detail="Tenant owner introuvable")

    # Vérifier si le nom existe déjà
    existing = get_product_by_name(db, owner.id, data.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Produit '{data.name}' existe déjà")

    # Créer produit
    product = Product(
        tenant_id=owner.id,
        name=data.name,
        description=data.description,
        category=data.category,
        unit=data.unit,
        unit_price_ht=data.unit_price_ht,
        tva_rate=data.tva_rate,
        minimum_ht=data.minimum_ht,
        active=True
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Modifie un produit existant.

    Body (tous les champs sont optionnels):
    {
      "unit_price_ht": 5.0,
      "description": "Nouvelle description",
      "active": false
    }
    """
    owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
    if not owner:
        raise HTTPException(status_code=404, detail="Tenant owner introuvable")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == owner.id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    # Mettre à jour les champs fournis
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Désactive un produit (soft delete).
    Le produit reste en base mais active=False.
    """
    owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
    if not owner:
        raise HTTPException(status_code=404, detail="Tenant owner introuvable")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == owner.id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    success = deactivate_product(db, product_id)

    if not success:
        raise HTTPException(status_code=500, detail="Erreur lors de la désactivation")

    return None


@router.get("/name/{name}", response_model=ProductResponse)
def get_product_by_name_endpoint(name: str, db: Session = Depends(get_db)):
    """
    Récupère un produit par son nom exact.
    Utile pour devis_engine qui cherche par nom.
    """
    owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
    if not owner:
        raise HTTPException(status_code=404, detail="Tenant owner introuvable")

    product = get_product_by_name(db, owner.id, name)

    if not product:
        raise HTTPException(status_code=404, detail=f"Produit '{name}' introuvable")

    return product
