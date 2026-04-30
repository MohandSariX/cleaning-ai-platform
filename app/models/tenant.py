"""
Modèle Tenant — Multi-tenant support
Permet de supporter plusieurs utilisateurs/entreprises sur la même plateforme
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Tenant(Base):
    """
    Tenant — Entreprise/Utilisateur de la plateforme

    Plans disponibles :
    - owner : Propriétaire de la plateforme (Proprexis)
    - starter : Plan gratuit (limites strictes)
    - pro : Plan professionnel
    - enterprise : Plan entreprise (illimité)
    """
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    plan = Column(String, nullable=False, default="starter")  # owner, starter, pro, enterprise
    status = Column(String, nullable=False, default="active")  # active, suspended, blocked
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relations
    config = relationship("TenantConfig", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("TenantSubscription", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.name} ({self.plan})>"


class TenantConfig(Base):
    """
    Configuration spécifique par tenant
    Stocke credentials, zones de travail, quotas, etc.
    """
    __tablename__ = "tenant_config"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Gmail configuration
    gmail_email = Column(String)
    gmail_credentials_encrypted = Column(String)  # JSON credentials chiffrées

    # Telegram configuration
    telegram_bot_token = Column(String)
    telegram_chat_id = Column(String)

    # Zones géographiques de travail
    zones_json = Column(JSON, default=[])  # Liste des villes/départements ciblés

    # Quotas
    max_emails_per_day = Column(Integer, default=50)
    max_prospects = Column(Integer, default=10000)
    max_api_calls_per_day = Column(Integer, default=1000)

    # API keys
    pappers_api_key = Column(String)
    groq_api_key = Column(String)

    # Personnalisation devis (Phase 6.2)
    logo_url = Column(String, nullable=True)  # URL du logo uploadé
    cgv_text = Column(String, nullable=True)  # CGV personnalisées
    conditions_paiement = Column(String, default="Comptant")  # Comptant, 30j, 60j, 90j
    remise_max_pct = Column(Float, default=15.0)  # Remise max autorisée (%)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relations
    tenant = relationship("Tenant", back_populates="config")

    def __repr__(self):
        return f"<TenantConfig tenant_id={self.tenant_id}>"


class TenantSubscription(Base):
    """
    Abonnement et facturation par tenant
    Gère les plans, paiements, dates de renouvellement
    """
    __tablename__ = "tenant_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Plan & Tarification
    plan = Column(String, nullable=False, default="starter")
    price_monthly = Column(Float, default=0.0)  # Prix mensuel en €
    currency = Column(String, default="EUR")

    # Dates importantes
    started_at = Column(DateTime, default=datetime.now)
    next_billing_date = Column(DateTime)
    canceled_at = Column(DateTime, nullable=True)

    # Statut abonnement
    status = Column(String, nullable=False, default="active")  # active, canceled, past_due, suspended

    # Paiement
    payment_method = Column(String)  # card, sepa, invoice
    last_payment_date = Column(DateTime, nullable=True)
    last_payment_amount = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relations
    tenant = relationship("Tenant", back_populates="subscription")

    def __repr__(self):
        return f"<TenantSubscription tenant_id={self.tenant_id} plan={self.plan}>"


# ══════════════════════════════════════════════════════════════
#  FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════

def get_tenant_by_id(db, tenant_id: int) -> Tenant:
    """Récupère un tenant par son ID."""
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def get_tenant_by_email(db, email: str) -> Tenant:
    """Récupère un tenant par son email."""
    return db.query(Tenant).filter(Tenant.email == email).first()


def create_owner_tenant(db) -> Tenant:
    """
    Crée le tenant propriétaire "owner" par défaut.
    À exécuter une seule fois lors de l'initialisation.
    """
    existing = get_tenant_by_email(db, "contact.proprexis@gmail.com")
    if existing:
        print(f"✅ Tenant owner existe déjà: {existing.name}")
        return existing

    # Créer tenant owner
    owner = Tenant(
        name="Proprexis",
        email="contact.proprexis@gmail.com",
        plan="owner",
        status="active"
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    # Créer config par défaut
    config = TenantConfig(
        tenant_id=owner.id,
        max_emails_per_day=50,
        max_prospects=100000,  # Illimité pour owner
        max_api_calls_per_day=10000,
        zones_json=["94", "93", "92", "77", "75", "91"]
    )
    db.add(config)

    # Créer subscription owner (gratuit)
    subscription = TenantSubscription(
        tenant_id=owner.id,
        plan="owner",
        price_monthly=0.0,
        status="active"
    )
    db.add(subscription)

    db.commit()

    print(f"✅ Tenant owner créé: {owner.name} (ID: {owner.id})")
    return owner
