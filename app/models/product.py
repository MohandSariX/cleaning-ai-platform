"""
Modèle Product — Catalogue produits/services
Remplace devis_rules.json par une table PostgreSQL
"""
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Product(Base):
    """
    Produit/Service au catalogue

    Categories :
    - prestation : Service de nettoyage (bureaux, fin chantier, etc.)
    - forfait : Forfait mensuel/trimestriel
    - materiel : Produits/matériel facturables

    Units :
    - m2 : Prix au mètre carré
    - heure : Prix horaire
    - forfait : Prix fixe
    - mois : Abonnement mensuel
    - unite : À l'unité
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)

    # Infos produit
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    category = Column(String, nullable=False, index=True)  # prestation, forfait, materiel

    # Tarification
    unit = Column(String, nullable=False)  # m2, heure, forfait, mois, unite
    unit_price_ht = Column(Float, nullable=False)  # Prix HT par unité
    tva_rate = Column(Float, nullable=False, default=0.20)  # 20% par défaut
    minimum_ht = Column(Float, nullable=True)  # Prix minimum HT

    # Statut
    active = Column(Boolean, default=True, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relations
#    devis_lines = relationship("DevisLine", back_populates="product")
#    facture_lines = relationship("FactureLine", back_populates="product")

    def __repr__(self):
        return f"<Product {self.name} ({self.unit_price_ht}€/{self.unit})>"


class DevisLine(Base):
    """
    Ligne de devis détaillée
    Chaque devis peut avoir plusieurs lignes de produits/services
    """
    __tablename__ = "devis_lines"

    id = Column(Integer, primary_key=True, index=True)
    devis_id = Column(Integer, ForeignKey('devis.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True, index=True)  # Nullable si produit supprimé

    # Détails ligne
    description = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price_ht = Column(Float, nullable=False)
    tva_rate = Column(Float, nullable=False, default=0.20)

    # Montants calculés
    total_ht = Column(Float, nullable=False)
    total_tva = Column(Float, nullable=False)
    total_ttc = Column(Float, nullable=False)

    # Ordre d'affichage
    position = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now)

    # Relations
#    devis = relationship("Devis", back_populates="lines")
#    product = relationship("Product", back_populates="devis_lines")

    def __repr__(self):
        return f"<DevisLine {self.description} - {self.total_ttc}€ TTC>"


class FactureLine(Base):
    """
    Ligne de facture détaillée
    Structure identique à DevisLine
    """
    __tablename__ = "facture_lines"

    id = Column(Integer, primary_key=True, index=True)
    facture_id = Column(Integer, ForeignKey('factures.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True, index=True)

    # Détails ligne
    description = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price_ht = Column(Float, nullable=False)
    tva_rate = Column(Float, nullable=False, default=0.20)

    # Montants calculés
    total_ht = Column(Float, nullable=False)
    total_tva = Column(Float, nullable=False)
    total_ttc = Column(Float, nullable=False)

    # Ordre d'affichage
    position = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now)

    # Relations
#    facture = relationship("Facture", back_populates="lines")
#    product = relationship("Product", back_populates="facture_lines")

    def __repr__(self):
        return f"<FactureLine {self.description} - {self.total_ttc}€ TTC>"


# ══════════════════════════════════════════════════════════════
#  FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════

def get_products_by_tenant(db, tenant_id: int, active_only: bool = True):
    """Récupère tous les produits d'un tenant."""
    query = db.query(Product).filter(Product.tenant_id == tenant_id)
    if active_only:
        query = query.filter(Product.active == True)
    return query.order_by(Product.category, Product.name).all()


def get_product_by_name(db, tenant_id: int, name: str):
    """Récupère un produit par son nom."""
    return db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.name == name,
        Product.active == True
    ).first()


def get_products_by_category(db, tenant_id: int, category: str, active_only: bool = True):
    """Récupère produits par catégorie."""
    query = db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.category == category
    )
    if active_only:
        query = query.filter(Product.active == True)
    return query.order_by(Product.name).all()


def deactivate_product(db, product_id: int):
    """Désactive un produit (soft delete)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.active = False
        db.commit()
        return True
    return False


def calculate_line_totals(quantity: float, unit_price_ht: float, tva_rate: float) -> dict:
    """Calcule les montants d'une ligne (HT, TVA, TTC)."""
    total_ht = round(quantity * unit_price_ht, 2)
    total_tva = round(total_ht * tva_rate, 2)
    total_ttc = round(total_ht + total_tva, 2)

    return {
        "total_ht": total_ht,
        "total_tva": total_tva,
        "total_ttc": total_ttc
    }
